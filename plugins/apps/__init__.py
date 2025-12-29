"""Apps plugin - Application launcher from .desktop files."""

from __future__ import annotations

import os
import shlex
import subprocess
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PluginInfo:
    """Plugin metadata."""

    name: str = "apps"
    version: str = "0.1.0"
    description: str = "Application launcher from .desktop files"
    api_version: str = "1"


@dataclass
class DesktopEntry:
    """Parsed .desktop file entry."""

    name: str
    exec_cmd: str
    icon: str | None = None
    comment: str | None = None
    terminal: bool = False
    path: str | None = None


class AppsPlugin:
    """Plugin for launching applications from .desktop files."""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo()

    def setup(self, ctx: object) -> None:
        """Called once when plugin is loaded."""
        pass

    def teardown(self, ctx: object) -> None:
        """Called when plugin is unloaded."""
        pass

    def run(self, ctx: object, action: str = "") -> None:
        """Called when user selects this plugin or an app."""
        if action:
            # Action is the app ID, launch it
            self._launch_app(ctx, action)
            return

        # Show apps menu
        items = self.index(ctx)
        selected = ctx.menu(items, prompt="Applications")  # type: ignore[attr-defined]

        if selected is None:
            return

        # Launch the selected app
        if selected.metadata and "exec" in selected.metadata:
            self._execute(
                selected.metadata["exec"], selected.metadata.get("terminal", False)
            )

    def _launch_app(self, ctx: object, app_id: str) -> None:
        """Launch an app by ID."""
        # Reconstruct full ID if needed (runner passes action part only)
        full_id = f"apps:{app_id}" if not app_id.startswith("apps:") else app_id
        item = ctx.database.get_item(full_id)  # type: ignore[attr-defined]
        if item is None or item.metadata is None:
            return

        exec_cmd = item.metadata.get("exec", "")
        terminal = item.metadata.get("terminal", False)

        if exec_cmd:
            self._execute(exec_cmd, terminal)

    def _execute(self, exec_cmd: str, terminal: bool = False) -> None:
        """Execute a command."""
        # Remove field codes from exec command
        cmd = self._clean_exec(exec_cmd)

        try:
            if terminal:
                # Try common terminal emulators
                terminals = ["kitty", "alacritty", "gnome-terminal", "xterm"]
                for term in terminals:
                    if self._command_exists(term):
                        subprocess.Popen([term, "-e", cmd], start_new_session=True)
                        return
                # Fallback: just run it
                subprocess.Popen(shlex.split(cmd), start_new_session=True)
            else:
                subprocess.Popen(shlex.split(cmd), start_new_session=True)
        except Exception:
            pass  # Silently fail for now

    def _clean_exec(self, exec_cmd: str) -> str:
        """Remove field codes (%f, %F, %u, %U, etc.) from exec command."""
        import re

        return re.sub(r"%[fFuUdDnNickvm]", "", exec_cmd).strip()

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        import shutil

        return shutil.which(cmd) is not None

    def index(self, ctx: object) -> list:
        """Return items to add to main menu."""
        from menu_kit.core.database import ItemType, MenuItem

        items: list[MenuItem] = []
        seen_names: set[str] = set()

        # Scan .desktop files
        for entry in self._scan_desktop_files():
            if entry.name in seen_names:
                continue
            seen_names.add(entry.name)

            item = MenuItem(
                id=f"apps:{entry.name.lower().replace(' ', '_')}",
                title=entry.name,
                item_type=ItemType.ACTION,
                plugin="apps",
                icon=entry.icon,
                metadata={
                    "exec": entry.exec_cmd,
                    "terminal": entry.terminal,
                    "comment": entry.comment,
                },
            )
            items.append(item)

        # Sort by name
        items.sort(key=lambda x: x.title.lower())

        return items

    def _scan_desktop_files(self) -> list[DesktopEntry]:
        """Scan for .desktop files."""
        entries: list[DesktopEntry] = []

        # XDG application directories
        dirs = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local" / "share" / "applications",
        ]

        # Add XDG_DATA_DIRS
        xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "").split(":")
        for d in xdg_data_dirs:
            if d:
                dirs.append(Path(d) / "applications")

        for app_dir in dirs:
            if not app_dir.exists():
                continue

            for desktop_file in app_dir.glob("*.desktop"):
                entry = self._parse_desktop_file(desktop_file)
                if entry:
                    entries.append(entry)

        return entries

    def _parse_desktop_file(self, path: Path) -> DesktopEntry | None:
        """Parse a .desktop file."""
        try:
            parser = ConfigParser(interpolation=None)
            parser.read(path, encoding="utf-8")

            if "Desktop Entry" not in parser:
                return None

            section = parser["Desktop Entry"]

            # Skip if NoDisplay or Hidden
            if section.get("NoDisplay", "false").lower() == "true":
                return None
            if section.get("Hidden", "false").lower() == "true":
                return None

            name = section.get("Name")
            exec_cmd = section.get("Exec")

            if not name or not exec_cmd:
                return None

            return DesktopEntry(
                name=name,
                exec_cmd=exec_cmd,
                icon=section.get("Icon"),
                comment=section.get("Comment"),
                terminal=section.get("Terminal", "false").lower() == "true",
                path=str(path),
            )
        except Exception:
            return None


def create_plugin() -> AppsPlugin:
    """Factory function to create the plugin."""
    return AppsPlugin()
