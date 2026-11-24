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
already present, recovery is allowed only when its linux/amd64 image
configuration digest matches the tested candidate. The registry inspector also
validates the root manifest digest and the selected platform manifest against
the OCI index descriptor. Version-minor and `latest` aliases are updated only
after the immutable image, attestations, and release evidence exist.

## Published evidence

The GitHub release attaches:

- an SPDX SBOM;
- a machine-readable release-evidence JSON document containing the source
  commit, published image digest, immutable parent reference, conformance
  commit, and attestation references.

Provenance and SBOM attestations are attached to the published GHCR image.
They are separate evidence from pull-request CI and must be verified after a
release run completes.

## Recovering the existing v0.4.0 image

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
