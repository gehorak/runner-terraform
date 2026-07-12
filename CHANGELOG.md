# Changelog

All notable changes to `runner-terraform` are documented here. The project uses
Semantic Versioning. No public `runner-terraform` release exists yet.

## [Unreleased] - runner-base v0.3.0 reference adoption

### Added

- Immutable parent reference to released `runner-base` v0.3.0.
- Derived overlay manifest using the base-owned metadata materializer.
- Terraform 1.14.2 integrity evidence in `tools.lock` v001.
- Commit-pinned Runner base conformance and explicit Terraform domain tests.
- Offline Terraform initialization and validation fixture using `terraform_data`.

### Changed

- Rebuilt the repository as a strict derived image instead of carrying an
  inherited copy of the base implementation.
- Replaced plugin-directory discovery with declarative `RUNNER_TOOL_*` metadata.
- Made `runner tool terraform` the canonical Terraform interface; `tf` remains
  only a declared compatibility alias.

### Removed

- Derived ownership of runtime user fields, entrypoint behavior, metadata
  parsing, base contract tests, and inherited base documentation.
- The pre-conformance release workflow; image publication remains deferred until
  this reference candidate has passed review and conformance.

## Versioning policy

- **MAJOR** — breaking change to the derived image or domain contract.
- **MINOR** — compatible domain capability addition.
- **PATCH** — compatible fix, dependency refresh, or documentation change.
