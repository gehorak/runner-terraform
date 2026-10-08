#!/usr/bin/env bash
# Apply the shared runner shell quality standard to this derived overlay only.

set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

shell_files=(
  ci/lint-shell.sh
  ci/run-release-candidate-checks.sh
  ci/test-domain.sh
  scripts/install-terraform.sh
)

for shell_file in "${shell_files[@]}"; do
  bash -n "${shell_file}"
done

shfmt -d -i 2 -ci "${shell_files[@]}"
