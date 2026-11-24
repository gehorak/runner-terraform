IMAGE_NAME ?= runner-terraform
IMAGE_TAG ?= dev
IMAGE := $(IMAGE_NAME):$(IMAGE_TAG)

BASE_IMAGE := ghcr.io/gehorak/runner-base:0.3.3@sha256:5fdcd758ef973fbab502858a91d3b362fa7a7cb621d911a7fc972625e546a3c2
RUNNER_CONFORMANCE_VERSION := v001
RUNNER_CONFORMANCE_REF := 94b070419c6ce4a4e17d7639cff61a4fd1adbc63
RUNNER_BASE_TAG := v0.3.3
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
	bash ci/lint-shell.sh
	python3 ci/test-dockerfile-structure.py
	python3 ci/test-ci-quality.py
	python3 ci/test-source-contract.py
	python3 ci/test-release-workflow.py
	python3 ci/test-release-support.py
	python3 ci/test-published-security-scan.py
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
