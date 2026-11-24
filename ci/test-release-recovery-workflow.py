#!/usr/bin/env python3
"""Keep v0.4.0 recovery bound to the published tag and image digest."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github" / "workflows" / "recover-v040.yml").read_text(
    encoding="utf-8"
)

required = (
    "workflow_dispatch:",
    "group: runner-terraform-release",
    "contents: write",
    "packages: write",
    "attestations: write",
    "id-token: write",
    "if: github.ref == 'refs/heads/main'",
    "TAG: v0.4.0",
    "EXPECTED_COMMIT: 3e3632734cbd670464d6df58a6db1501b220595a",
    "EXPECTED_IMAGE_DIGEST: sha256:61ce44fa41655547c6f63197dd55bbffa2cb2b986ff6ab3038406a7f43c63df7",
    "ref: ${{ steps.target.outputs.commit }}",
    "ci/inspect-ghcr-manifest.py",
    "linux/amd64 manifest",
    "docker pull --platform linux/amd64",
    "ci/run-release-candidate-checks.sh",
    "aquasec/trivy@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969",
    "anchore/sbom-action@66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c",
    "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
    "ci/write-release-evidence.py",
    "softprops/action-gh-release@efb35369e0ad2afab669f228072c1b0d510eae64",
    "docker buildx imagetools create",
    "for alias in 0.4 latest",
    "git ls-remote origin \"refs/tags/${TAG}^{}\"",
)
for value in required:
    assert value in workflow, f"recovery workflow is missing {value!r}"

assert workflow.index("Validate fixed recovery target") < workflow.index(
    "Inspect immutable GHCR image"
)
assert workflow.index("Inspect immutable GHCR image") < workflow.index(
    "Pull and validate exact published image"
)
conformance_step = workflow.split(
    "      - name: Run v0.4.0 derived conformance\n", 1
)[1].split("\n      - name:", 1)[0]
assert "EXPECTED_IMAGE_VERSION: ${{ env.VERSION }}" in conformance_step
assert "EXPECTED_IMAGE_REVISION: ${{ steps.target.outputs.commit }}" in conformance_step
assert workflow.index("Scan exact published release image") < workflow.index(
    "Attest published image provenance"
)
assert workflow.index("Attest published image SBOM") < workflow.index(
    "Write v0.4.0 release evidence"
)
assert workflow.index("Write v0.4.0 release evidence") < workflow.index(
    "Revalidate v0.4.0 tag before release publication"
)
assert workflow.index("Revalidate v0.4.0 tag before release publication") < workflow.index(
    "Publish release evidence assets"
)
assert workflow.index("Publish release evidence assets") < workflow.index(
    "Publish convenience aliases after immutable evidence"
)
assert "docker image push" not in workflow
assert "git push" not in workflow

action_pins = re.findall(r"^\s*uses:\s+([^@\s]+)@([^\s#]+)", workflow, re.MULTILINE)
assert action_pins, "recovery workflow must declare pinned actions"
for action, revision in action_pins:
    assert re.fullmatch(r"[0-9a-f]{40}", revision), f"{action} is not pinned by commit SHA"

print("==> v0.4.0 recovery workflow contract passed")
