#!/usr/bin/env -S uv --quiet run --script
# Copyright (c) 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Synchronize marketplace and plugin versions with stable Git release tags."""

# /// script
# requires-python = ">=3.12"
# dependencies = ["semver>=3.0.0,<4"]
# ///

import json
import subprocess
from pathlib import Path
from typing import Any

from semver import Version


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a JSON object only when its parsed content has changed."""
    if json.loads(path.read_text(encoding="utf-8")) != data:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sync_versions(root: Path) -> None:
    """Synchronize catalog and plugin versions in the repository at root.

    Consider only stable SemVer tags with an optional ``v`` prefix,
    excluding prerelease and build metadata.

    Raises:
        SystemExit: If no stable release tags exist or a plugin source
            resolves outside the repository.

    """
    root = root.resolve()
    tags = subprocess.check_output(
        ["git", "tag", "--list"], cwd=root, text=True
    ).splitlines()
    versions: list[Version] = []
    for tag in tags:
        try:
            parsed = Version.parse(tag.removeprefix("v"))
        except ValueError:
            continue
        if parsed.prerelease is None and parsed.build is None:
            versions.append(parsed)
    if not versions:
        raise SystemExit("No stable release tags found; run git fetch --tags origin.")

    version = str(max(versions))
    catalog_path = root / ".github" / "plugin" / "marketplace.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for plugin in catalog["plugins"]:
        manifest_path = (root / plugin["source"] / "plugin.json").resolve()
        if not manifest_path.is_relative_to(root):
            raise SystemExit(f"Plugin source escapes repository: {plugin['source']}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = version
        write_json(manifest_path, manifest)
        plugin["version"] = version
    catalog["metadata"]["version"] = version
    write_json(catalog_path, catalog)
    print(f"Plugin versions synchronized to {version}")


def main() -> None:
    """Synchronize versions for the repository containing this script."""
    sync_versions(Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    main()
