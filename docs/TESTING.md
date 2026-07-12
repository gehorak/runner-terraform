# Testing runner-terraform

## Test ownership

Runner platform behavior is tested by the immutable conformance bundle supplied
by `runner-base`. This repository does not copy or maintain the base test suite.
It owns only the Terraform domain assertions in `ci/test-domain.sh`.

## Pinned conformance inputs

- Base image: `ghcr.io/gehorak/runner-base:0.3.0@sha256:8e663302934d78f5edd77f7c07cf3f66813085f1922f5a27ad379a6ca6831003`
- Contract: `v001`
- Conformance commit: `4bd01b01ab063a4f3bd2ce8bd3748577beb9e71f`
- Tools lock: `contracts/tools-lock/v001/tools.lock.json`
- Domain test: `ci/test-domain.sh`

GitHub Actions invokes the reusable workflow from the exact conformance commit.
Local `make conformance` checks out tag `v0.3.0`, verifies that it resolves to the
same full commit, and runs the same conformance script.

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
- Runner 0.3.0 and contract v001 are inherited unchanged;
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
