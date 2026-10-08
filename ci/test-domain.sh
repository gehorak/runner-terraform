#!/usr/bin/env bash
# Explicit runner-terraform domain contract exercised after base conformance.

set -Eeuo pipefail

IMAGE="${IMAGE:?IMAGE variable must be set}"
BASE_REFERENCE="${BASE_REFERENCE:?BASE_REFERENCE variable must be set}"
RUNNER_CONFORMANCE_VERSION="${RUNNER_CONFORMANCE_VERSION:?RUNNER_CONFORMANCE_VERSION variable must be set}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/test-source-contract.py"

EXPECTED_BASE_REFERENCE="ghcr.io/gehorak/runner-base:0.3.2@sha256:23ca54058c01e5362e89c2746f794b637584842df803992d8568f64d302a8cf0"
EXPECTED_RUNNER_VERSION="runner 0.3.2 (contract v001)"
EXPECTED_TERRAFORM_VERSION="1.16.4"
EXPECTED_TFLINT_VERSION="0.64.0"
EXPECTED_TRIVY_VERSION="0.74.0"
EXPECTED_IMAGE_VERSION="${EXPECTED_IMAGE_VERSION:-0.1.0}"
EXPECTED_IMAGE_REVISION="${EXPECTED_IMAGE_REVISION:-local}"

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
INFO_JSON="${info_json}" EXPECTED_TERRAFORM_VERSION="${EXPECTED_TERRAFORM_VERSION}" EXPECTED_TFLINT_VERSION="${EXPECTED_TFLINT_VERSION}" EXPECTED_TRIVY_VERSION="${EXPECTED_TRIVY_VERSION}" EXPECTED_IMAGE_VERSION="${EXPECTED_IMAGE_VERSION}" EXPECTED_IMAGE_REVISION="${EXPECTED_IMAGE_REVISION}" python3 - <<'PY'
import json
import os

info = json.loads(os.environ["INFO_JSON"])
expected_terraform = os.environ["EXPECTED_TERRAFORM_VERSION"]
expected_tflint = os.environ["EXPECTED_TFLINT_VERSION"]
expected_trivy = os.environ["EXPECTED_TRIVY_VERSION"]
expected_image_version = os.environ["EXPECTED_IMAGE_VERSION"]
expected_image_revision = os.environ["EXPECTED_IMAGE_REVISION"]

assert info["schema_version"] == 1
assert info["runner"] == {
    "name": "runner",
    "version": "0.3.2",
    "contract_version": "v001",
}
assert info["image"] == {
    "name": "runner-terraform",
    "version": expected_image_version,
    "domain": "terraform",
    "role": "terraform",
    "revision": expected_image_revision,
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
        "aliases": [],
    },
    {
        "name": "tflint",
        "version": expected_tflint,
        "aliases": [],
    },
    {
        "name": "trivy",
        "version": expected_trivy,
        "aliases": [],
    },
]
PY

terraform_output="$(docker run --rm -e CHECKPOINT_DISABLE=1 "${IMAGE}" tool terraform version)"
grep -Fqx "Terraform v${EXPECTED_TERRAFORM_VERSION}" <<<"$(head -n 1 <<<"${terraform_output}")" ||
  fail "canonical Terraform invocation reported an unexpected version"

tflint_output="$(docker run --rm "${IMAGE}" tool tflint --version)"
grep -Fqx "TFLint version ${EXPECTED_TFLINT_VERSION}" <<<"$(head -n 1 <<<"${tflint_output}")" ||
  fail "canonical TFLint invocation reported an unexpected version"

trivy_output="$(docker run --rm "${IMAGE}" tool trivy --version)"
grep -Fqx "Version: ${EXPECTED_TRIVY_VERSION}" <<<"$(head -n 1 <<<"${trivy_output}")" ||
  fail "canonical Trivy invocation reported an unexpected version"

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

set +e
docker run --rm -e CHECKPOINT_DISABLE=1 "${IMAGE}" tool terraform version -invalid-flag \
  >"${scratch}/terraform-child-failure.out" 2>"${scratch}/terraform-child-failure.err"
terraform_child_status=$?
set -e
[[ ${terraform_child_status} -eq 1 ]] ||
  fail "Terraform child failure returned ${terraform_child_status}, expected 1"

set +e
docker run --rm "${IMAGE}" tool missing-tool >"${scratch}/missing.out" 2>"${scratch}/missing.err"
missing_status=$?
set -e
[[ ${missing_status} -eq 4 ]] || fail "unknown tool returned ${missing_status}, expected 4"
grep -Fq "RUNNER_E_NOT_FOUND" "${scratch}/missing.err" ||
  fail "unknown tool did not emit RUNNER_E_NOT_FOUND"

cat >"${scratch}/main.tf" <<'HCL'
terraform {
  required_version = "= 1.16.4"
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
