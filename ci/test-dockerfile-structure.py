#!/usr/bin/env python3
"""Reject derived-image Dockerfile drift that conformance cannot infer safely."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    require(
        re.search(
            r"^ARG BASE_IMAGE=ghcr\.io/gehorak/runner-base:[0-9]+\.[0-9]+\.[0-9]+@sha256:[0-9a-f]{64}$",
            dockerfile,
            re.MULTILINE,
        )
        is not None,
        "Dockerfile must pin the released runner-base parent by SemVer and digest",
    )
    require("FROM ${BASE_IMAGE}" in dockerfile, "Dockerfile must derive from BASE_IMAGE")
    require(
        'org.opencontainers.image.base.name="${BASE_IMAGE}"' in dockerfile,
        "Dockerfile must expose the immutable parent reference in OCI metadata",
    )
    require(
        "runner_metadata_materialize_derived_manifest" in dockerfile,
        "Dockerfile must materialize the declarative derived manifest through runner-base",
    )
    require(
        dockerfile.rstrip().endswith("USER runner"),
        "Dockerfile must re-assert the inherited non-root runner user",
    )
    require(re.search(r"^ADD\s", dockerfile, re.MULTILINE) is None, "Dockerfile must not use ADD")
    require(
        re.search(r"^ARG RUNTIME_", dockerfile, re.MULTILINE) is None,
        "runtime identity must not be a Docker build argument",
    )
    for instruction in ("ENTRYPOINT", "CMD", "WORKDIR"):
        require(
            re.search(rf"^{instruction}\s", dockerfile, re.MULTILINE) is None,
            f"Dockerfile must inherit the parent-owned {instruction} unchanged",
        )
    print("==> Dockerfile structure tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
