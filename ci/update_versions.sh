#!/bin/bash
# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2025
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -o errexit
set -o pipefail
if [[ ${DEBUG:-false} == "true" ]]; then
    set -o xtrace
fi

trap "make fmt" EXIT

git fetch --tags origin
if ! command -v uv >/dev/null 2>&1; then
    uv_env="$(mktemp -d)"
    trap 'rm -rf "$uv_env"' EXIT
    python3 -m venv "$uv_env"
    "$uv_env/bin/python" -m pip install uv
    export PATH="$uv_env/bin:$PATH"
fi

uvx pre-commit autoupdate
uv run --no-project --with git+https://github.com/electrocucaracha/gh-updater.git gh-updater .
./ci/sync_skill_versions.py
