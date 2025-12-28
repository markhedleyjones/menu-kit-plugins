#!/usr/bin/env python3
"""Build index.json from plugin manifests."""

from __future__ import annotations

import hashlib
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path


def compute_checksum(directory: Path) -> str:
    """Compute SHA256 checksum of a plugin directory."""
    sha256 = hashlib.sha256()

    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file():
            sha256.update(file_path.read_bytes())

    return sha256.hexdigest()


def build_index(plugins_dir: Path) -> dict:
    """Build the plugin index from manifest files."""
    index = {
        "version": 1,
        "generated": datetime.now(timezone.utc).isoformat(),
        "plugins": {},
    }

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue

        manifest_path = plugin_dir / "manifest.toml"
        if not manifest_path.exists():
            print(f"Warning: No manifest.toml in {plugin_dir.name}, skipping")
            continue

        with manifest_path.open("rb") as f:
            manifest = tomllib.load(f)

        plugin_info = manifest.get("plugin", {})
        name = plugin_info.get("name", plugin_dir.name)

        index["plugins"][name] = {
            "version": plugin_info.get("version", "0.0.0"),
            "description": plugin_info.get("description", ""),
            "api_version": plugin_info.get("api_version", "1"),
            "author": plugin_info.get("author", ""),
            "download": f"plugins/{plugin_dir.name}",
            "sha256": compute_checksum(plugin_dir),
            "dependencies": manifest.get("plugin", {}).get("dependencies", {}),
            "verified": True,  # Official repo plugins are verified
        }

    return index


def main() -> None:
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    plugins_dir = repo_root / "plugins"
    index_path = repo_root / "index.json"

    if not plugins_dir.exists():
        print(f"Error: {plugins_dir} does not exist")
        return

    index = build_index(plugins_dir)

    with index_path.open("w") as f:
        json.dump(index, f, indent=2)
        f.write("\n")

    print(f"Generated {index_path}")
    print(f"Plugins: {list(index['plugins'].keys())}")


if __name__ == "__main__":
    main()
