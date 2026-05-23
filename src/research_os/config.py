from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class HubError(ValueError):
    """Raised when a Research OS hub cannot be loaded."""


@dataclass(frozen=True)
class Hub:
    path: Path
    config: dict[str, Any]

    @property
    def projects_path(self) -> Path:
        return self.path / "registries" / "projects.yaml"

    @property
    def sources_path(self) -> Path:
        return self.path / "registries" / "sources.yaml"


def load_hub(path: Path) -> Hub:
    hub_path = path.expanduser().resolve()
    config_path = hub_path / "research-os.yaml"
    if not config_path.is_file():
        raise HubError(f"missing Research OS config: {config_path}")
    config = read_yaml_mapping(config_path)
    return Hub(path=hub_path, config=config)


def read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise HubError(f"invalid YAML in {path.relative_to(path.parent.parent)}: {error}") from error


def read_yaml_mapping(path: Path) -> dict[str, Any]:
    data = read_yaml(path)
    if not isinstance(data, dict):
        raise HubError(f"{path.name} must contain a mapping")
    return data


def read_yaml_list(path: Path, label: str) -> list[dict[str, Any]]:
    data = read_yaml(path)
    if data is None:
        return []
    if not isinstance(data, list):
        raise HubError(f"{label} must contain a list")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise HubError(f"{label} item {index} must contain a mapping")
    return data


def load_projects(hub: Hub) -> list[dict[str, Any]]:
    return read_yaml_list(hub.projects_path, "registries/projects.yaml")


def load_sources(hub: Hub) -> list[dict[str, Any]]:
    return read_yaml_list(hub.sources_path, "registries/sources.yaml")
