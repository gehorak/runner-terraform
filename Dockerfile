# syntax=docker/dockerfile:1

# runner-terraform is a strict derived image. The parent is a released immutable
# runner-base artifact; changing it requires an explicit reviewed PR and a full
# conformance run.
ARG BASE_IMAGE=ghcr.io/gehorak/runner-base:0.3.2@sha256:23ca54058c01e5362e89c2746f794b637584842df803992d8568f64d302a8cf0
FROM ${BASE_IMAGE}

ARG BASE_IMAGE
LABEL org.opencontainers.image.title="runner-terraform" \
      org.opencontainers.image.description="Deterministic Terraform runner derived from runner-base" \
      org.opencontainers.image.source="https://github.com/gehorak/runner-terraform" \
      org.opencontainers.image.base.name="${BASE_IMAGE}"

USER root

COPY image.manifest /tmp/runner-terraform.image.manifest
COPY contracts/tools-lock/v001/tools.lock.json /tmp/runner-terraform.tools.lock.json
COPY scripts/install-terraform.sh /tmp/runner-terraform.install-terraform.sh

RUN chmod 0755 /tmp/runner-terraform.install-terraform.sh \
 && /tmp/runner-terraform.install-terraform.sh /tmp/runner-terraform.tools.lock.json \
 && . /usr/local/lib/runner/metadata.sh \
 && runner_metadata_materialize_derived_manifest /tmp/runner-terraform.image.manifest \
 && rm -f \
      /tmp/runner-terraform.image.manifest \
      /tmp/runner-terraform.tools.lock.json \
      /tmp/runner-terraform.install-terraform.sh

# Re-assert the inherited runtime user after the root-only build layer.
# The entrypoint, command, and workdir remain inherited from runner-base.
USER runner
