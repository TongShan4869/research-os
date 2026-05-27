from __future__ import annotations

from dataclasses import dataclass

from research_os.config import Hub, HubError, load_files, load_inbox, load_projects, load_relations, load_sources


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
    "obsidian/starter-vault/index.md",
    "obsidian/starter-vault/log.md",
    "obsidian/starter-vault/wiki/inbox.md",
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
    "obsidian/starter-vault/Synthesis",
    "obsidian/starter-vault/Entities",
    "obsidian/starter-vault/Claims",
    "obsidian/starter-vault/Methods",
    "obsidian/starter-vault/Datasets",
    "obsidian/starter-vault/Results",
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

    if not isinstance(hub.config.get("version"), int):
        errors.append("research-os.yaml must contain integer field: version")

    errors.extend(validate_registries(hub))
    return ValidationResult(errors=errors)


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
