# Changelog

All notable changes to `runner-terraform` are documented here. The project uses
Semantic Versioning.

## [Unreleased]

## [0.4.1]

### Fixed

- GHCR release verification now supports OCI image indexes and Docker manifest
  lists, validates the linux/amd64 child manifest, and compares the published
  root digest with the tested BuildKit image digest. Release builds use stable
  commit metadata and rely on GitHub attestations instead of build-time inline
  provenance for repeatable candidate identity.
- Added pinned recovery workflows for existing `v0.4.0` and `v0.4.1` images to
  complete validation and release evidence without rebuilding or moving their
  immutable tags.

### Tests

- Added registry response and recovery-workflow contract coverage for release
  verification and evidence recovery.

## [0.4.0]

### Added

- Non-publishing CI candidate-image build with reusable parent and inherited
  Runner contract checks.
- jq 1.8.2, terraform-docs 0.25.1, and TFLint 0.66.0 as integrity-pinned
  runtime tools alongside Terraform.
- Digest-pinned Trivy image and Terraform-fixture scans in CI.
- Adopted runner-base v0.3.3 by immutable digest and pinned Terraform CLI 1.17.1.
- Refreshed pinned `docker/login-action` to v4.8.0,
  `anchore/sbom-action` to v0.24.3, and
  `github/codeql-action/upload-sarif` to v4.39.4.

### Changed

- Removed Trivy from the runtime image; CI retains its separately pinned scanner.
- Release recovery distinguishes a confirmed absent GHCR manifest from
  registry errors and verifies the published linux/amd64 image configuration
  against the tested candidate before attestation.

### Tests

- Added functional Terraform documentation, TFLint, and jq acceptance fixtures.

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
