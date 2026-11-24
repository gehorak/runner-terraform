#!/usr/bin/env python3
"""Keep the tag-triggered release workflow bound to verified release gates."""

from __future__ import annotations

import re
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
    "docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc",
    "anchore/sbom-action@66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c",
    "docker/login-action@8aa5831fb8d48d8f76594c7ddde61ae58019f550",
    "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
    "ci/release-publication-state.py",
    "ci/inspect-ghcr-manifest.py",
    "GHCR_USERNAME: ${{ github.actor }}",
    "GHCR_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
    "candidate_config_digest",
    "published_config_digest",
    "--existing-config-digest",
    "--candidate-config-digest",
    'value["config_digest"]',
    'value["config_digest"]',
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
    "Verify published image matches tested candidate"
)
assert workflow.index("Verify published image matches tested candidate") < workflow.index(
    "Resolve published image digest"
)
assert workflow.index("Verify published image matches tested candidate") < workflow.index(
    "Publish release evidence assets"
)
assert "docker manifest inspect" not in workflow

action_pins = re.findall(r"^\s*uses:\s+([^@\s]+)@([^\s#]+)", workflow, re.MULTILINE)
assert action_pins, "release workflow must declare pinned actions"
for action, revision in action_pins:
    assert re.fullmatch(r"[0-9a-f]{40}", revision), f"{action} is not pinned by commit SHA"

print("==> release workflow contract passed")
