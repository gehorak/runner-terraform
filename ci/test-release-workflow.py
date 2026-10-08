#!/usr/bin/env python3
"""Keep the tag-triggered release workflow bound to verified release gates."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

required = (
    "tags:",
    "- 'v*'",
    "contents: write",
    "packages: write",
    "attestations: write",
    "id-token: write",
    "fetch-depth: 0",
    "^v([0-9]+)\\.([0-9]+)\\.([0-9]+)$",
    "release tag must point exactly at origin/main HEAD",
    "ci/prepare-release-manifest.py",
    "ci/run-release-candidate-checks.sh",
    "aquasec/trivy@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969",
    "anchore/sbom-action@3ad7283483fc7af8ff2b4ea19663c2d5ca935e26",
    "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
    "ci/release-publication-state.py",
    "ci/write-release-evidence.py",
    "softprops/action-gh-release@efb35369e0ad2afab669f228072c1b0d510eae64",
)
for value in required:
    assert value in workflow, f"release workflow is missing {value!r}"

assert workflow.index("Run tag-bound derived conformance") < workflow.index(
    "Scan exact tested release candidate"
)
assert workflow.index("Scan exact tested release candidate") < workflow.index(
    "Publish or resume immutable tested image"
)
assert workflow.index("Publish or resume immutable tested image") < workflow.index(
    "Publish release evidence assets"
)

print("==> release workflow contract passed")
