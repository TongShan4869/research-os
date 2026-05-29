from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from research_os.config import Hub, HubError, load_files, load_inbox, load_projects


IGNORED_DIRS = {".git", ".obsidian", "__pycache__", ".pytest_cache", "visual"}
EXTENSION_LABELS = {
    ".csv": "tabular data",
    ".tsv": "tabular data",
    ".xlsx": "spreadsheets",
    ".json": "JSON data",
    ".mat": "MATLAB data",
    ".set": "EEG datasets",
    ".fdt": "EEG binary data",
    ".vhdr": "BrainVision EEG headers",
    ".eeg": "EEG data",
    ".wav": "audio stimuli",
    ".mp3": "audio stimuli",
    ".png": "figures",
    ".jpg": "figures",
    ".jpeg": "figures",
    ".svg": "figures",
    ".tif": "figures",
    ".tiff": "figures",
    ".py": "Python code",
    ".r": "R code",
    ".m": "MATLAB code",
    ".ipynb": "notebooks",
    ".md": "notes",
    ".txt": "text notes",
    ".pdf": "PDF documents",
    ".docx": "manuscripts",
    ".tex": "LaTeX manuscripts",
}


def scan_hub(
    hub: Hub,
    ignore_names: list[str] | None = None,
    max_files: int | None = None,
    status: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ignored = IGNORED_DIRS | {name for name in (ignore_names or []) if name}
    existing_paths = {file_entry.get("path") for file_entry in load_files(hub)}
    existing_paths |= {proposal.get("path") for proposal in load_inbox(hub)}
    proposals: list[dict[str, Any]] = []
    scanned_files = 0
    for project in load_projects(hub):
        project_id = project.get("id")
        folders = project.get("folders")
        if not isinstance(project_id, str) or not project_id or not isinstance(folders, dict):
            continue
        for folder_value in folders.values():
            if not isinstance(folder_value, str) or not folder_value.strip():
                continue
            folder = resolve_hub_path(hub, folder_value)
            if not folder.is_dir():
                continue
            for path in sorted(folder.rglob("*")):
                if should_skip_path(path, ignored):
                    continue
                if max_files is not None and scanned_files >= max_files:
                    if status is not None:
                        status["stopped_early"] = True
                        status["max_files"] = max_files
                    return proposals
                scanned_files += 1
                relative_path = path.relative_to(hub.path).as_posix() if path.is_relative_to(hub.path) else str(path)
                if relative_path in existing_paths:
                    continue
                proposal = proposal_for_path(relative_path, project_id)
                if proposal is not None:
                    proposals.append(proposal)
                    existing_paths.add(relative_path)
    return proposals


def apply_scan(hub: Hub, proposals: list[dict[str, Any]]) -> Path:
    inbox = load_inbox(hub)
    known_ids = {proposal.get("id") for proposal in inbox}
    for proposal in proposals:
        if proposal.get("id") not in known_ids:
            inbox.append(proposal)
    hub.inbox_path.write_text(yaml.safe_dump(inbox, sort_keys=False), encoding="utf-8")
    return hub.inbox_path


def index_folder_surfaces(
    hub: Hub,
    max_depth: int = 2,
    ignore_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    ignored = IGNORED_DIRS | {name for name in (ignore_names or []) if name}
    files = load_files(hub)
    by_id = {file_entry.get("id"): index for index, file_entry in enumerate(files)}
    surfaces: list[dict[str, Any]] = []
    for project in load_projects(hub):
        project_id = string_value(project.get("id"))
        folders = project.get("folders")
        if project_id is None or not isinstance(folders, dict):
            continue
        for root_kind, folder_value in sorted(folders.items()):
            if not isinstance(root_kind, str) or not isinstance(folder_value, str) or not folder_value.strip():
                continue
            root = resolve_hub_path(hub, folder_value)
            if not root.is_dir():
                continue
            for folder in iter_surface_folders(root, ignored, max_depth):
                entry = folder_surface_entry(hub, project_id, root_kind, root, folder, ignored)
                surfaces.append(entry)
                existing_index = by_id.get(entry["id"])
                if existing_index is None:
                    by_id[entry["id"]] = len(files)
                    files.append(entry)
                else:
                    files[existing_index] = merge_folder_surface(files[existing_index], entry)
    hub.files_path.write_text(yaml.safe_dump(files, sort_keys=False), encoding="utf-8")
    return surfaces


def iter_surface_folders(root: Path, ignored: set[str], max_depth: int) -> list[Path]:
    folders: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_dir() or should_skip_directory(path, ignored):
            continue
        depth = len(path.relative_to(root).parts)
        if depth <= 0 or depth > max_depth:
            continue
        folders.append(path)
    return folders


def folder_surface_entry(
    hub: Hub,
    project_id: str,
    root_kind: str,
    root: Path,
    folder: Path,
    ignored: set[str],
) -> dict[str, Any]:
    relative_to_root = folder.relative_to(root).as_posix()
    path = folder.relative_to(hub.path).as_posix() if folder.is_relative_to(hub.path) else str(folder)
    return {
        "id": f"folder-surface:{safe_id(project_id)}:{safe_id(root_kind)}:{safe_id(relative_to_root)}",
        "type": "Folder",
        "title": folder.name,
        "path": path,
        "projects": [project_id],
        "roles": ["workspace_section"],
        "summary": summarize_folder(folder, ignored),
        "provider": {"name": "local_folder", "root_kind": root_kind},
        "review": {"status": "auto_indexed", "scope": "folder_surface"},
    }


def merge_folder_surface(existing: dict[str, Any], new_entry: dict[str, Any]) -> dict[str, Any]:
    preserved = {key: value for key, value in existing.items() if key not in {"summary", "provider", "review"}}
    merged = {**new_entry, **preserved}
    merged["summary"] = new_entry["summary"]
    merged["provider"] = new_entry["provider"]
    merged["review"] = new_entry["review"]
    return merged


def summarize_folder(folder: Path, ignored: set[str]) -> str:
    children = sorted([child for child in folder.iterdir() if not should_skip_directory(child, ignored)], key=lambda item: item.name)
    file_count = sum(1 for child in children if child.is_file())
    folder_count = sum(1 for child in children if child.is_dir())
    labels = labels_for_children(children)
    notable = ", ".join(child.name for child in children[:5])
    parts = [f"Folder with {count_phrase(file_count, 'file')}"]
    if folder_count:
        parts.append(count_phrase(folder_count, "subfolder"))
    if labels:
        parts.append(f"includes {', '.join(labels)}")
    if notable:
        parts.append(f"notable children: {notable}")
    return "; ".join(parts) + "."


def labels_for_children(children: list[Path]) -> list[str]:
    labels: list[str] = []
    for child in children:
        if not child.is_file():
            continue
        label = EXTENSION_LABELS.get(child.suffix.casefold())
        if label is not None and label not in labels:
            labels.append(label)
    return labels[:4]


def count_phrase(count: int, noun: str) -> str:
    return f"{count} {noun if count == 1 else noun + 's'}"


def should_skip_directory(path: Path, ignored: set[str]) -> bool:
    return any(part in ignored or part.startswith(".") for part in path.parts)


def confirm_proposal(hub: Hub, proposal_id: str) -> dict[str, Any]:
    inbox = load_inbox(hub)
    files = load_files(hub)
    proposal = next(
        (
            item
            for item in inbox
            if item.get("id") == proposal_id and item.get("status", "pending") == "pending"
        ),
        None,
    )
    if proposal is None:
        raise HubError(f"proposal not found or not pending: {proposal_id}")
    path = proposal.get("path")
    if not isinstance(path, str) or not path:
        raise HubError(f"proposal missing path: {proposal_id}")
    if any(file_entry.get("path") == path for file_entry in files):
        raise HubError(f"file already indexed for path: {path}")

    file_entry = file_entry_from_proposal(proposal)
    files.append(file_entry)
    proposal["status"] = "confirmed"
    proposal["confirmed_file"] = file_entry["id"]
    hub.files_path.write_text(yaml.safe_dump(files, sort_keys=False), encoding="utf-8")
    hub.inbox_path.write_text(yaml.safe_dump(inbox, sort_keys=False), encoding="utf-8")
    return file_entry


def file_entry_from_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    path = string_value(proposal.get("path"))
    proposed_type = string_value(proposal.get("proposed_type")) or "File"
    proposed_project = string_value(proposal.get("proposed_project"))
    proposed_role = string_value(proposal.get("proposed_role")) or role_for_type(proposed_type)
    provider = proposal.get("provider") if isinstance(proposal.get("provider"), dict) else {"name": "local_folder"}
    return {
        "id": f"file:{safe_id(path or 'unknown')}",
        "type": proposed_type,
        "title": Path(path or "unknown").name,
        "path": path,
        "projects": [proposed_project] if proposed_project else [],
        "roles": [proposed_role],
        "provider": provider,
        "review": {"status": "confirmed", "proposal_id": proposal.get("id")},
    }


def resolve_hub_path(hub: Hub, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return hub.path / path


def should_skip_path(path: Path, ignored: set[str] | None = None) -> bool:
    ignored = ignored or IGNORED_DIRS
    return not path.is_file() or any(part in ignored or part.startswith(".") for part in path.parts)


def proposal_for_path(path: str, project_id: str) -> dict[str, Any] | None:
    proposed_type = type_for_path(path)
    if proposed_type is None:
        return None
    return {
        "id": f"proposal:{safe_id(path)}",
        "path": path,
        "proposed_type": proposed_type,
        "proposed_role": role_for_type(proposed_type),
        "proposed_project": project_id,
        "provider": {"name": "local_folder"},
        "confidence": "medium",
        "status": "pending",
    }


def type_for_path(path: str) -> str | None:
    suffix = Path(path).suffix.casefold()
    parts = {part.casefold() for part in Path(path).parts}
    if suffix in {".csv", ".tsv", ".xlsx", ".json"} or "data" in parts:
        return "Dataset"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".tif", ".tiff"} or "figures" in parts:
        return "Figure"
    if suffix == ".pdf":
        return "Paper"
    if suffix in {".md", ".txt"}:
        return "Note"
    if suffix in {".doc", ".docx", ".tex"} or "manuscript" in parts:
        return "Manuscript"
    if suffix in {".py", ".r", ".R", ".ipynb", ".m"} or "analysis" in parts:
        return "Code"
    return None


def role_for_type(proposed_type: str) -> str:
    return {
        "Dataset": "dataset",
        "Figure": "figure",
        "Paper": "reference_paper",
        "Note": "note",
        "Manuscript": "manuscript",
        "Code": "code",
    }.get(proposed_type, "file")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-") or "unknown"


def string_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
