#!/bin/bash

set -o errexit
set -o pipefail
if [[ ${DEBUG:-false} == "true" ]]; then
    set -o xtrace
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

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
