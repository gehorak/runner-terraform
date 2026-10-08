# Testing runner-terraform

## Test ownership

Runner platform behavior is tested by the immutable conformance bundle supplied
by `runner-base`. This repository does not copy or maintain the base test suite.
It owns only the Terraform domain assertions in `ci/test-domain.sh`.

## Pinned conformance inputs

- Base image: `ghcr.io/gehorak/runner-base:0.3.2@sha256:23ca54058c01e5362e89c2746f794b637584842df803992d8568f64d302a8cf0`
- Contract: `v001`
- Conformance commit: `5803155a3fe9e737668cdc196bc768f46727ec50`
- Tools lock: `contracts/tools-lock/v001/tools.lock.json`
- Domain test: `ci/test-domain.sh`

GitHub Actions invokes the reusable workflow from the exact conformance commit.
Local `make conformance` checks out tag `v0.3.2`, verifies that it resolves to the
same full commit, and runs the same conformance script.

## Release verification

The pull-request CI additionally validates the release-workflow contract and
release-only helpers. It builds a separate candidate image and fails on fixable
high or critical CVEs using the same digest-pinned Trivy scanner used by the
release workflow.

The tag workflow never publishes an untested image. For a strict `vMAJOR.MINOR.PATCH`
tag that points exactly at `main`, it:

- creates a build context whose image version and revision equal the tag and
  tagged commit;
- builds the candidate and reruns the pinned `runner-base` derived conformance,
  including the Terraform domain contract;
- scans that exact candidate, generates an SPDX SBOM, and then either publishes
  the new immutable version tag or verifies that a recovery run has the same
  image configuration digest;
- creates provenance and SBOM attestations and publishes the SBOM plus a
  machine-readable release-evidence asset.

These release-specific controls are verified locally by `make check` without
requiring a tag, registry credentials, or publication.

## Base conformance guarantees

The base bundle validates:

- the immutable SemVer-plus-digest parent reference;
- the v001 tools-lock structure and lexical tool ordering;
- exact agreement between locked tool names and runtime Runner metadata;
- inherited Runner contract version;
- root ownership and runtime-user non-writability of parent-owned metadata,
  dispatcher, and parser files;
- execution of the repository-owned domain test.

## Terraform domain guarantees

`ci/test-domain.sh` validates:

- the OCI parent label equals the conformance parent reference;
- Runner 0.3.2 and contract v001 are inherited unchanged;
- image identity, runtime identity, and the Terraform registry entry are exact;
- `runner tool terraform` executes Terraform 1.14.2;
- source references remain consistent across the build, CI, local validation,
  domain test, and candidate documentation;
- a Terraform child failure preserves exit code 1 through `runner tool`;
- an unknown tool fails with exit code 4 and `RUNNER_E_NOT_FOUND`;
- a minimal offline configuration can be formatted, initialized, and validated
  as the inherited non-root runtime user.

## Commands

```bash
make domain-test
make conformance
make check
```

A parent digest or conformance commit change is incomplete until `make check`
and the pull-request CI job both pass.
