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
