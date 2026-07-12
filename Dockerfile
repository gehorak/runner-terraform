# syntax=docker/dockerfile:1

# runner-terraform is a strict derived image. The parent is a released immutable
# runner-base artifact; changing it requires an explicit reviewed PR and a full
# conformance run.
ARG BASE_IMAGE=ghcr.io/gehorak/runner-base:0.3.0@sha256:8e663302934d78f5edd77f7c07cf3f66813085f1922f5a27ad379a6ca6831003
FROM ${BASE_IMAGE}

ARG BASE_IMAGE
LABEL org.opencontainers.image.title="runner-terraform" \
      org.opencontainers.image.description="Deterministic Terraform runner derived from runner-base" \
      org.opencontainers.image.source="https://github.com/gehorak/runner-terraform" \
      org.opencontainers.image.base.name="${BASE_IMAGE}"

USER root

COPY image.manifest /tmp/runner-terraform.image.manifest
COPY contracts/tools-lock/v001/tools.lock.json /tmp/runner-terraform.tools.lock.json
COPY build/install-terraform.sh /usr/local/lib/runner-terraform/install-terraform.sh

RUN chmod 0755 /usr/local/lib/runner-terraform/install-terraform.sh \
 && /usr/local/lib/runner-terraform/install-terraform.sh /tmp/runner-terraform.tools-lock.json \
 && . /usr/local/lib/runner/metadata.sh \
 && runner_metadata_materialize_derived_manifest /tmp/runner-terraform.image.manifest \
 && rm -f \
      /tmp/runner-terraform.image.manifest \
      /tmp/runner-terraform.tools-lock.json \
      /usr/local/lib/runner-terraform/install-terraform.sh \
 && rmdir /usr/local/lib/runner-terraform

# Re-assert the inherited runtime context after the root-only build layer.
# The entrypoint and command remain inherited unchanged from runner-base.
USER runner
WORKDIR /workspace
