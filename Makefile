IMAGE_NAME ?= runner-terraform
IMAGE_TAG ?= dev
IMAGE := $(IMAGE_NAME):$(IMAGE_TAG)

BASE_IMAGE := ghcr.io/gehorak/runner-base:0.3.0@sha256:8e663302934d78f5edd77f7c07cf3f66813085f1922f5a27ad379a6ca6831003
RUNNER_CONFORMANCE_VERSION := v001
RUNNER_CONFORMANCE_REF := 4bd01b01ab063a4f3bd2ce8bd3748577beb9e71f
RUNNER_BASE_TAG := v0.3.0
CONFORMANCE_DIR := .cache/runner-base-conformance
TOOLS_LOCK := contracts/tools-lock/v001/tools.lock.json
DOMAIN_TEST := ci/test-domain.sh

.PHONY: help build lint domain-test conformance check clean

help:
	@printf '%s\n' \
	  'runner-terraform local targets:' \
	  '  make build        Build the derived image from the pinned parent.' \
	  '  make domain-test  Build and run only the Terraform domain contract.' \
	  '  make conformance  Build and run pinned runner-base conformance.' \
	  '  make check        Lint and run full conformance.' \
	  '  make clean        Remove local image and conformance checkout.'

build:
	docker build \
	  --build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
	  --tag "$(IMAGE)" \
	  .

lint:
	bash -n scripts/install-terraform.sh
	bash -n $(DOMAIN_TEST)
	python3 -m json.tool $(TOOLS_LOCK) >/dev/null

domain-test: build
	IMAGE="$(IMAGE)" \
	BASE_REFERENCE="$(BASE_IMAGE)" \
	RUNNER_CONFORMANCE_VERSION="$(RUNNER_CONFORMANCE_VERSION)" \
	bash $(DOMAIN_TEST)

conformance: build
	rm -rf "$(CONFORMANCE_DIR)"
	mkdir -p "$(dir $(CONFORMANCE_DIR))"
	git clone --depth 1 --branch "$(RUNNER_BASE_TAG)" \
	  https://github.com/gehorak/runner-base.git \
	  "$(CONFORMANCE_DIR)"
	test "$$(git -C "$(CONFORMANCE_DIR)" rev-parse HEAD)" = "$(RUNNER_CONFORMANCE_REF)"
	bash "$(CONFORMANCE_DIR)/ci/derived-conformance.sh" \
	  --image "$(IMAGE)" \
	  --base-reference "$(BASE_IMAGE)" \
	  --contract-version "$(RUNNER_CONFORMANCE_VERSION)" \
	  --tools-lock "$(TOOLS_LOCK)" \
	  --domain-test "$(DOMAIN_TEST)"

check: lint conformance

clean:
	docker image rm --force "$(IMAGE)" 2>/dev/null || true
	rm -rf "$(CONFORMANCE_DIR)"
