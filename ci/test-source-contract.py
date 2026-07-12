#!/usr/bin/env python3
"""Check consistency of the immutable derived-image source contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def one_match(pattern: str, text: str, label: str) -> str:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"{label} must have exactly one matching source value")
    return matches[0]


def require_contains(relative_paths: list[str], value: str, label: str) -> None:
    missing = [path for path in relative_paths if value not in read(path)]
    if missing:
        raise ValueError(f"{label} is missing from: {', '.join(missing)}")


def main() -> int:
    dockerfile = read("Dockerfile")
    workflow = read(".github/workflows/ci.yml")
    makefile = read("Makefile")
    domain_test = read("ci/test-domain.sh")

    base_reference = one_match(r"^ARG BASE_IMAGE=(\S+)$", dockerfile, "Dockerfile base reference")
    conformance_reference = one_match(
        r"uses: gehorak/runner-base/.github/workflows/derived-conformance.yml@([0-9a-f]{40})",
        workflow,
        "workflow conformance reference",
    )
    contract_version = one_match(
        r"expected_contract_version: (v[0-9]+)",
        workflow,
        "workflow contract version",
    )

    tools_lock = json.loads(read("contracts/tools-lock/v001/tools.lock.json"))
    tools = tools_lock.get("tools")
    if not isinstance(tools, list) or len(tools) != 1 or tools[0].get("name") != "terraform":
        raise ValueError("tools.lock must declare exactly one Terraform tool")
    terraform_version = tools[0].get("version")
    if not isinstance(terraform_version, str):
        raise ValueError("tools.lock Terraform version must be a string")

    require_contains(
        [".github/workflows/ci.yml", "Makefile", "ci/test-domain.sh", "README.md", "docs/TESTING.md"],
        base_reference,
        "base reference",
    )
    require_contains(
        ["Makefile", "README.md", "docs/TESTING.md"],
        conformance_reference,
        "conformance reference",
    )
    require_contains(
        ["Makefile", "ci/test-domain.sh", "README.md", "docs/TESTING.md"],
        contract_version,
        "contract version",
    )
    require_contains(
        ["image.manifest", "ci/test-domain.sh", "README.md", "docs/TESTING.md"],
        terraform_version,
        "Terraform version",
    )

    print("==> source contract is consistent")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
