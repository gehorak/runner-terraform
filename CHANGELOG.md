# Changelog

All notable changes to `runner-terraform` are documented here. The project uses
Semantic Versioning.

## [Unreleased]

### Added

- Non-publishing CI candidate-image build with reusable parent and inherited
  Runner contract checks.
- terraform-docs 0.24.0 and TFLint 0.64.0 as integrity-pinned runtime tools
  alongside Terraform.

## [0.3.2]

### Added

- Immutable parent reference to released `runner-base` v0.3.2.
- Derived overlay manifest using the base-owned metadata materializer.
- Terraform 1.16.4 integrity evidence in `tools.lock` v001.
- Trivy 0.74.0 pinned for candidate and release vulnerability scans.
- Scheduled scan of the latest published immutable digest with SARIF reporting.
- Dependabot coverage for the Dockerfile parent reference and GitHub Actions.
- Release build action pin aligned with the reviewed `runner-base` v0.3.2 pin.
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
