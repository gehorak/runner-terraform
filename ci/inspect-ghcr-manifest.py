#!/usr/bin/env python3
"""Inspect a public GHCR image tag and distinguish absence from registry errors."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REFERENCE_PATTERN = re.compile(r"^ghcr\.io/gehorak/runner-terraform:([0-9]+\.[0-9]+\.[0-9]+)$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
TOKEN_URL = "https://ghcr.io/token?service=ghcr.io&scope=repository:gehorak/runner-terraform:pull"
MANIFEST_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


class RegistryError(ValueError):
    """The registry response could not safely establish release state."""


def classify_response(status: int, body: bytes) -> dict[str, str]:
    """Return absent or a validated config digest; reject all ambiguous responses."""
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RegistryError("registry returned invalid JSON") from error

    if status == 404:
        errors = payload.get("errors", []) if isinstance(payload, dict) else []
        if (
            isinstance(payload, dict)
            and set(payload) == {"errors"}
            and isinstance(errors, list)
            and len(errors) == 1
            and isinstance(errors[0], dict)
            and errors[0].get("code") == "MANIFEST_UNKNOWN"
            and set(errors[0]).issubset({"code", "message", "detail"})
        ):
            return {"state": "absent"}
        raise RegistryError("registry returned an unclassified 404")
    if status != 200:
        raise RegistryError(f"registry returned HTTP {status}")
    if not isinstance(payload, dict):
        raise RegistryError("manifest payload must be an object")

    config = payload.get("config")
    digest = config.get("digest") if isinstance(config, dict) else None
    if not isinstance(digest, str) or DIGEST_PATTERN.fullmatch(digest) is None:
        raise RegistryError("manifest has no valid config digest")
    return {"state": "present", "config_digest": digest}


def build_token_request(username: str, password: str) -> Request:
    if not username or not password:
        raise RegistryError("GHCR username and workflow token are required")
    credentials = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return Request(TOKEN_URL, headers={"Authorization": f"Basic {credentials}"})


def inspect_reference(reference: str) -> dict[str, str]:
    match = REFERENCE_PATTERN.fullmatch(reference)
    if match is None:
        raise RegistryError("reference must be an immutable numeric runner-terraform version tag")
    version = quote(match.group(1), safe=".")

    try:
        token_request = build_token_request(
            os.environ.get("GHCR_USERNAME", ""), os.environ.get("GHCR_TOKEN", "")
        )
        with urlopen(token_request, timeout=20) as response:
            token_payload = json.load(response)
        if not isinstance(token_payload, dict):
            raise RegistryError("GHCR token response must be an object")
        token = token_payload.get("token") or token_payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise RegistryError("GHCR token response did not contain a token")

        request = Request(
            f"https://ghcr.io/v2/gehorak/runner-terraform/manifests/{version}",
            headers={"Authorization": f"Bearer {token}", "Accept": MANIFEST_ACCEPT},
        )
        try:
            with urlopen(request, timeout=20) as response:
                return classify_response(response.status, response.read())
        except HTTPError as error:
            return classify_response(error.code, error.read())
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RegistryError(f"GHCR inspection failed: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    arguments = parser.parse_args()
    try:
        result = inspect_reference(arguments.reference)
    except RegistryError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
