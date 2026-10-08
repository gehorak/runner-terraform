#!/usr/bin/env python3
"""Exercise release-only helpers without building or publishing an image."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SHA = "0123456789abcdef0123456789abcdef01234567"
DIGEST = "sha256:" + "a" * 64
PARENT = "ghcr.io/gehorak/runner-base:0.3.2@sha256:23ca54058c01e5362e89c2746f794b637584842df803992d8568f64d302a8cf0"


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
        "v0.3.1",
        "--revision",
        SHA,
    )
    assert result.returncode == 0, result.stderr
    assert prepared.read_text(encoding="utf-8") == (
        "RUNNER_IMAGE_VERSION=0.3.1\nRUNNER_IMAGE_REVISION=" + SHA + "\n"
    )
    invalid_tag = invoke(
        str(ROOT / "ci/prepare-release-manifest.py"),
        "--input",
        str(manifest),
        "--output",
        str(prepared),
        "--tag",
        "0.3.1",
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

    evidence = temporary / "evidence.json"
    result = invoke(
        str(ROOT / "ci/write-release-evidence.py"),
        "--output",
        str(evidence),
        "--tag",
        "v0.3.1",
        "--commit",
        SHA,
        "--image-reference",
        "ghcr.io/gehorak/runner-terraform:0.3.1",
        "--image-digest",
        DIGEST,
        "--parent-reference",
        PARENT,
        "--conformance-ref",
        SHA,
        "--sbom",
        "runner-terraform-0.3.1.sbom.spdx.json",
        "--provenance-attestation",
        "https://example.invalid/provenance",
        "--sbom-attestation",
        "https://example.invalid/sbom",
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(evidence.read_text(encoding="utf-8"))
    assert parsed["release"] == {"tag": "v0.3.1", "version": "0.3.1", "commit": SHA}
    assert parsed["image"] == {
        "reference": "ghcr.io/gehorak/runner-terraform:0.3.1",
        "digest": DIGEST,
    }

print("==> release support tests passed")
