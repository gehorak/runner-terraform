#!/usr/bin/env bash
# Run the pinned runner-base conformance bundle against a tag-bound candidate.

set -Eeuo pipefail

IMAGE="${IMAGE:?IMAGE must identify the already-built release candidate}"
BASE_REFERENCE="ghcr.io/gehorak/runner-base:0.3.1@sha256:e4c9cbe6c4faf07984beaa2a6bb857e575dc84676a6e2e76b875e8cb83d615e0"
CONFORMANCE_TAG="v0.3.1"
CONFORMANCE_REF="65e5386e56f6b986c47e746353da19a59f6136a1"
CONTRACT_VERSION="v001"
TOOLS_LOCK="contracts/tools-lock/v001/tools.lock.json"
DOMAIN_TEST="ci/test-domain.sh"

work_dir="$(mktemp -d)"
trap 'rm -rf "${work_dir}"' EXIT
conformance_dir="${work_dir}/runner-base"

python3 ci/test-source-contract.py
git clone --depth 1 --branch "${CONFORMANCE_TAG}" \
  https://github.com/gehorak/runner-base.git "${conformance_dir}"
test "$(git -C "${conformance_dir}" rev-parse HEAD)" = "${CONFORMANCE_REF}"

IMAGE="${IMAGE}" \
BASE_REFERENCE="${BASE_REFERENCE}" \
RUNNER_CONFORMANCE_VERSION="${CONTRACT_VERSION}" \
bash "${conformance_dir}/ci/derived-conformance.sh" \
  --image "${IMAGE}" \
  --base-reference "${BASE_REFERENCE}" \
  --contract-version "${CONTRACT_VERSION}" \
  --tools-lock "${TOOLS_LOCK}" \
  --domain-test "${DOMAIN_TEST}"

echo "==> tag-bound release candidate conformance passed"
