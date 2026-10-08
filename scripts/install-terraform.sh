#!/usr/bin/env bash
# Install the fixed derived-image tool set declared by tools.lock v001.

set -Eeuo pipefail

LOCK_FILE="${1:?tools.lock path is required}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

read_lock_tool_string() {
  local tool_name="$1"
  local key="$2"
  local value=""

  value="$(
    awk -v tool_name="${tool_name}" -v key="${key}" '
      BEGIN { RS = "}" }
      $0 ~ ("\\\"name\\\"[[:space:]]*:[[:space:]]*\\\"" tool_name "\\\"") {
        value = $0
        sub(".*\\\"" key "\\\"[[:space:]]*:[[:space:]]*\\\"", "", value)
        sub("\\\".*", "", value)
        if (value == $0) {
          exit 1
        }
        values[++count] = value
      }
      END {
        if (count != 1) {
          exit 1
        }
        print values[1]
      }
    ' "${LOCK_FILE}"
  )" || fail "tools.lock must contain exactly one ${key} field for ${tool_name}"

  [[ -n "${value}" ]] || fail "tools.lock ${key} for ${tool_name} must not be empty"
  printf '%s' "${value}"
}

read_lock_tool_names() {
  awk -F'"' '
    $2 == "name" { print $4 }
  ' "${LOCK_FILE}"
}

[[ -r "${LOCK_FILE}" ]] || fail "tools.lock is not readable: ${LOCK_FILE}"

mapfile -t locked_tools < <(read_lock_tool_names)
expected_tools=(terraform terraform-docs tflint)
[[ "${locked_tools[*]}" == "${expected_tools[*]}" ]] ||
  fail "tools.lock must declare exactly: ${expected_tools[*]}"

install_archive_binary() {
  local tool_name="$1"
  local expected_source="$2"
  local archive_format="$3"
  local version=""
  local source_url=""
  local sha256=""
  local work_dir=""
  local archive=""
  local install_dir=""

  version="$(read_lock_tool_string "${tool_name}" version)"
  source_url="$(read_lock_tool_string "${tool_name}" source)"
  sha256="$(read_lock_tool_string "${tool_name}" sha256)"

  [[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "invalid ${tool_name} version: ${version}"
  [[ "${sha256}" =~ ^[0-9a-f]{64}$ ]] || fail "invalid ${tool_name} SHA256"
  [[ "${source_url}" == "${expected_source}" ]] || fail "unexpected ${tool_name} source URL"

  work_dir="$(mktemp -d)"
  archive="${work_dir}/archive"
  install_dir="${work_dir}/unpacked"
  mkdir -p "${install_dir}"

  curl --proto '=https' --tlsv1.2 -fsSLo "${archive}" "${source_url}"
  printf '%s  %s\n' "${sha256}" "${archive}" | sha256sum -c -
  case "${archive_format}" in
    zip) unzip -q "${archive}" -d "${install_dir}" ;;
    tar.gz) tar -xzf "${archive}" -C "${install_dir}" ;;
    *) fail "unsupported archive format: ${archive_format}" ;;
  esac
  [[ -f "${install_dir}/${tool_name}" ]] || fail "${tool_name} archive does not contain the expected binary"
  install -o root -g root -m 0755 "${install_dir}/${tool_name}" "/usr/local/bin/${tool_name}"
  rm -rf "${work_dir}"
}

terraform_version="$(read_lock_tool_string terraform version)"
terraform_docs_version="$(read_lock_tool_string terraform-docs version)"
tflint_version="$(read_lock_tool_string tflint version)"

install_archive_binary terraform \
  "https://releases.hashicorp.com/terraform/${terraform_version}/terraform_${terraform_version}_linux_amd64.zip" zip
install_archive_binary terraform-docs \
  "https://github.com/terraform-docs/terraform-docs/releases/download/v${terraform_docs_version}/terraform-docs-v${terraform_docs_version}-linux-amd64.tar.gz" tar.gz
install_archive_binary tflint \
  "https://github.com/terraform-linters/tflint/releases/download/v${tflint_version}/tflint_linux_amd64.zip" zip

installed_terraform_version="$(CHECKPOINT_DISABLE=1 /usr/local/bin/terraform version | awk 'NR == 1 { sub(/^Terraform v/, ""); print }')"
[[ "${installed_terraform_version}" == "${terraform_version}" ]] ||
  fail "installed Terraform version ${installed_terraform_version} does not match lock ${terraform_version}"

installed_terraform_docs_version="$(/usr/local/bin/terraform-docs version | awk 'NR == 1 { for (field_number = 1; field_number <= NF; field_number++) if ($field_number ~ /^v[0-9]+\.[0-9]+\.[0-9]+$/) { sub(/^v/, "", $field_number); print $field_number; exit } }')"
[[ "${installed_terraform_docs_version}" == "${terraform_docs_version}" ]] ||
  fail "installed terraform-docs version ${installed_terraform_docs_version} does not match lock ${terraform_docs_version}"

installed_tflint_version="$(/usr/local/bin/tflint --version | awk 'NR == 1 { print $3 }')"
[[ "${installed_tflint_version}" == "${tflint_version}" ]] ||
  fail "installed TFLint version ${installed_tflint_version} does not match lock ${tflint_version}"
