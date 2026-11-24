#!/usr/bin/env bash
# Explicit runner-terraform domain contract exercised after base conformance.

set -Eeuo pipefail

IMAGE="${IMAGE:?IMAGE variable must be set}"
BASE_REFERENCE="${BASE_REFERENCE:?BASE_REFERENCE variable must be set}"
RUNNER_CONFORMANCE_VERSION="${RUNNER_CONFORMANCE_VERSION:?RUNNER_CONFORMANCE_VERSION variable must be set}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/test-source-contract.py"

EXPECTED_BASE_REFERENCE="ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2"
EXPECTED_RUNNER_VERSION="runner 0.3.3 (contract v001)"
EXPECTED_TERRAFORM_VERSION="1.17.1"
EXPECTED_TERRAFORM_DOCS_VERSION="0.25.1"
EXPECTED_TFLINT_VERSION="0.66.0"
EXPECTED_JQ_VERSION="1.8.2"
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
INFO_JSON="${info_json}" EXPECTED_TERRAFORM_VERSION="${EXPECTED_TERRAFORM_VERSION}" EXPECTED_TERRAFORM_DOCS_VERSION="${EXPECTED_TERRAFORM_DOCS_VERSION}" EXPECTED_TFLINT_VERSION="${EXPECTED_TFLINT_VERSION}" EXPECTED_JQ_VERSION="${EXPECTED_JQ_VERSION}" EXPECTED_IMAGE_VERSION="${EXPECTED_IMAGE_VERSION}" EXPECTED_IMAGE_REVISION="${EXPECTED_IMAGE_REVISION}" python3 - <<'PY'
import json
import os

info = json.loads(os.environ["INFO_JSON"])
expected_terraform = os.environ["EXPECTED_TERRAFORM_VERSION"]
expected_terraform_docs = os.environ["EXPECTED_TERRAFORM_DOCS_VERSION"]
expected_tflint = os.environ["EXPECTED_TFLINT_VERSION"]
expected_jq = os.environ["EXPECTED_JQ_VERSION"]
expected_image_version = os.environ["EXPECTED_IMAGE_VERSION"]
expected_image_revision = os.environ["EXPECTED_IMAGE_REVISION"]

assert info["schema_version"] == 1
assert info["runner"] == {
    "name": "runner",
    "version": "0.3.3",
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
        "name": "jq",
        "version": expected_jq,
        "aliases": [],
    },
    {
        "name": "terraform",
        "version": expected_terraform,
        "aliases": [],
    },
    {
        "name": "terraform-docs",
        "version": expected_terraform_docs,
        "aliases": [],
    },
    {
        "name": "tflint",
        "version": expected_tflint,
        "aliases": [],
    },
]
PY

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

terraform_output="$(docker run --rm -e CHECKPOINT_DISABLE=1 "${IMAGE}" tool terraform version)"
grep -Fqx "Terraform v${EXPECTED_TERRAFORM_VERSION}" <<<"$(head -n 1 <<<"${terraform_output}")" ||
  fail "canonical Terraform invocation reported an unexpected version"

terraform_docs_output="$(docker run --rm "${IMAGE}" tool terraform-docs version)"
terraform_docs_version="$(awk 'NR == 1 { for (field_number = 1; field_number <= NF; field_number++) if ($field_number ~ /^v[0-9]+\.[0-9]+\.[0-9]+$/) { sub(/^v/, "", $field_number); print $field_number; exit } }' <<<"${terraform_docs_output}")"
[[ "${terraform_docs_version}" == "${EXPECTED_TERRAFORM_DOCS_VERSION}" ]] ||
  fail "canonical terraform-docs invocation reported an unexpected version"

tflint_output="$(docker run --rm "${IMAGE}" tool tflint --version)"
grep -Fqx "TFLint version ${EXPECTED_TFLINT_VERSION}" <<<"$(head -n 1 <<<"${tflint_output}")" ||
  fail "canonical TFLint invocation reported an unexpected version"

jq_output="$(docker run --rm "${IMAGE}" tool jq --version)"
[[ "${jq_output}" == "jq-${EXPECTED_JQ_VERSION}" ]] || fail "canonical jq invocation reported an unexpected version"

jq_result="$(printf '%s' '{"region":{"sensitive":false,"type":"string","value":"eu-west-1"}}' | docker run --rm -i "${IMAGE}" tool jq -er '.region.value')"
[[ "${jq_result}" == "eu-west-1" ]] || fail "jq did not parse Terraform output JSON"

terraform_fixture="${SCRIPT_DIR}/fixtures/terraform"
terraform_docs_output="$(docker run --rm --mount "type=bind,src=${terraform_fixture},dst=/workspace,readonly" "${IMAGE}" tool terraform-docs markdown table /workspace)"
grep -Fq "terraform_data.documented" <<<"${terraform_docs_output}" ||
  fail "terraform-docs output did not include the Terraform fixture resource"
set +e
docker run --rm "${IMAGE}" tool terraform-docs markdown table /workspace/does-not-exist \
  >"${scratch}/terraform-docs-invalid.out" 2>"${scratch}/terraform-docs-invalid.err"
terraform_docs_invalid_status=$?
set -e
[[ ${terraform_docs_invalid_status} -ne 0 ]] ||
  fail "terraform-docs accepted a missing module directory"

tflint_fixture="${SCRIPT_DIR}/fixtures/tflint-missing-version"
set +e
tflint_output="$(docker run --rm --mount "type=bind,src=${tflint_fixture},dst=/workspace,readonly" "${IMAGE}" tool tflint --chdir=/workspace 2>&1)"
tflint_status=$?
set -e
[[ ${tflint_status} -eq 2 ]] || fail "TFLint fixture returned ${tflint_status}, expected lint findings (2)"
grep -Fq "required_version" <<<"${tflint_output}" ||
  fail "TFLint did not report the missing Terraform required_version"

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

set +e
docker run --rm "${IMAGE}" tool trivy --version >"${scratch}/trivy.out" 2>"${scratch}/trivy.err"
trivy_status=$?
set -e
[[ ${trivy_status} -eq 4 ]] || fail "Trivy remained registered in the runtime (exit ${trivy_status})"
grep -Fq "RUNNER_E_NOT_FOUND" "${scratch}/trivy.err" ||
  fail "removed Trivy tool did not emit RUNNER_E_NOT_FOUND"

cat >"${scratch}/main.tf" <<'HCL'
terraform {
  required_version = "= 1.17.1"
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
docker run "${common_docker_args[@]}" init -backend=false -input=false -no-color
docker run "${common_docker_args[@]}" validate -no-color

provider_lock_fixture="${SCRIPT_DIR}/fixtures/terraform-provider-lock"
lock_hash_before="$(sha256sum "${provider_lock_fixture}/.terraform.lock.hcl")"
docker run --rm \
  -e TF_IN_AUTOMATION=1 \
  -e TF_DATA_DIR=/tmp/terraform-provider-lock \
  --mount "type=bind,src=${provider_lock_fixture},dst=/workspace,readonly" \
  --entrypoint /bin/bash "${IMAGE}" -c '
    set -Eeuo pipefail
    runner tool terraform init -backend=false -input=false -lockfile=readonly -no-color
    runner tool terraform init -backend=false -input=false -lockfile=readonly -no-color
    runner tool terraform validate -no-color
  '
lock_hash_after="$(sha256sum "${provider_lock_fixture}/.terraform.lock.hcl")"
[[ "${lock_hash_before}" == "${lock_hash_after}" ]] ||
  fail "Terraform init changed the committed provider lock file"

echo "==> runner-terraform domain contract passed"
