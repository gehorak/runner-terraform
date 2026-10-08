# Security model for runner-terraform

## Scope and ownership

`runner-terraform` owns the Terraform archive lock, derived image metadata,
Terraform domain contract, and release automation. It inherits the Runner
runtime, dispatcher, entrypoint, runtime user, and parent operating-system
packages from the immutable `runner-base` reference declared in this
repository.

Report a vulnerability privately through GitHub Security Advisories for this
repository. Include the affected immutable image reference and digest when
available. Vulnerabilities in inherited Runner behavior or the parent image
should also be reported to `runner-base`.

## Runtime controls

- Do not mount `/var/run/docker.sock` into the image. It gives workloads
  effective control over the host Docker daemon.
- Do not forward an SSH agent unless the invoked tool requires it. Prefer a
  narrowly scoped deploy key or short-lived credential.
- Mount only required workspace paths; avoid broad host mounts such as the user
  home directory or repository parent.
- Prefer a read-only root filesystem, drop Linux capabilities, and set
  `no-new-privileges`. Add writable mounts or tmpfs only where Terraform needs
  them.
- Use a fixed SemVer-and-digest image reference from release evidence in
  automation. Do not use `latest`.

Example hardening envelope for a reviewed immutable image reference:

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  -v "$PWD:/workspace:rw" \
  ghcr.io/gehorak/runner-terraform:<released-version>@sha256:<published-digest> \
  info
```

## Build and release gates

Pull-request CI and tag-gated releases build a fresh candidate image, run the
commit-pinned Runner derived conformance bundle, and reject fixable `HIGH` and
`CRITICAL` vulnerabilities with digest-pinned Trivy 0.74.0. The policy uses
`--ignore-unfixed`: findings with no available remediation are recorded for
triage but do not silently block a release that cannot yet be repaired. Any
exception for a blocking finding must record the scanner, advisory, affected
digest, expiry date, and remediation version; it requires explicit renewal.

The release workflow scans the same tested image before it publishes the
immutable version tag. It then creates an SPDX SBOM, provenance and SBOM
attestations, and release evidence bound to the published digest.

## Published-image monitoring

After a release exists, the scheduled published-image scan resolves the latest
GitHub Release to its immutable GHCR digest, applies the same Trivy policy, and
uploads SARIF to GitHub Security. The scheduled workflow has no image target
before the first release and exits successfully without a scan in that state.

## Dependency maintenance

Dependabot monitors the Dockerfile base reference and GitHub Actions monthly.
Dependency updates remain subject to the normal conformance and CVE gates; an
automated update is not release evidence.

## Security response

For a critical defect, publish a new fixed SemVer release and document the
upgrade digest in release evidence. Never silently replace an immutable image
tag or digest.
