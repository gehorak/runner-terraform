# Changelog

All notable changes to `runner-terraform` are documented here. The project uses
Semantic Versioning.

## [0.3.1]

### Added

- Immutable parent reference to released `runner-base` v0.3.1.
- Derived overlay manifest using the base-owned metadata materializer.
- Terraform 1.14.2 integrity evidence in `tools.lock` v001.
- Commit-pinned Runner base conformance and explicit Terraform domain tests.
- Offline Terraform initialization and validation fixture using `terraform_data`.
- Source-contract consistency validation for the parent, conformance, contract,
  and Terraform version references.
- Tag-gated release verification: tag binding, pinned derived conformance,
  vulnerability scanning, SBOM generation, immutable publication recovery, and
  provenance/SBOM attestations.

### Changed

- Rebuilt the repository as a strict derived image instead of carrying an
  inherited copy of the base implementation.
- Replaced plugin-directory discovery with declarative `RUNNER_TOOL_*` metadata.
- Made `runner tool terraform` the only Terraform interface.

### Removed

- Derived ownership of runtime user fields, entrypoint behavior, metadata
  parsing, base contract tests, and inherited base documentation.
- The `tf` compatibility alias and redundant derived `WORKDIR /workspace`.
- The pre-conformance release workflow that could publish without the derived
  conformance and release-security gates.

## Versioning policy

- **MAJOR** — breaking change to the derived image or domain contract.
- **MINOR** — compatible domain capability addition.
- **PATCH** — compatible fix, dependency refresh, or documentation change.
