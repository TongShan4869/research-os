from __future__ import annotations

from pathlib import Path

from research_os.config import Hub


DEFAULT_OBSIDIAN_VAULT = Path("obsidian") / "research-os"
LEGACY_OBSIDIAN_VAULT = Path("obsidian") / "starter-vault"


def obsidian_vault_path(hub: Hub) -> Path:
    configured = hub.config.get("paths", {}).get("obsidian_vault")
    if isinstance(configured, str) and configured:
        path = Path(configured).expanduser()
        return path if path.is_absolute() else hub.path / path
    default_path = hub.path / DEFAULT_OBSIDIAN_VAULT
    legacy_path = hub.path / LEGACY_OBSIDIAN_VAULT
    if legacy_path.exists() and not default_path.exists():
        return legacy_path
    return default_path
