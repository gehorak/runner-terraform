# Releasing runner-terraform

## Authority boundary

Only a strict SemVer tag (`vMAJOR.MINOR.PATCH`) placed exactly on `main` starts
the release workflow. A pull request, a merge, a CI success, or a GitHub
release page alone is not a release.

## Release gates

The workflow rebuilds the image from the tagged source after binding
`RUNNER_IMAGE_VERSION` and `RUNNER_IMAGE_REVISION` to the tag and commit. Before
publication it runs the immutable `runner-base` derived conformance bundle and
the repository-owned Terraform domain contract, then scans the exact Docker
image tarball for fixable high and critical vulnerabilities.

After those gates pass, the workflow generates an SPDX SBOM and publishes only
the immutable `ghcr.io/gehorak/runner-terraform:<version>` tag. If that tag is
already present, recovery is allowed only when its root manifest digest matches
the digest reported by the tested BuildKit candidate. The registry inspector
also validates the root body digest, linux/amd64 child manifest digest, and
child configuration digest against the OCI index descriptor. Version-minor and
`latest` aliases are updated only after the immutable image, attestations, and
release evidence exist.

The candidate's `org.opencontainers.image.created` label uses the tagged
commit's timestamp. Inline BuildKit provenance is disabled for the image
build; the release workflow creates and attaches GitHub provenance and SBOM
attestations after testing. This keeps rebuilds for the same tag bound to a
stable image identity.

## Published evidence

The GitHub release attaches:

- an SPDX SBOM;
- a machine-readable release-evidence JSON document containing the source
  commit, published image digest, immutable parent reference, conformance
  commit, and attestation references.

Provenance and SBOM attestations are attached to the published GHCR image.
They are separate evidence from pull-request CI and must be verified after a
release run completes.

## Historical recovery records

The manual recovery workflows below completed for the recorded releases. Their
instructions are historical; do not dispatch them as routine release steps.
In particular, rerunning the v0.4.0 recovery can move the GitHub `latest`
release marker and GHCR `0.4` and `latest` aliases backward from v0.4.1 to
v0.4.0. The workflows remain manually dispatchable; this documentation does
not prevent a dispatch.

### v0.4.0 recovery — historical

The immutable v0.4.0 image was published before its original release run
stopped at registry verification. The completed [recovery run](https://github.com/gehorak/runner-terraform/actions/runs/45441423791) validated the fixed
source commit and digest, checked the existing linux/amd64 image, ran derived
conformance and the vulnerability scan, and generated release evidence and
attestations. The workflow updates the GitHub Release and copies the image to
mutable aliases; it does not rebuild the immutable v0.4.0 image or move its tag.

### v0.4.1 recovery — historical

The immutable v0.4.1 image was published before its original release workflow
stopped at candidate-digest verification. The completed [recovery run](https://github.com/gehorak/runner-terraform/actions/runs/45448335646) validated the
fixed source commit and root image digest, performed the same evidence and
conformance steps, and updated `0.4` and `latest` to v0.4.1. It did not rebuild
or move the immutable v0.4.1 tag. Verify the current public release and
registry state before any future recovery operation.
