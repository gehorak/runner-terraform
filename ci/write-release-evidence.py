#!/usr/bin/env python3
"""Write validated release evidence for one immutable runner-terraform image."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
PARENT = re.compile(r"^ghcr\.io/gehorak/runner-base:[0-9]+\.[0-9]+\.[0-9]+@sha256:[0-9a-f]{64}$")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--image-reference", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--parent-reference", required=True)
    parser.add_argument("--conformance-ref", required=True)
    parser.add_argument("--sbom", required=True)
    parser.add_argument("--provenance-attestation", required=True)
    parser.add_argument("--sbom-attestation", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    version = args.tag.removeprefix("v")
    if TAG.fullmatch(args.tag) is None:
        print("ERROR: tag must be strict SemVer", file=sys.stderr)
        return 1
    if SHA.fullmatch(args.commit) is None or SHA.fullmatch(args.conformance_ref) is None:
        print("ERROR: commit references must be lowercase 40-character Git SHAs", file=sys.stderr)
        return 1
    if DIGEST.fullmatch(args.image_digest) is None:
        print("ERROR: image digest must be sha256", file=sys.stderr)
        return 1
    if PARENT.fullmatch(args.parent_reference) is None:
        print("ERROR: parent reference must be an immutable runner-base reference", file=sys.stderr)
        return 1
    if args.image_reference != f"ghcr.io/gehorak/runner-terraform:{version}":
        print("ERROR: image reference must match the release version", file=sys.stderr)
        return 1

    evidence = {
        "schema_version": 1,
        "release": {"tag": args.tag, "version": version, "commit": args.commit},
        "image": {"reference": args.image_reference, "digest": args.image_digest},
        "parent": {"reference": args.parent_reference},
        "verification": {
            "derived_conformance_ref": args.conformance_ref,
            "security_scan": "trivy-vulnerability-high-critical-ignore-unfixed",
        },
        "artifacts": {
            "sbom": args.sbom,
            "provenance_attestation": args.provenance_attestation,
            "sbom_attestation": args.sbom_attestation,
        },
    }
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
