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

## Recovering already-published images

The immutable `v0.4.0` GHCR image was published before its original release run
stopped at registry verification. After the recovery workflow is merged, run
**Recover v0.4.0 release evidence** from the `main` branch in GitHub Actions.
The workflow is manual and fixed to the recorded `v0.4.0` source commit and
image digest. It checks those pins, validates the existing `linux/amd64` image,
runs derived conformance and the vulnerability scan, generates an SPDX SBOM,
and creates provenance/SBOM attestations and release evidence for that image.

The recovery workflow creates or updates the GitHub Release and its evidence
assets before copying the exact existing image index to the `0.4` and `latest`
aliases. It does not build or push another `0.4.0` image and does not create,
move, or delete a Git tag. Alias digests are checked against the pinned image
digest after each copy.

The immutable `v0.4.1` image was also published before its release workflow
stopped at candidate-digest verification. After the recovery workflow is
merged, run **Recover v0.4.1 release evidence** from `main`. It is fixed to the
recorded `v0.4.1` source commit and root image digest, performs the same
validation and evidence steps, and then updates `0.4` and `latest` to v0.4.1.
It does not rebuild or move the immutable `v0.4.1` tag.
