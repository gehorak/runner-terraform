# runner-terraform

`runner-terraform` is the reference Terraform-derived image for the Runner
platform. It adds one domain tool to the immutable runtime and CLI contract
owned by `runner-base`.

## Status

Reference candidate for the first repository-level adoption of the
`runner-base` v0.3.0 derived-image contract. This repository has no published
`runner-terraform` tag or release yet.

The candidate is bound to:

- parent: `ghcr.io/gehorak/runner-base:0.3.0@sha256:8e663302934d78f5edd77f7c07cf3f66813085f1922f5a27ad379a6ca6831003`;
- Runner contract: `v001`;
- conformance bundle: `runner-base` commit `4bd01b01ab063a4f3bd2ce8bd3748577beb9e71f`;
- Terraform: `1.14.2` for `linux/amd64`.

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

Run from Linux or WSL with Docker, Git, Bash, Make, and Python 3 available:

```bash
make check
```

`make check` performs shell and JSON validation, builds from the exact parent
digest, checks out the exact conformance commit through tag `v0.3.0`, verifies
the commit identity, runs Runner base conformance, and executes the Terraform
domain contract.

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

## License

MIT. See `LICENSE`.
