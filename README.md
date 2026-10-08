# runner-terraform

`runner-terraform` is the reference Terraform-derived image for the Runner
platform. It adds one domain tool to the immutable runtime and CLI contract
owned by `runner-base`.

## Status

Reference candidate for the first repository-level adoption of the
`runner-base` v0.3.2 derived-image contract. Published status is determined by
an immutable version tag, its GHCR image, and release evidence; a branch commit
or CI success alone is not a release. The release contract is documented in
[docs/RELEASING.md](docs/RELEASING.md).

The candidate is bound to:

- parent: `ghcr.io/gehorak/runner-base:0.3.2@sha256:23ca54058c01e5362e89c2746f794b637584842df803992d8568f64d302a8cf0`;
- Runner contract: `v001`;
- conformance bundle: `runner-base` commit `5803155a3fe9e737668cdc196bc768f46727ec50`;
- Terraform: `1.16.4` for `linux/amd64`.

## Derived-image boundary

This repository owns only:

- the `runner-terraform` overlay identity;
- Terraform installation and integrity evidence;
- Terraform tool registration;
- Terraform-specific tests and documentation.

It does not own or replace the Runner dispatcher, metadata parser, entrypoint,
runtime user, `HOME`, shell, workdir, base commands, or parent runtime files.
Those remain inherited unchanged from the pinned `runner-base` artifact.

## Tool interface

Canonical invocation:

```text
runner tool terraform [arguments...]
```

## Local validation

Run from Linux or WSL with Docker, Git, Bash, Make, Python 3, and `shfmt`
available. CI also runs ShellCheck over the derived shell surface.

```bash
make check
```

`make check` performs shell and JSON validation, builds from the exact parent
digest, checks out the exact conformance commit through tag `v0.3.2`, verifies
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
docker run --rm runner-terraform:dev tool terraform version
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
`contracts/tools-lock/v001/tools.lock.json`. The build verifies the locked
archive before installing Terraform.

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
