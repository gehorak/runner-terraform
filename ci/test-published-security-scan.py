#!/usr/bin/env python3
"""Keep published-image vulnerability monitoring pinned and policy-aligned."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github" / "workflows" / "published-security-scan.yml").read_text(
    encoding="utf-8"
)

required = (
    "schedule:",
    "release:",
    "workflow_dispatch:",
    "security-events: write",
    "repos/${GITHUB_REPOSITORY}/releases/latest",
    "latest GitHub Release tag is not strict SemVer",
    "ghcr.io/gehorak/runner-terraform:${tag#v}",
    "aquasec/trivy@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969",
    "--scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1",
    "--format sarif --output /work/trivy.sarif",
    "github/codeql-action/upload-sarif@24c54180a607b1449ed407dd24f251e4e9147c8d",
    "category: trivy-published-image",
)
for value in required:
    assert value in workflow, f"published security scan is missing {value!r}"

dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
for value in ('package-ecosystem: "docker"', 'package-ecosystem: "github-actions"'):
    assert value in dependabot, f"Dependabot policy is missing {value!r}"

security_policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
assert "GitHub Security" in security_policy
assert (ROOT / "docs" / "SECURITY.md").is_file()

print("==> published security scan contract passed")
