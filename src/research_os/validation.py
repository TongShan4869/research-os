from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research_os.config import Hub, HubError, load_files, load_inbox, load_projects, load_relations, load_sources
from research_os.paths import obsidian_vault_path


REQUIRED_FILES = [
    "research-os.yaml",
    "AGENTS.md",
    "GETTING_STARTED.md",
    "workflows/onboard.md",
    "registries/projects.yaml",
    "registries/sources.yaml",
    "registries/files.yaml",
    "registries/relations.yaml",
    "registries/inbox.yaml",
    "schemas/project.schema.yaml",
    "schemas/graph.schema.yaml",
    "schemas/note-types.yaml",
    "graph/graph.json",
]

REQUIRED_DIRS = [
    "workflows",
    "registries",
    "schemas",
    "graph",
    "obsidian/templates",
]

REQUIRED_VAULT_FILES = [
    "index.md",
    "log.md",
    "wiki/inbox.md",
]

REQUIRED_VAULT_DIRS = [
    "Synthesis",
    "Entities",
    "Claims",
    "Methods",
    "Datasets",
    "Results",
]


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_hub(hub: Hub) -> ValidationResult:
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (hub.path / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    for relative_path in REQUIRED_DIRS:
        if not (hub.path / relative_path).is_dir():
            errors.append(f"missing required directory: {relative_path}")

    vault = obsidian_vault_path(hub)
    for relative_path in REQUIRED_VAULT_FILES:
        path = vault / relative_path
        if not path.is_file():
            errors.append(f"missing required file: {display_path(path, hub)}")

    for relative_path in REQUIRED_VAULT_DIRS:
        path = vault / relative_path
        if not path.is_dir():
            errors.append(f"missing required directory: {display_path(path, hub)}")

    if not isinstance(hub.config.get("version"), int):
        errors.append("research-os.yaml must contain integer field: version")

    errors.extend(validate_registries(hub))
    return ValidationResult(errors=errors)


def display_path(path: Path, hub: Hub) -> str:
    try:
        return path.relative_to(hub.path).as_posix()
    except ValueError:
        return path.as_posix()


def validate_registries(hub: Hub) -> list[str]:
    errors: list[str] = []
    try:
        projects = load_projects(hub)
    except HubError as error:
        errors.append(str(error))
    else:
        for project in projects:
            project_id = project.get("id")
            if not isinstance(project_id, str) or not project_id:
                errors.append("project entry missing required string field: id")
            title = project.get("title")
            if not isinstance(title, str) or not title:
                errors.append(f"project {project_id or '<unknown>'} missing required string field: title")

    try:
        load_sources(hub)
    except HubError as error:
        errors.append(str(error))

    for loader in (load_files, load_relations, load_inbox):
        try:
            loader(hub)
        except HubError as error:
            errors.append(str(error))

    return errors
