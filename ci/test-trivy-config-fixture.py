#!/usr/bin/env python3
"""Require the pinned Trivy checks bundle to find the known insecure Terraform fixture."""

from __future__ import annotations

import json
import sys


report = json.load(sys.stdin)
results = report.get("Results") if isinstance(report, dict) else None
findings = [
    finding
    for result in results or []
    if isinstance(result, dict)
    for finding in result.get("Misconfigurations") or []
    if isinstance(finding, dict)
]
expected_id = "AWS-0086"
if not any(
    finding.get("ID") == expected_id and finding.get("Severity", "").upper() == "HIGH"
    for finding in findings
):
    print(f"ERROR: Trivy did not report expected HIGH finding {expected_id}", file=sys.stderr)
    raise SystemExit(1)

print(f"==> Trivy detected expected HIGH Terraform misconfiguration {expected_id}")
