# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2025
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

DOCKER_CMD ?= $(shell which docker 2> /dev/null || which podman 2> /dev/null || echo docker)

.PHONY: cleanup
cleanup:
	rm -rf node_modules
	rm -rf .tox/ .venv/

.PHONY: fmt
fmt:
	command -v textlint > /dev/null && npm list --global --depth=0 textlint-rule-terminology > /dev/null 2>&1 || sudo npm install --global textlint textlint-rule-terminology
	textlint . --fix --ignore-path .gitignore
	command -v shfmt > /dev/null || curl -s "https://i.jpillora.com/mvdan/sh!!?as=shfmt" | bash
	git ls-files --cached --others --exclude-standard -z -- '*.sh' | xargs -0 shfmt -l -w -s -i 4
	command -v yamlfmt > /dev/null || curl -s "https://i.jpillora.com/google/yamlfmt!!" | bash
	yamlfmt -dstar -gitignore_excludes '**/*.{yaml,yml}'
	# Keep this aligned with the Prettier version pinned by Super-Linter.
	npx --yes prettier@3.9.8 . --write --ignore-path .gitignore --use-tabs false --prose-wrap preserve
	uvx ruff check --fix .
	uvx ruff format .

.PHONY: lint-python
lint-python:
	git ls-files --cached --others --exclude-standard -z -- '*.py' | xargs -0 uvx pylint --rcfile=.python-lint
