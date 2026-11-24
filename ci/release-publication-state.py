#!/usr/bin/env python3
"""Choose a safe immutable-release publication action from image digests."""

from __future__ import annotations

import argparse
import re
import sys


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing-image-digest", required=True)
    parser.add_argument("--candidate-image-digest", required=True)
    args = parser.parse_args()
    try:
        if SHA256.fullmatch(args.candidate_image_digest) is None:
            raise ValueError("candidate image digest must be sha256")
        if args.existing_image_digest == "absent":
            print("publish")
            return 0
        if SHA256.fullmatch(args.existing_image_digest) is None:
            raise ValueError("existing image digest must be sha256 or absent")
        if args.existing_image_digest != args.candidate_image_digest:
            raise ValueError("existing immutable release does not match the tested candidate image digest")
        print("resume")
        return 0
    except ValueError as error:
        print(f"ERROR: unsafe release recovery: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
