#!/usr/bin/env python3
"""Keep derived-image CI aligned with the runner platform quality baseline."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

required = (
    "name: Lint derived shell surface",
    "https://github.com/mvdan/sh/releases/download/v3.13.1/shfmt_v3.13.1_linux_amd64",
    "fb096c5d1ac6beabbdbaa2874d025badb03ee07929f0c9ff67563ce8c75398b1",
    "bash ci/lint-shell.sh",
    "ludeeus/action-shellcheck@00cae500b08a931fb5698e11e79bfbd38e612a38",
    "version: v0.11.0",
    "python3 ci/test-dockerfile-structure.py",
    "gehorak/runner-base/.github/workflows/derived-conformance.yml@5803155a3fe9e737668cdc196bc768f46727ec50",
    "aquasec/trivy@sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969",
)
for value in required:
    assert value in workflow, f"CI quality contract is missing {value!r}"

for action, revision in re.findall(r"^\s*uses:\s+([^@\s]+)@([^\s#]+)", workflow, re.MULTILINE):
    assert re.fullmatch(r"[0-9a-f]{40}", revision), f"{action} is not pinned by commit SHA"

print("==> CI quality contract passed")
