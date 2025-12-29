"""Files plugin - File search and launcher."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str = "files"
    version: str = "0.1.0"
    description: str = "Search and open files"
    api_version: str = "1"


@dataclass
class FilesConfig:
    """Configuration for the files plugin."""

    # Directories to scan (~ is expanded)
    scan_paths: list[str] = field(
        default_factory=lambda: ["~/Documents", "~/Downloads", "~/Projects"]
    )
    # Maximum depth to scan (-1 for unlimited)
    max_depth: int = 5
    # File extensions to include (empty = all)
    include_extensions: list[str] = field(default_factory=list)
    # Patterns to exclude
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            ".cache",
        ]
    )
    # Maximum files to index
    max_files: int = 10000


class FilesPlugin:
    """Plugin for searching and opening files."""

    def __init__(self) -> None:
        self._config: FilesConfig | None = None

    @property
    def info(self) -> PluginInfo:
        return PluginInfo()

    def setup(self, ctx: object) -> None:
        """Load configuration from plugin data."""
        self._config = self._load_config(ctx)

    def teardown(self, ctx: object) -> None:
        """Called when plugin is unloaded."""
        pass

    def _load_config(self, ctx: object) -> FilesConfig:
        """Load config from plugin data storage."""
        data = ctx.get_data("config")  # type: ignore[attr-defined]
        if data is None:
            return FilesConfig()

        return FilesConfig(
            scan_paths=data.get("scan_paths", FilesConfig.scan_paths),
            max_depth=data.get("max_depth", FilesConfig.max_depth),
            include_extensions=data.get(
                "include_extensions", FilesConfig.include_extensions
            ),
            exclude_patterns=data.get("exclude_patterns", FilesConfig.exclude_patterns),
            max_files=data.get("max_files", FilesConfig.max_files),
        )

    def _save_config(self, ctx: object) -> None:
        """Save config to plugin data storage."""
        if self._config is None:
            return

        ctx.set_data(  # type: ignore[attr-defined]
            "config",
            {
                "scan_paths": self._config.scan_paths,
                "max_depth": self._config.max_depth,
                "include_extensions": self._config.include_extensions,
                "exclude_patterns": self._config.exclude_patterns,
                "max_files": self._config.max_files,
            },
        )

    def run(self, ctx: object, action: str = "") -> None:
        """Called when user selects this plugin or a file."""
        if action == "settings":
            self._show_settings(ctx)
            return

        if action:
            # Action is a file path, open it
            self._open_file(action)
            return

        # Show files menu
        self._show_files_menu(ctx)

    def _show_files_menu(self, ctx: object) -> None:
        """Show the main files menu."""
        from menu_kit.core.database import ItemType, MenuItem

        while True:
            items = self._get_file_items()

            # Add settings at the end
            items.append(
                MenuItem(
                    id="files:settings",
                    title="Settings",
                    item_type=ItemType.SUBMENU,
                    plugin="files",
                )
            )

            selected = ctx.menu(items, prompt="Files")  # type: ignore[attr-defined]

            if selected is None:
                return

            if selected.id == "files:settings":
                self._show_settings(ctx)
            elif selected.metadata and "path" in selected.metadata:
                self._open_file(selected.metadata["path"])
                return  # Exit after opening a file

    def _show_settings(self, ctx: object) -> None:
        """Show settings menu."""
        from menu_kit.core.database import ItemType, MenuItem

        if self._config is None:
            self._config = FilesConfig()

        while True:
            items = [
                MenuItem(
                    id="files:settings:paths",
                    title="Scan Paths",
                    item_type=ItemType.SUBMENU,
                    badge=str(len(self._config.scan_paths)),
                ),
                MenuItem(
                    id="files:settings:depth",
                    title="Max Depth",
                    item_type=ItemType.ACTION,
                    badge=str(self._config.max_depth),
                ),
                MenuItem(
                    id="files:settings:rescan",
                    title="Rescan Files",
                    item_type=ItemType.ACTION,
                ),
            ]

            selected = ctx.menu(items, prompt="Files Settings")  # type: ignore[attr-defined]

            if selected is None:
                return

            if selected.id == "files:settings:paths":
                self._edit_paths(ctx)
            elif selected.id == "files:settings:depth":
                ctx.notify(f"Max depth: {self._config.max_depth}")  # type: ignore[attr-defined]
            elif selected.id == "files:settings:rescan":
                ctx.notify("Rescan not yet implemented")  # type: ignore[attr-defined]

    def _edit_paths(self, ctx: object) -> None:
        """Edit scan paths."""
        from menu_kit.core.database import ItemType, MenuItem

        if self._config is None:
            return

        while True:
            items = []

            for path in self._config.scan_paths:
                expanded = str(Path(path).expanduser())
                exists = Path(expanded).exists()
                badge = None if exists else "not found"

                items.append(
                    MenuItem(
                        id=f"files:path:{path}",
                        title=path,
                        item_type=ItemType.ACTION,
                        badge=badge,
                    )
                )

            items.append(
                MenuItem(
                    id="files:path:add",
                    title="Add Path...",
                    item_type=ItemType.ACTION,
                )
            )

            selected = ctx.menu(items, prompt="Scan Paths")  # type: ignore[attr-defined]

            if selected is None:
                return

            if selected.id == "files:path:add":
                ctx.notify("Add path not yet implemented")  # type: ignore[attr-defined]
            else:
                # Show path options (remove, etc.)
                path = selected.id.replace("files:path:", "")
                ctx.notify(f"Path: {path}")  # type: ignore[attr-defined]

    def _open_file(self, path: str) -> None:
        """Open a file with xdg-open."""
        try:
            subprocess.Popen(
                ["xdg-open", path],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def index(self, ctx: object) -> list:
        """Return submenu entry for main menu."""
        from menu_kit.core.database import ItemType, MenuItem

        return [
            MenuItem(
                id="files",
                title="Files",
                item_type=ItemType.SUBMENU,
                plugin="files",
            )
        ]

    def _get_file_items(self) -> list:
        """Get menu items for files."""
        from menu_kit.core.database import ItemType, MenuItem

        if self._config is None:
            self._config = FilesConfig()

        items: list[MenuItem] = []
        files = self._scan_files()

        for file_path in files:
            path = Path(file_path)

            item = MenuItem(
                id=f"files:{file_path}",
                title=path.name,
                item_type=ItemType.ACTION,
                plugin="files",
                badge=str(path.parent).replace(str(Path.home()), "~"),
                metadata={"path": file_path},
            )
            items.append(item)

        return items

    def _scan_files(self) -> list[str]:
        """Scan configured directories for files."""
        if self._config is None:
            return []

        # Try fd first (faster), fall back to find
        if self._has_fd():
            return self._scan_with_fd()
        else:
            return self._scan_with_python()

    def _has_fd(self) -> bool:
        """Check if fd is available."""
        return shutil.which("fd") is not None

    def _scan_with_fd(self) -> list[str]:
        """Scan files using fd."""
        if self._config is None:
            return []

        all_files: list[str] = []

        for scan_path in self._config.scan_paths:
            path = Path(scan_path).expanduser()
            if not path.exists():
                continue

            cmd = ["fd", "--type", "f", "--absolute-path"]

            # Max depth
            if self._config.max_depth > 0:
                cmd.extend(["--max-depth", str(self._config.max_depth)])

            # Exclusions
            for pattern in self._config.exclude_patterns:
                cmd.extend(["--exclude", pattern])

            # Extensions filter
            if self._config.include_extensions:
                for ext in self._config.include_extensions:
                    cmd.extend(["--extension", ext.lstrip(".")])

            cmd.append(str(path))

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split("\n")
                    all_files.extend(f for f in files if f)
            except (subprocess.TimeoutExpired, Exception):
                continue

            # Check limit
            if len(all_files) >= self._config.max_files:
                all_files = all_files[: self._config.max_files]
                break

        return all_files

    def _scan_with_python(self) -> list[str]:
        """Scan files using Python (fallback)."""
        if self._config is None:
            return []

        all_files: list[str] = []

        for scan_path in self._config.scan_paths:
            path = Path(scan_path).expanduser()
            if not path.exists():
                continue

            try:
                for root, dirs, files in os.walk(path):
                    # Check depth
                    depth = str(root).count(os.sep) - str(path).count(os.sep)
                    if self._config.max_depth > 0 and depth >= self._config.max_depth:
                        dirs.clear()
                        continue

                    # Filter excluded directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if d not in self._config.exclude_patterns
                        and not d.startswith(".")
                    ]

                    for filename in files:
                        if filename.startswith("."):
                            continue

                        # Extension filter
                        if self._config.include_extensions:
                            ext = Path(filename).suffix.lstrip(".")
                            if ext not in self._config.include_extensions:
                                continue

                        all_files.append(os.path.join(root, filename))

                        if len(all_files) >= self._config.max_files:
                            return all_files
            except PermissionError:
                continue

        return all_files


def create_plugin() -> FilesPlugin:
    """Factory function to create the plugin."""
    return FilesPlugin()
