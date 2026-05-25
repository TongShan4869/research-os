from __future__ import annotations

from pathlib import Path

from research_os.config import Hub


def obsidian_vault_path(hub: Hub) -> Path:
    configured = hub.config.get("paths", {}).get("obsidian_vault")
    if isinstance(configured, str) and configured:
        path = Path(configured).expanduser()
        return path if path.is_absolute() else hub.path / path
    return hub.path / "obsidian" / "starter-vault"
