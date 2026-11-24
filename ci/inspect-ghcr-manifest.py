#!/usr/bin/env python3
"""Inspect a public GHCR image tag and distinguish absence from registry errors."""

from __future__ import annotations

import argparse
import base64
import hashlib
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
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)
IMAGE_MANIFEST_TYPES = {
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}
IMAGE_INDEX_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}


class RegistryError(ValueError):
    """The registry response could not safely establish release state."""


def classify_response(
    status: int, body: bytes, headers: object | None = None
) -> dict[str, str]:
    """Return absence or validated manifest digests; reject ambiguous responses."""
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

    manifest_digest = f"sha256:{hashlib.sha256(body).hexdigest()}"
    docker_digest = _header_value(headers, "docker-content-digest")
    if docker_digest is not None:
        if DIGEST_PATTERN.fullmatch(docker_digest) is None or docker_digest != manifest_digest:
            raise RegistryError("registry manifest digest header does not match its body")

    media_type = payload.get("mediaType")
    if media_type in IMAGE_MANIFEST_TYPES:
        config = payload.get("config")
        config_digest = config.get("digest") if isinstance(config, dict) else None
        if not isinstance(config_digest, str) or DIGEST_PATTERN.fullmatch(config_digest) is None:
            raise RegistryError("manifest has no valid config digest")
        return {
            "state": "present",
            "manifest_digest": manifest_digest,
            "config_digest": config_digest,
        }

    if media_type in IMAGE_INDEX_TYPES:
        descriptors = payload.get("manifests")
        if not isinstance(descriptors, list):
            raise RegistryError("image index has no manifest descriptor list")
        platform_manifests = [
            descriptor
            for descriptor in descriptors
            if isinstance(descriptor, dict)
            and isinstance(descriptor.get("platform"), dict)
            and descriptor["platform"].get("os") == "linux"
            and descriptor["platform"].get("architecture") == "amd64"
        ]
        if len(platform_manifests) != 1:
            raise RegistryError("image index must contain exactly one linux/amd64 manifest")
        platform_digest = platform_manifests[0].get("digest")
        if not isinstance(platform_digest, str) or DIGEST_PATTERN.fullmatch(platform_digest) is None:
            raise RegistryError("image index has no valid linux/amd64 manifest digest")
        return {
            "state": "present",
            "manifest_digest": manifest_digest,
            "platform_manifest_digest": platform_digest,
        }

    raise RegistryError("registry returned an unsupported manifest media type")


def _header_value(headers: object | None, name: str) -> str | None:
    if headers is None:
        return None
    items = getattr(headers, "items", None)
    if items is None:
        raise RegistryError("registry response headers are invalid")
    for key, value in items():
        if isinstance(key, str) and key.lower() == name.lower():
            return value.strip() if isinstance(value, str) else None
    return None


def build_token_request(username: str, password: str) -> Request:
    if not username or not password:
        raise RegistryError("GHCR username and workflow token are required")
    credentials = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return Request(TOKEN_URL, headers={"Authorization": f"Basic {credentials}"})


def _fetch_manifest(token: str, reference: str) -> dict[str, str]:
    request = Request(
        f"https://ghcr.io/v2/gehorak/runner-terraform/manifests/{quote(reference, safe=":")}",
        headers={"Authorization": f"Bearer {token}", "Accept": MANIFEST_ACCEPT},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return classify_response(response.status, response.read(), response.headers)
    except HTTPError as error:
        return classify_response(error.code, error.read(), error.headers)


def inspect_reference(reference: str) -> dict[str, str]:
    match = REFERENCE_PATTERN.fullmatch(reference)
    if match is None:
        raise RegistryError("reference must be an immutable numeric runner-terraform version tag")

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

        result = _fetch_manifest(token, quote(match.group(1), safe="."))
        platform_digest = result.get("platform_manifest_digest")
        if platform_digest is not None:
            platform_manifest = _fetch_manifest(token, platform_digest)
            if platform_manifest.get("manifest_digest") != platform_digest:
                raise RegistryError("linux/amd64 manifest digest does not match its index descriptor")
            config_digest = platform_manifest.get("config_digest")
            if config_digest is None:
                raise RegistryError("linux/amd64 descriptor does not reference an image manifest")
            result["config_digest"] = config_digest
        return result
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
