# Testing runner-terraform

## Test ownership

Runner platform behavior is tested by the immutable conformance bundle supplied
by `runner-base`. This repository does not copy or maintain the base test suite.
It owns the Terraform, jq, terraform-docs, and TFLint domain assertions in
`ci/test-domain.sh`.

## Pinned conformance inputs

- Base image: `ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2`
- Contract: `v001`
- Conformance commit: `94b070419c6ce4a4e17d7639cff61a4fd1adbc63`
- Tools lock: `contracts/tools-lock/v001/tools.lock.json`
- Domain test: `ci/test-domain.sh`

GitHub Actions invokes the reusable workflow from the exact conformance commit.
Local `make conformance` checks out tag `v0.3.3`, verifies that it resolves to the
same full commit, and runs the same conformance script.

## Release verification

### Non-publishing candidate build

`Build and validate derived image` is a deliberately portable CI template for
runner-derived images. Its job-level inputs declare the candidate tag, immutable
parent reference, Runner version, and contract version. The visible steps are:

- build the local linux/amd64 candidate image;
- compare its OCI parent label to the immutable parent reference;
- verify the inherited Runner version and contract; and
- invoke the repository-owned domain contract as the derivation extension hook.

The job never pushes an image and never creates a release. A new derivative can
copy the job, replace its declared inputs and domain-test path, and retain the
same parent and inherited-contract checks.

The pull-request CI additionally validates the release-workflow contract and
release-only helpers. It builds a separate candidate image and fails on fixable
high or critical CVEs using the digest-pinned Trivy scanner container, Trivy
0.74.0 (`sha256:62b1e65e8869bc4b4c6aa4fa2b21595256c7c2f6018a9d9ad61caf87187c1969`).
It scans a clean Terraform fixture for high or critical misconfigurations and
checks that an intentionally insecure S3 fixture produces the expected
high-severity `AWS-0086` finding. Those fixtures are this repository's only
Terraform configurations; they do not represent external workspaces.

The derived shell surface is checked with Bash syntax validation, a
SHA-256-verified `shfmt` 3.13.1 binary, and ShellCheck. A repository-owned
Dockerfile structure test rejects a floating parent, `ADD`, runtime identity
build arguments, and any override of parent-owned `ENTRYPOINT`, `CMD`, or
`WORKDIR`.

The tag workflow never publishes an untested image. For a strict `vMAJOR.MINOR.PATCH`
tag that points exactly at `main`, it:

- creates a build context whose image version and revision equal the tag and
  tagged commit;
- builds the candidate and reruns the pinned `runner-base` derived conformance,
  including the Terraform domain contract;
- scans that exact candidate, generates an SPDX SBOM, and then either publishes
  the new immutable version tag or verifies that a recovery run has the same
  linux/amd64 image configuration digest; the inspector validates the root
  manifest and child descriptor, and compares the child configuration with the
  exact tested candidate before attestation;
- creates provenance and SBOM attestations and publishes the SBOM plus a
  machine-readable release-evidence asset.

The release state classifier and workflow ordering are verified locally by
`make lint` without a tag or publication. Live GHCR state inspection requires
network access and recognizes only a confirmed `MANIFEST_UNKNOWN` response as
an absent version tag.

After the first release, a scheduled workflow resolves the latest GitHub
Release to its immutable digest, scans it with the same Trivy policy, and
uploads SARIF under `trivy-published-image` in GitHub Security. Before the
first release, the scheduled scan has no target and exits without a report.

## Base conformance guarantees

The base bundle validates:

- the immutable SemVer-plus-digest parent reference;
- the v001 tools-lock structure and lexical tool ordering;
- exact agreement between locked tool names and runtime Runner metadata;
- inherited Runner contract version;
- root ownership and runtime-user non-writability of parent-owned metadata,
  dispatcher, and parser files;
- execution of the repository-owned domain test.

## Domain-tool guarantees

`ci/test-domain.sh` validates:

- the OCI parent label equals the conformance parent reference;
- Runner 0.3.3 and contract v001 are inherited unchanged;
- image identity, runtime identity, and the jq, Terraform, terraform-docs, and TFLint
  registry entries are exact;
- `runner tool jq` reports 1.8.2 and parses a Terraform-shaped JSON output;
- `runner tool terraform` executes Terraform 1.17.1;
- `runner tool terraform-docs` executes version 0.25.1 and generates a resource
  table from a local fixture;
- `runner tool tflint` executes version 0.66.0 and reports a missing required Terraform version from a local
  fixture using the bundled Terraform ruleset, without downloading plugins;
- Trivy is absent from runtime registration; CI separately scans the exact image
  and clean Terraform fixture with its pinned scanner container, and detects a
  known HIGH finding in the intentionally insecure fixture;
- source references remain consistent across the build, CI, local validation,
  domain test, and candidate documentation;
- a Terraform child failure preserves exit code 1 through `runner tool`;
- an unknown tool fails with exit code 4 and `RUNNER_E_NOT_FOUND`;
- a minimal offline configuration can be formatted, initialized, and validated
  as the inherited non-root runtime user; and
- a locked `hashicorp/random` 3.6.3 fixture can be initialized twice in
  `-lockfile=readonly` mode and validated without changing its committed lock.

## Reproducibility and network boundaries

Local WSL2 and GitHub Actions use the same `linux/amd64` image, tool lock,
fixtures, and return-code assertions. Every runtime CLI artifact is downloaded
over HTTPS and checked against the SHA-256 recorded in
`contracts/tools-lock/v001/tools.lock.json`.

The `terraform-docs`, bundled TFLint, and built-in-provider fixtures are
offline. The provider-lock acceptance fixture contacts the Terraform Registry
to fetch the exact locked `hashicorp/random` 3.6.3 package; project provider
versions and checksums belong in each project's committed
`.terraform.lock.hcl`. TFLint configurations that add
external rulesets own their plugin network access and cache. Trivy's CI scanner
may fetch misconfiguration checks or vulnerability data; the CI job shares one
temporary cache across image and Terraform scans, outside the runtime image.

## Commands

```bash
make domain-test
make conformance
make check
```

A parent digest or conformance commit change is incomplete until `make check`
and the pull-request CI job both pass.
