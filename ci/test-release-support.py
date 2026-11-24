#!/usr/bin/env python3
"""Exercise release-only helpers without building or publishing an image."""

from __future__ import annotations

import json
import importlib.util
import base64
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INSPECT_MODULE = ROOT / "ci/inspect-ghcr-manifest.py"
spec = importlib.util.spec_from_file_location("inspect_ghcr_manifest", INSPECT_MODULE)
assert spec is not None and spec.loader is not None
inspect_ghcr_manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspect_ghcr_manifest)
SHA = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "a" * 64
PARENT = "ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2"


def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *arguments], text=True, capture_output=True, check=False
    )


with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    manifest = temporary / "image.manifest"
    manifest.write_text(
        "RUNNER_IMAGE_VERSION=0.1.0\nRUNNER_IMAGE_REVISION=local\n", encoding="utf-8"
    )
    prepared = temporary / "prepared.manifest"
    result = invoke(
        str(ROOT / "ci/prepare-release-manifest.py"),
        "--input",
        str(manifest),
        "--output",
        str(prepared),
        "--tag",
        "v0.4.0",
        "--revision",
        SHA,
    )
    assert result.returncode == 0, result.stderr
    assert prepared.read_text(encoding="utf-8") == (
        "RUNNER_IMAGE_VERSION=0.4.0\nRUNNER_IMAGE_REVISION=" + SHA + "\n"
    )
    invalid_tag = invoke(
        str(ROOT / "ci/prepare-release-manifest.py"),
        "--input",
        str(manifest),
        "--output",
        str(prepared),
        "--tag",
        "0.4.0",
        "--revision",
        SHA,
    )
    assert invalid_tag.returncode == 1

    assert invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-image-digest",
        "absent",
        "--candidate-image-digest",
        DIGEST,
    ).stdout.strip() == "publish"
    assert invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-image-digest",
        DIGEST,
        "--candidate-image-digest",
        DIGEST,
    ).stdout.strip() == "resume"
    conflict = invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-image-digest",
        "sha256:" + "b" * 64,
        "--candidate-image-digest",
        DIGEST,
    )
    assert conflict.returncode == 1

    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"digest": DIGEST},
    }
    manifest_body = json.dumps(manifest).encode("utf-8")
    manifest_digest = "sha256:" + hashlib.sha256(manifest_body).hexdigest()
    assert inspect_ghcr_manifest.classify_response(200, manifest_body) == {
        "state": "present",
        "manifest_digest": manifest_digest,
        "config_digest": DIGEST,
    }

    image_index = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": "sha256:" + "c" * 64,
                "platform": {"os": "linux", "architecture": "amd64"},
            },
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": "sha256:" + "d" * 64,
                "platform": {"os": "unknown", "architecture": "unknown"},
            },
        ],
    }
    index_body = json.dumps(image_index).encode("utf-8")
    index_digest = "sha256:" + hashlib.sha256(index_body).hexdigest()
    assert inspect_ghcr_manifest.classify_response(200, index_body) == {
        "state": "present",
        "manifest_digest": index_digest,
        "platform_manifest_digest": "sha256:" + "c" * 64,
    }
    assert "application/vnd.oci.image.index.v1+json" in inspect_ghcr_manifest.MANIFEST_ACCEPT
    assert "application/vnd.docker.distribution.manifest.list.v2+json" in inspect_ghcr_manifest.MANIFEST_ACCEPT

    docker_manifest_list = {
        **image_index,
        "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    }
    docker_list_body = json.dumps(docker_manifest_list).encode("utf-8")
    assert inspect_ghcr_manifest.classify_response(200, docker_list_body)[
        "platform_manifest_digest"
    ] == "sha256:" + "c" * 64

    platform_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"digest": DIGEST},
    }
    platform_body = json.dumps(platform_manifest).encode("utf-8")
    platform_manifest_digest = "sha256:" + hashlib.sha256(platform_body).hexdigest()
    published_index = {
        **image_index,
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": platform_manifest_digest,
                "platform": {"os": "linux", "architecture": "amd64"},
            }
        ],
    }
    published_index_body = json.dumps(published_index).encode("utf-8")
    registry_responses = [
        (200, b'{"token":"test-token"}', {}),
        (200, published_index_body, {}),
        (200, platform_body, {"Docker-Content-Digest": platform_manifest_digest}),
    ]
    requested_urls: list[str] = []

    class FakeResponse:
        def __init__(self, status: int, body: bytes, headers: dict[str, str]) -> None:
            self.status = status
            self._body = body
            self.headers = headers

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self._body

    original_urlopen = inspect_ghcr_manifest.urlopen

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        requested_urls.append(request.full_url)
        status, body, headers = registry_responses.pop(0)
        return FakeResponse(status, body, headers)

    inspect_ghcr_manifest.urlopen = fake_urlopen
    previous_username = os.environ.get("GHCR_USERNAME")
    previous_token = os.environ.get("GHCR_TOKEN")
    os.environ["GHCR_USERNAME"] = "runner"
    os.environ["GHCR_TOKEN"] = "test-token"
    try:
        inspected = inspect_ghcr_manifest.inspect_reference(
            "ghcr.io/gehorak/runner-terraform:0.4.0"
        )
    finally:
        inspect_ghcr_manifest.urlopen = original_urlopen
        if previous_username is None:
            os.environ.pop("GHCR_USERNAME", None)
        else:
            os.environ["GHCR_USERNAME"] = previous_username
        if previous_token is None:
            os.environ.pop("GHCR_TOKEN", None)
        else:
            os.environ["GHCR_TOKEN"] = previous_token
    assert inspected["manifest_digest"] == "sha256:" + hashlib.sha256(published_index_body).hexdigest()
    assert inspected["platform_manifest_digest"] == platform_manifest_digest
    assert inspected["config_digest"] == DIGEST
    assert requested_urls[-1].endswith("/manifests/" + platform_manifest_digest)
    assert not registry_responses

    # Publication identity is the root image manifest digest, not the child config digest.
    assert index_digest != inspected["config_digest"]
    assert invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-image-digest",
        index_digest,
        "--candidate-image-digest",
        index_digest,
    ).stdout.strip() == "resume"

    assert inspect_ghcr_manifest.classify_response(
        200, index_body, {"Docker-Content-Digest": index_digest}
    )["manifest_digest"] == index_digest
    try:
        inspect_ghcr_manifest.classify_response(
            200, index_body, {"Docker-Content-Digest": "sha256:" + "e" * 64}
        )
    except inspect_ghcr_manifest.RegistryError:
        pass
    else:
        raise AssertionError("registry digest header mismatch was accepted")

    invalid_index = {**image_index, "manifests": image_index["manifests"][1:]}
    try:
        inspect_ghcr_manifest.classify_response(
            200, json.dumps(invalid_index).encode("utf-8")
        )
    except inspect_ghcr_manifest.RegistryError:
        pass
    else:
        raise AssertionError("index without a linux/amd64 manifest was accepted")

    duplicate_platform_index = {
        **image_index,
        "manifests": image_index["manifests"][:1] * 2,
    }
    try:
        inspect_ghcr_manifest.classify_response(
            200, json.dumps(duplicate_platform_index).encode("utf-8")
        )
    except inspect_ghcr_manifest.RegistryError:
        pass
    else:
        raise AssertionError("index with ambiguous linux/amd64 manifests was accepted")
    assert inspect_ghcr_manifest.classify_response(
        404, b'{"errors":[{"code":"MANIFEST_UNKNOWN"}]}'
    ) == {"state": "absent"}
    for body in (
        b'{"errors":[{"code":"MANIFEST_UNKNOWN"},{"code":"DENIED"}]}',
        b'{"errors":[{"code":"MANIFEST_UNKNOWN"}],"status":"inconsistent"}',
    ):
        try:
            inspect_ghcr_manifest.classify_response(404, body)
        except inspect_ghcr_manifest.RegistryError:
            pass
        else:
            raise AssertionError("ambiguous registry 404 was classified as absent")
    for status, body in (
        (401, b'{"errors":[{"code":"UNAUTHORIZED"}]}'),
        (403, b'{"errors":[{"code":"DENIED"}]}'),
        (404, b'{"errors":[{"code":"NAME_UNKNOWN"}]}'),
        (500, b"registry unavailable"),
    ):
        try:
            inspect_ghcr_manifest.classify_response(status, body)
        except inspect_ghcr_manifest.RegistryError:
            pass
        else:
            raise AssertionError(f"registry response {status} was not rejected")

    token_request = inspect_ghcr_manifest.build_token_request("workflow-user", "workflow-token")
    expected_authorization = "Basic " + base64.b64encode(
        b"workflow-user:workflow-token"
    ).decode("ascii")
    assert token_request.get_header("Authorization") == expected_authorization
    try:
        inspect_ghcr_manifest.build_token_request("", "")
    except inspect_ghcr_manifest.RegistryError:
        pass
    else:
        raise AssertionError("GHCR token request accepted missing workflow credentials")

    evidence = temporary / "evidence.json"
    result = invoke(
        str(ROOT / "ci/write-release-evidence.py"),
        "--output",
        str(evidence),
        "--tag",
        "v0.4.0",
        "--commit",
        SHA,
        "--image-reference",
        "ghcr.io/gehorak/runner-terraform:0.4.0",
        "--image-digest",
        DIGEST,
        "--parent-reference",
        PARENT,
        "--conformance-ref",
        SHA,
        "--sbom",
        "runner-terraform-0.4.0.sbom.spdx.json",
        "--provenance-attestation",
        "https://example.invalid/provenance",
        "--sbom-attestation",
        "https://example.invalid/sbom",
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(evidence.read_text(encoding="utf-8"))
    assert parsed["release"] == {"tag": "v0.4.0", "version": "0.4.0", "commit": SHA}
    assert parsed["image"] == {
        "reference": "ghcr.io/gehorak/runner-terraform:0.4.0",
        "digest": DIGEST,
    }

print("==> release support tests passed")
