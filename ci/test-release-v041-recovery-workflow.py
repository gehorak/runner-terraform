#!/usr/bin/env python3
"""Keep v0.4.1 recovery pinned to its already-published immutable image."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github" / "workflows" / "recover-v041.yml").read_text(
    encoding="utf-8"
)

required = (
    "workflow_dispatch:",
    "group: runner-terraform-release",
    "if: github.ref == 'refs/heads/main'",
    "TAG: v0.4.1",
    "VERSION: 0.4.1",
    "EXPECTED_COMMIT: 32fc7f7eba2e732b80e1b4f1d410dd8294f31149",
    "EXPECTED_IMAGE_DIGEST: sha256:49791a47e049e05ccf0d4e852c896275b82692a0139c327ff773cd39c8ca005f",
    "docker pull --platform linux/amd64",
    "EXPECTED_IMAGE_VERSION: ${{ env.VERSION }}",
    "EXPECTED_IMAGE_REVISION: ${{ steps.target.outputs.commit }}",
    "bash ci/run-release-candidate-checks.sh",
    "aquasec/trivy@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969",
    "anchore/sbom-action@66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c",
    "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
    "ci/write-release-evidence.py",
    "softprops/action-gh-release@efb35369e0ad2afab669f228072c1b0d510eae64",
    "for alias in 0.4 latest",
)
for value in required:
    assert value in workflow, f"v0.4.1 recovery workflow is missing {value!r}"

assert workflow.index("Validate fixed recovery target") < workflow.index(
    "Inspect immutable GHCR image"
)
assert workflow.index("Inspect immutable GHCR image") < workflow.index(
    "Pull and validate exact published image"
)
assert workflow.index("Run v0.4.1 derived conformance") < workflow.index(
    "Scan exact published release image"
)
assert workflow.index("Scan exact published release image") < workflow.index(
    "Attest published image provenance"
)
assert workflow.index("Publish release evidence assets") < workflow.index(
    "Publish convenience aliases after immutable evidence"
)
assert "docker image push" not in workflow
assert "git push" not in workflow
assert "v0.4.0" not in workflow

action_pins = re.findall(r"^\s*uses:\s+([^@\s]+)@([^\s#]+)", workflow, re.MULTILINE)
assert action_pins, "v0.4.1 recovery workflow must declare pinned actions"
for action, revision in action_pins:
    assert re.fullmatch(r"[0-9a-f]{40}", revision), f"{action} is not pinned by commit SHA"

print("==> v0.4.1 recovery workflow contract passed")
