from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from research_os.config import Hub, HubError, load_projects, load_sources
from research_os.graph import build_graph, write_graph
from research_os.paths import obsidian_vault_path
from research_os.projects import find_project
from research_os.wiki import append_wiki_log, queue_wiki_integration


@dataclass(frozen=True)
class IngestResult:
    collection_name: str
    collection_key: str
    item_count: int
    vault_path: Path


def ingest_zotero_collection(hub: Hub, collection_ref: str, project_id: str, zotero_client: Any) -> IngestResult:
    projects = load_projects(hub)
    if find_project(projects, project_id) is None:
        raise HubError(f"unknown project: {project_id}")

    collection = resolve_collection(zotero_client.collections(), collection_ref)
    collection_key = collection["key"]
    collection_name = collection["name"]
    items = zotero_client.collection_top_items(collection_key)
    vault = obsidian_vault_path(hub)

    collection_note_path = vault / "Sources" / "Collections" / f"{safe_filename(collection_name)}.md"
    paper_entries: list[dict[str, Any]] = []
    paper_links: list[str] = []

    for item in items:
        entry = source_entry_from_zotero_item(item, project_id)
        paper_entries.append(entry)
        citation_key = entry["citation_key"]
        title = entry["title"]
        paper_links.append(f"- [[Sources/Papers/{citation_key}|{title}]]")
        paper_note_path = vault / "Sources" / "Papers" / f"{citation_key}.md"
        write_text_if_changed(paper_note_path, render_paper_note(entry, collection_name))
        queue_wiki_integration(
            hub,
            entry["id"],
            "academic-paper",
            "PDF/full text requires explicit confirmation",
        )
        append_wiki_log(
            hub,
            "register-source",
            entry["id"],
            f"Registered Zotero paper stub for {entry['title']}. Full paper integration remains queued.",
        )

    write_text_if_changed(
        collection_note_path,
        render_collection_note(collection_name, collection_key, project_id, paper_links),
    )
    merge_sources(hub, paper_entries)
    write_graph(hub, build_graph(hub))
    return IngestResult(collection_name=collection_name, collection_key=collection_key, item_count=len(paper_entries), vault_path=vault)


def resolve_collection(collections: list[dict[str, Any]], collection_ref: str) -> dict[str, str]:
    matches = [
        collection
        for collection in collections
        if collection.get("key") == collection_ref or str(collection.get("name", "")).casefold() == collection_ref.casefold()
    ]
    if not matches:
        raise HubError(f"Zotero collection not found: {collection_ref}")
    if len(matches) > 1:
        keys = ", ".join(str(collection.get("key")) for collection in matches)
        raise HubError(f"Zotero collection name is ambiguous: {collection_ref} ({keys})")
    collection = matches[0]
    key = collection.get("key")
    name = collection.get("name")
    if not isinstance(key, str) or not isinstance(name, str):
        raise HubError(f"Zotero collection is missing key or name: {collection_ref}")
    return {"key": key, "name": name}


def source_entry_from_zotero_item(item: dict[str, Any], project_id: str) -> dict[str, Any]:
    data = item.get("data", {})
    if not isinstance(data, dict):
        raise HubError("Zotero item missing data mapping")
    item_key = data.get("key") or item.get("key")
    title = data.get("title")
    citation_key = data.get("citationKey") or item_key
    if not isinstance(item_key, str) or not isinstance(title, str) or not isinstance(citation_key, str):
        raise HubError("Zotero item missing key, title, or citation key")
    entry = {
        "id": f"paper:{citation_key}",
        "type": "Paper",
        "title": title,
        "zotero_item_key": item_key,
        "citation_key": citation_key,
        "projects": [project_id],
        "concepts": [],
        "provider": {"name": "zotero", "key": item_key},
    }
    attachment_key = pdf_attachment_key(item)
    if attachment_key is not None:
        entry["zotero_attachment_key"] = attachment_key
        entry["provider"]["attachment_key"] = attachment_key
    doi = data.get("DOI")
    if isinstance(doi, str) and doi:
        entry["doi"] = doi
    return entry


def pdf_attachment_key(item: dict[str, Any]) -> str | None:
    links = item.get("links", {})
    if not isinstance(links, dict):
        return None
    attachment = links.get("attachment")
    if not isinstance(attachment, dict):
        return None
    href = attachment.get("href")
    if not isinstance(href, str) or not href:
        return None
    return href.rstrip("/").split("/")[-1]


def render_collection_note(collection_name: str, collection_key: str, project_id: str, paper_links: list[str]) -> str:
    lines = [
        "---",
        "type: zotero_collection",
        f"zotero_collection_key: {collection_key}",
        f"zotero_collection_name: {yaml_quote(collection_name)}",
        "tags:",
        "  - research-os/zotero-collection",
        "  - zotero/collection",
        f"  - zotero/collection/{safe_tag(collection_name)}",
        "---",
        "",
        f"# {collection_name}",
        "",
        f"[Open collection in Zotero](zotero://select/library/collections/{collection_key})",
        "",
        "## Papers",
        "",
        *paper_links,
        "",
        "## Projects",
        "",
        f"- [[Projects/{project_id}|{project_id}]]",
        "",
    ]
    return "\n".join(lines)


def render_paper_note(entry: dict[str, Any], collection_name: str) -> str:
    attachment_key = entry.get("zotero_attachment_key")
    lines = [
        "---",
        "type: paper",
        f"title: {yaml_quote(entry['title'])}",
        f"zotero_item_key: {entry['zotero_item_key']}",
        f"citation_key: {entry['citation_key']}",
    ]
    if isinstance(attachment_key, str):
        lines.append(f"zotero_attachment_key: {attachment_key}")
    if isinstance(entry.get("doi"), str):
        lines.append(f"doi: {entry['doi']}")
    lines.extend(
        [
            "tags:",
            "  - research-os/paper",
            "  - research-os/source",
            f"  - project/{entry['projects'][0]}",
            f"  - zotero/collection/{safe_tag(collection_name)}",
            "---",
            "",
            f"# {entry['title']}",
            "",
            f"[Open in Zotero](zotero://select/library/items/{entry['zotero_item_key']})",
            "",
        ]
    )
    if isinstance(attachment_key, str):
        lines.extend([f"[Open PDF in Zotero](zotero://open-pdf/library/items/{attachment_key})", ""])
    lines.extend(
        [
            "## Links",
            "",
            f"- Collection: [[Sources/Collections/{safe_filename(collection_name)}|{collection_name}]]",
            f"- Project: [[Projects/{entry['projects'][0]}|{entry['projects'][0]}]]",
            "",
        ]
    )
    return "\n".join(lines)


def merge_sources(hub: Hub, entries: list[dict[str, Any]]) -> None:
    sources = load_sources(hub)
    by_item_key = {
        source.get("zotero_item_key"): index
        for index, source in enumerate(sources)
        if isinstance(source, dict) and isinstance(source.get("zotero_item_key"), str)
    }
    for entry in entries:
        item_key = entry["zotero_item_key"]
        existing_index = by_item_key.get(item_key)
        if existing_index is None:
            sources.append(entry)
        else:
            sources[existing_index] = merge_source(sources[existing_index], entry)
    hub.sources_path.write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")


def merge_source(existing: dict[str, Any], new_entry: dict[str, Any]) -> dict[str, Any]:
    merged = {**existing, **new_entry}
    merged["projects"] = sorted(set(existing.get("projects", [])) | set(new_entry.get("projects", [])))
    merged["concepts"] = sorted(set(existing.get("concepts", [])) | set(new_entry.get("concepts", [])))
    return merged


def write_text_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "untitled"


def safe_tag(value: str) -> str:
    return safe_filename(value).lower()


def yaml_quote(value: str) -> str:
    if re.search(r"[:#\n]", value):
        return repr(value)
    return value
