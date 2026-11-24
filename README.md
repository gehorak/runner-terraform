# runner-terraform

`runner-terraform` is the reference Terraform-derived image for the Runner
platform. It adds Terraform, jq, terraform-docs, and TFLint tooling to the
immutable runtime and CLI contract owned by `runner-base`.

## Status

The current public release is runner-terraform v0.4.1. Published status is
determined by its version tag, GHCR image digest, and release evidence; a
branch commit or CI success alone is not a release. The release contract is
documented in [docs/RELEASING.md](docs/RELEASING.md).

The v0.4.1 release is bound to:

- source commit: `32fc7f7eba2e732b80e1b4f1d410dd8294f31149`;
- image: `ghcr.io/gehorak/runner-terraform:0.4.1@sha256:49791a47e049e05ccf0d4e852c896275b82692a0139c327ff773cd39c8ca005f`;
- parent: `ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2`;
- Runner contract: `v001`;
- conformance bundle: `runner-base` commit `94b070419c6ce4a4e17d7639cff61a4fd1adbc63`;
- Terraform: `1.17.1` for `linux/amd64`;
- jq: `1.8.2` for `linux/amd64`;
- terraform-docs: `0.25.1` for `linux/amd64`;
- TFLint: `0.66.0` for `linux/amd64`.

## Derived-image boundary

This repository owns only:

- the `runner-terraform` overlay identity;
- Terraform-domain tool installation and integrity evidence;
- Terraform-domain tool registration;
- Terraform-specific tests and documentation.

It does not own or replace the Runner dispatcher, metadata parser, entrypoint,
runtime user, `HOME`, shell, workdir, base commands, or parent runtime files.
Those remain inherited unchanged from the pinned `runner-base` artifact.

## Tool interface

Canonical invocation:

```text
runner tool jq [arguments...]
runner tool terraform [arguments...]
runner tool terraform-docs [arguments...]
runner tool tflint [arguments...]
```

## Local validation

Run from Linux or WSL with Docker, Git, Bash, Make, Python 3, and `shfmt`
available. CI also runs ShellCheck over the derived shell surface.

```bash
make check
```

`make check` performs shell and JSON validation, builds from the exact parent
digest, checks out the exact conformance commit through tag `v0.3.3`, verifies
the commit identity, runs Runner base conformance, and executes the Terraform
domain contract. It also validates the release workflow, tag-bound manifest
preparation, immutable-publication recovery, and release-evidence writer.

A shorter domain-only cycle is available:

```bash
make domain-test
```

## Direct usage

```bash
make build
docker run --rm runner-terraform:dev info --format json
docker run --rm runner-terraform:dev tool jq --version
docker run --rm runner-terraform:dev tool terraform version
docker run --rm runner-terraform:dev tool terraform-docs version
docker run --rm runner-terraform:dev tool tflint --version
```

A working directory can be mounted at the inherited `/workspace` path:

```bash
docker run --rm \
  --mount type=bind,src="$PWD",dst=/workspace \
  runner-terraform:dev \
  tool terraform validate
```

Credentials, backend configuration, approvals, state policy, and deployment
orchestration remain external responsibilities.

## Integrity model

Runtime tool metadata is declared in `image.manifest`. Download source and
SHA-256 evidence are recorded separately in
`contracts/tools-lock/v001/tools.lock.json`. The build verifies each locked
artifact before installing the four declared runtime tools.

`jq` supports machine-readable Terraform outputs such as `terraform output -json`.
TFLint's Terraform ruleset is bundled in its pinned binary, so the domain test
does not download plugins. If a project enables external provider rulesets,
TFLint may access GitHub and writes plugins to its plugin directory; callers
control that cache and network access. Terraform provider initialization still
uses the project's provider lock file and any configured registry or mirror.

Trivy is not installed in the runtime image. CI invokes a digest-pinned Trivy
container to scan the exact candidate image and the repository's Terraform
acceptance fixture. A separate intentionally insecure S3 fixture verifies that
the scanner reports its expected high-severity rule. These fixtures are the
only Terraform configurations tracked in this repository; no production
infrastructure configuration is present.

Local WSL2 and GitHub Actions both exercise `linux/amd64`. Exact tool artifacts
are verified against the same SHA-256 lock; provider downloads and optional
external TFLint plugins remain workload dependencies and are not bundled into
the image. The acceptance suite fetches the pinned `hashicorp/random` 3.6.3
provider to verify repeated read-only lockfile initialization.

## Parent upgrade policy

A new `runner-base` digest is adopted only through a dedicated pull request.
That PR must update every recorded parent reference, rebuild from the new exact
digest, and pass the commit-pinned base conformance plus the full Terraform
domain contract. Floating tags and silent digest refreshes are not accepted.

## Release policy

An official release is a strict SemVer tag on `main`, not a GitHub release page
or a mutable container tag alone. The tag workflow rebuilds a tag-bound image,
runs the pinned derived conformance, rejects fixable high and critical CVEs,
generates an SPDX SBOM, publishes an immutable GHCR version tag, creates
provenance and SBOM attestations, and attaches the SBOM plus release evidence
to the GitHub release. See [docs/RELEASING.md](docs/RELEASING.md).

## Security

The derived-image security boundary, CVE policy, published-image monitoring,
and private reporting guidance are in [SECURITY.md](SECURITY.md) and
[docs/SECURITY.md](docs/SECURITY.md).

## License

MIT. See `LICENSE`.
