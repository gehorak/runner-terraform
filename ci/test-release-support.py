#!/usr/bin/env python3
"""Exercise release-only helpers without building or publishing an image."""

from __future__ import annotations

import json
import importlib.util
import base64
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
        "--existing-config-digest",
        "absent",
        "--candidate-config-digest",
        DIGEST,
    ).stdout.strip() == "publish"
    assert invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-config-digest",
        DIGEST,
        "--candidate-config-digest",
        DIGEST,
    ).stdout.strip() == "resume"
    conflict = invoke(
        str(ROOT / "ci/release-publication-state.py"),
        "--existing-config-digest",
        "sha256:" + "b" * 64,
        "--candidate-config-digest",
        DIGEST,
    )
    assert conflict.returncode == 1

    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"digest": DIGEST},
    }
    assert inspect_ghcr_manifest.classify_response(
        200, json.dumps(manifest).encode("utf-8")
    ) == {"state": "present", "config_digest": DIGEST}
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
