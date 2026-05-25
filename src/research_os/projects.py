from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from research_os.config import Hub, HubError, load_hub, load_projects, read_yaml_mapping


MARKER_NAME = ".research-os-project.yaml"


@dataclass(frozen=True)
class ProjectResolution:
    project_id: str
    resolution: str
    workspace: Path | None = None
    folder_kind: str | None = None
    matched_path: Path | None = None


def create_project(hub: Hub, project_id: str, title: str) -> dict[str, Any]:
    projects = load_projects(hub)
    if find_project(projects, project_id) is not None:
        raise HubError(f"project already exists: {project_id}")

    project = {
        "id": project_id,
        "title": title,
        "status": "active",
        "obsidian_note": f"Projects/{project_id}.md",
        "folders": {},
        "zotero_collections": [],
        "tags": [],
        "created": date.today().isoformat(),
    }
    projects.append(project)
    save_projects(hub, projects)
    write_project_note(hub, project)
    return project


def attach_folder(hub: Hub, project_id: str, folder: Path, kind: str) -> None:
    projects = load_projects(hub)
    project = find_project(projects, project_id)
    if project is None:
        raise HubError(f"unknown project: {project_id}")

    resolved_folder = folder.expanduser().resolve()
    resolved_folder.mkdir(parents=True, exist_ok=True)
    folders = project.setdefault("folders", {})
    if not isinstance(folders, dict):
        raise HubError(f"project {project_id} field folders must contain a mapping")
    folders[kind] = str(resolved_folder)
    save_projects(hub, projects)
    write_marker(hub, project_id, resolved_folder, kind)


def resolve_project(path: Path, hub: Hub | None = None) -> ProjectResolution:
    target = path.expanduser().resolve()
    marker = find_marker(target)
    if marker is not None:
        data = read_yaml_mapping(marker)
        project_id = data.get("project_id")
        if not isinstance(project_id, str) or not project_id:
            raise HubError(f"{marker} missing required field: project_id")
        workspace = data.get("workspace")
        folder_kind = data.get("folder_kind")
        return ProjectResolution(
            project_id=project_id,
            resolution="marker",
            workspace=Path(workspace).expanduser().resolve() if isinstance(workspace, str) else None,
            folder_kind=folder_kind if isinstance(folder_kind, str) else None,
            matched_path=marker.parent,
        )

    if hub is None:
        raise HubError("project unresolved: no marker found and no --hub provided for registry path lookup")

    projects = load_projects(hub)
    for project in projects:
        project_id = project.get("id")
        folders = project.get("folders", {})
        if not isinstance(project_id, str) or not isinstance(folders, dict):
            continue
        for kind, folder_value in folders.items():
            if not isinstance(kind, str) or not isinstance(folder_value, str):
                continue
            folder_path = Path(folder_value).expanduser().resolve()
            if is_relative_to(target, folder_path):
                return ProjectResolution(
                    project_id=project_id,
                    resolution="registry-path",
                    workspace=hub.path,
                    folder_kind=kind,
                    matched_path=folder_path,
                )

    raise HubError(f"project unresolved: {target}")


def load_optional_hub(path: Path | None) -> Hub | None:
    if path is None:
        return None
    return load_hub(path)


def find_project(projects: list[dict[str, Any]], project_id: str) -> dict[str, Any] | None:
    for project in projects:
        if project.get("id") == project_id:
            return project
    return None


def save_projects(hub: Hub, projects: list[dict[str, Any]]) -> None:
    hub.projects_path.write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")


def write_project_note(hub: Hub, project: dict[str, Any]) -> None:
    note_path_value = project.get("obsidian_note")
    if not isinstance(note_path_value, str):
        return
    note_path = hub.path / "obsidian" / "starter-vault" / note_path_value
    if note_path.exists():
        return
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(
        "\n".join(
            [
                "---",
                "type: project",
                f"project_id: {project['id']}",
                f"status: {project['status']}",
                "tags:",
                *[f"  - {tag}" for tag in project_note_tags(project)],
                "---",
                "",
                f"# {project['title']}",
                "",
                "## Current State",
                "",
                "## Decisions",
                "",
                "## Next Actions",
                "",
            ]
        ),
        encoding="utf-8",
    )


def project_note_tags(project: dict[str, Any]) -> list[str]:
    project_id = project.get("id")
    status = project.get("status", "active")
    tags = ["research-os/project"]
    if isinstance(project_id, str) and project_id:
        tags.append(f"project/{project_id}")
    if isinstance(status, str) and status:
        tags.append(f"status/{status}")
    for tag in project.get("tags", []):
        if isinstance(tag, str) and tag:
            tags.append(topic_tag(tag))
    return dedupe(tags)


def topic_tag(tag: str) -> str:
    return tag if "/" in tag else f"topic/{tag}"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def write_marker(hub: Hub, project_id: str, folder: Path, kind: str) -> None:
    marker = {
        "workspace": str(hub.path),
        "project_id": project_id,
        "folder_kind": kind,
    }
    (folder / MARKER_NAME).write_text(yaml.safe_dump(marker, sort_keys=False), encoding="utf-8")


def find_marker(path: Path) -> Path | None:
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        marker = candidate / MARKER_NAME
        if marker.is_file():
            return marker
    return None


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True
