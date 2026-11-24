#!/usr/bin/env bash
# Run the pinned runner-base conformance bundle against a tag-bound candidate.

set -Eeuo pipefail

IMAGE="${IMAGE:?IMAGE must identify the already-built release candidate}"
BASE_REFERENCE="ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2"
CONFORMANCE_TAG="v0.3.3"
CONFORMANCE_REF="94b070419c6ce4a4e17d7639cff61a4fd1adbc63"
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

env \
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
