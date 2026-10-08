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
already present, recovery is allowed only when its configuration digest equals
the tested candidate. Version-minor and `latest` aliases are updated only after
the immutable image, attestations, and release evidence exist.

## Published evidence

The GitHub release attaches:

- an SPDX SBOM;
- a machine-readable release-evidence JSON document containing the source
  commit, published image digest, immutable parent reference, conformance
  commit, and attestation references.

Provenance and SBOM attestations are attached to the published GHCR image.
They are separate evidence from pull-request CI and must be verified after a
release run completes.
