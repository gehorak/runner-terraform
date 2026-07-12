#!/usr/bin/env bash
# Explicit runner-terraform domain contract exercised after base conformance.

set -Eeuo pipefail

IMAGE="${IMAGE:?IMAGE variable must be set}"
BASE_REFERENCE="${BASE_REFERENCE:?BASE_REFERENCE variable must be set}"
RUNNER_CONFORMANCE_VERSION="${RUNNER_CONFORMANCE_VERSION:?RUNNER_CONFORMANCE_VERSION variable must be set}"

EXPECTED_BASE_REFERENCE="ghcr.io/gehorak/runner-base:0.3.0@sha256:8e663302934d78f5edd77f7c07cf3f66813085f1922f5a27ad379a6ca6831003"
EXPECTED_RUNNER_VERSION="runner 0.3.0 (contract v001)"
EXPECTED_TERRAFORM_VERSION="1.14.2"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ "${BASE_REFERENCE}" == "${EXPECTED_BASE_REFERENCE}" ]] || fail "unexpected parent reference: ${BASE_REFERENCE}"
[[ "${RUNNER_CONFORMANCE_VERSION}" == "v001" ]] || fail "unexpected conformance version: ${RUNNER_CONFORMANCE_VERSION}"

observed_base_reference="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.base.name" }}' "${IMAGE}")"
[[ "${observed_base_reference}" == "${BASE_REFERENCE}" ]] || fail "OCI base reference does not match the conformance input"

runner_version="$(docker run --rm "${IMAGE}" --version)"
[[ "${runner_version}" == "${EXPECTED_RUNNER_VERSION}" ]] || fail "unexpected Runner version output: ${runner_version}"

info_json="$(docker run --rm "${IMAGE}" info --format json)"
INFO_JSON="${info_json}" EXPECTED_TERRAFORM_VERSION="${EXPECTED_TERRAFORM_VERSION}" python3 - <<'PY'
import json
import os

info = json.loads(os.environ["INFO_JSON"])
expected_terraform = os.environ["EXPECTED_TERRAFORM_VERSION"]

assert info["schema_version"] == 1
assert info["runner"] == {
    "name": "runner",
    "version": "0.3.0",
    "contract_version": "v001",
}
assert info["image"] == {
    "name": "runner-terraform",
    "version": "0.1.0",
    "domain": "terraform",
    "role": "terraform",
    "revision": "local",
}
assert info["runtime"] == {
    "platform": "linux",
    "architecture": "amd64",
    "user": "runner",
    "home": "/home/runner",
    "workdir": "/workspace",
    "shell": "/bin/bash",
}
assert info["tools"] == [
    {
        "name": "terraform",
        "version": expected_terraform,
        "aliases": ["tf"],
    }
]
PY

terraform_output="$(docker run --rm -e CHECKPOINT_DISABLE=1 "${IMAGE}" tool terraform version)"
grep -Fqx "Terraform v${EXPECTED_TERRAFORM_VERSION}" <<<"$(head -n 1 <<<"${terraform_output}")" \
  || fail "canonical Terraform invocation reported an unexpected version"

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

if ! docker run --rm -e CHECKPOINT_DISABLE=1 "${IMAGE}" tool tf version >"${scratch}/alias.out" 2>"${scratch}/alias.err"; then
  fail "declared tf alias failed"
fi
grep -Fq "DEPRECATED: tool alias 'tf'" "${scratch}/alias.err" \
  || fail "declared tf alias did not emit the compatibility warning"

set +e
docker run --rm "${IMAGE}" tool missing-tool >"${scratch}/missing.out" 2>"${scratch}/missing.err"
missing_status=$?
set -e
[[ ${missing_status} -eq 4 ]] || fail "unknown tool returned ${missing_status}, expected 4"
grep -Fq "RUNNER_E_NOT_FOUND" "${scratch}/missing.err" \
  || fail "unknown tool did not emit RUNNER_E_NOT_FOUND"

cat >"${scratch}/main.tf" <<'HCL'
terraform {
  required_version = "= 1.14.2"
}

resource "terraform_data" "reference" {
  input = "runner-terraform"
}
HCL
chmod 0777 "${scratch}"

common_docker_args=(
  --rm
  -e CHECKPOINT_DISABLE=1
  -e TF_IN_AUTOMATION=1
  --mount "type=bind,src=${scratch},dst=/workspace"
  "${IMAGE}"
  tool
  terraform
)

docker run "${common_docker_args[@]}" fmt -check -no-color
docker run "${common_docker_args[@]}" init -backend=false -input=false -no-color
docker run "${common_docker_args[@]}" validate -no-color

echo "==> runner-terraform domain contract passed"
