# =============================================================================
# Dockerfile — runner-terraform
#
# Terraform-specific runner image.
# Runtime is inherited READ-ONLY from runner-base.
# =============================================================================


# =============================================================================
# Base operating system
#
# NOTE:
# - Base OS is an implementation detail
# - NOT part of the runner contract
# =============================================================================

FROM ghcr.io/gehorak/runner-base:0.2.0

USER root

# =============================================================================
# Image manifest (single source of truth)
#
# The manifest defines:
# - image identity
# - runtime execution context
# - declared tooling (for derived images)
# =============================================================================

COPY image.manifest /tmp/image.manifest


# =============================================================================
# Manifest validation
#
# Fail early if the manifest schema is unsupported.
# =============================================================================

RUN grep -q '^MANIFEST_SCHEMA_VERSION=1$' /tmp/image.manifest \
 || (echo "ERROR: unsupported manifest schema version" >&2 && exit 1)


# =============================================================================
# Materialize runtime contract
#
# Runtime code MUST read only files under /etc/runner.
# The manifest itself MUST NOT be accessed at runtime.
# =============================================================================

RUN mkdir -p /etc/runner \
 && grep '^RUNNER_'  /tmp/image.manifest > /etc/runner/image.env \
 && grep '^TOOL_'    /tmp/image.manifest > /etc/runner/tools.env || true \
 && chmod 0444 /etc/runner/*.env


# =============================================================================
# TOOL: tf - Terraform
# =============================================================================
RUN set -Eeuo pipefail; \
    source /etc/runner/tools.env; \
    \
    : "${TOOL_TERRAFORM_VERSION:?Missing TOOL_TERRAFORM_VERSION}"; \
    : "${TOOL_TERRAFORM_SHA256:?Missing TOOL_TERRAFORM_SHA256}"; \
    \
    echo "==> Installing terraform ${TOOL_TERRAFORM_VERSION}"; \
    curl -fsSLo /tmp/terraform.zip \
      "https://releases.hashicorp.com/terraform/${TOOL_TERRAFORM_VERSION}/terraform_${TOOL_TERRAFORM_VERSION}_linux_amd64.zip"; \
    echo "${TOOL_TERRAFORM_SHA256}  /tmp/terraform.zip" | sha256sum -c -; \
    unzip /tmp/terraform.zip -d /usr/local/bin; \
    rm -f /tmp/terraform.zip




# =============================================================================
# Runtime execution context (INHERITED FROM runner-base)
#
# NOTE:
# - Runtime user, UID/GID, HOME and WORKDIR are defined in runner-base
# - This image MUST NOT modify runtime execution context
# - Values are applied here only to make inheritance explicit
# =============================================================================


# =============================================================================
# Runner plugins
# =============================================================================
COPY runner.d/ /usr/local/lib/runner.d/
RUN chmod +x /usr/local/lib/runner.d/* \
  && chown -R 10001:10001 /usr/local/lib/runner.d/
#&& chown -R ${RUNTIME_USER_UID}:${RUNTIME_USER_GID} /usr/local/lib/runner.d/


# =============================================================================
# Set runtime user and working directory
# =============================================================================
#USER ${RUNTIME_USER_NAME}
#WORKDIR ${RUNTIME_WORKDIR}
USER runner
WORKDIR /workspace

# =============================================================================
# Entrypoint (platform contract)
#
# MUST NOT be overridden by derived images.
# =============================================================================

#ENTRYPOINT ["/usr/local/bin/runner"]
#CMD ["help"]


# =============================================================================
# End of Dockerfile
#
# Status: CANONICAL
#
# This file defines platform behavior only.
# Domain-specific concerns belong in derived images.
# =============================================================================
