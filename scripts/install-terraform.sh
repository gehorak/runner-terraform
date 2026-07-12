#!/usr/bin/env bash
# Install the single Terraform tool declared by tools.lock v001.

set -Eeuo pipefail

LOCK_FILE="${1:?tools.lock path is required}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

read_lock_string() {
  local key="$1"
  local value=""

  value="$({
    awk -F'"' -v key="${key}" '
      $2 == key { values[++count] = $4 }
      END {
        if (count != 1) {
          exit 1
        }
        print values[1]
      }
    ' "${LOCK_FILE}"
  })" || fail "tools.lock must contain exactly one string field named ${key}"

  [[ -n "${value}" ]] || fail "tools.lock field ${key} must not be empty"
  printf '%s' "${value}"
}

[[ -r "${LOCK_FILE}" ]] || fail "tools.lock is not readable: ${LOCK_FILE}"

name="$(read_lock_string name)"
version="$(read_lock_string version)"
source_url="$(read_lock_string source)"
sha256="$(read_lock_string sha256)"

[[ "${name}" == "terraform" ]] || fail "unsupported tool in lock: ${name}"
[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "invalid Terraform version: ${version}"
[[ "${sha256}" =~ ^[0-9a-f]{64}$ ]] || fail "invalid Terraform SHA256"

expected_source="https://releases.hashicorp.com/terraform/${version}/terraform_${version}_linux_amd64.zip"
[[ "${source_url}" == "${expected_source}" ]] || fail "unexpected Terraform source URL"

work_dir="$(mktemp -d)"
trap 'rm -rf "${work_dir}"' EXIT
archive="${work_dir}/terraform.zip"
install_dir="${work_dir}/unpacked"
mkdir -p "${install_dir}"

curl --proto '=https' --tlsv1.2 -fsSLo "${archive}" "${source_url}"
printf '%s  %s\n' "${sha256}" "${archive}" | sha256sum -c -
unzip -q "${archive}" -d "${install_dir}"
[[ -f "${install_dir}/terraform" ]] || fail "Terraform archive does not contain the expected binary"

install -o root -g root -m 0755 "${install_dir}/terraform" /usr/local/bin/terraform
installed_version="$(CHECKPOINT_DISABLE=1 /usr/local/bin/terraform version | awk 'NR == 1 { sub(/^Terraform v/, ""); print }')"
[[ "${installed_version}" == "${version}" ]] || fail "installed Terraform version ${installed_version} does not match lock ${version}"
