from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from research_os.config import Hub, load_files, load_inbox, load_projects, load_relations, load_sources
from research_os.graph import graph_from_registries
from research_os.paths import obsidian_vault_path
from research_os.staleness import FINGERPRINT_KEY, FINGERPRINT_VERSION, FINGERPRINT_VERSION_KEY, home_fingerprint
from research_os.wiki import count_pending_wiki_integrations, ensure_concept_notes, folder_guide_markdown_table, wiki_page_count


def build_index(hub: Hub) -> Path:
    projects = load_projects(hub)
    sources = load_sources(hub)
    inbox = load_inbox(hub)
    files = load_files(hub)
    relations = load_relations(hub)
    ensure_concept_notes(hub, registry_concepts(projects, sources, files))
    home_path = obsidian_vault_path(hub) / "Home.md"
    write_text_if_changed(
        home_path,
        render_home(
            projects,
            sources,
            inbox,
            files,
            relations,
            wiki_pending=count_pending_wiki_integrations(hub),
            wiki_pages=wiki_page_count(hub),
            fingerprint=home_fingerprint(hub),
        ),
    )
    return home_path


def registry_concepts(
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    files: list[dict[str, Any]],
) -> list[str]:
    concepts: list[str] = []
    for item in [*projects, *sources, *files]:
        concepts.extend(string_list(item.get("concepts")))
    return concepts


def render_home(
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    inbox: list[dict[str, Any]] | None = None,
    files: list[dict[str, Any]] | None = None,
    relations: list[dict[str, Any]] | None = None,
    wiki_pending: int = 0,
    wiki_pages: int = 0,
    fingerprint: str | None = None,
) -> str:
    inbox = inbox or []
    files = files or []
    relations = relations or []
    graph = graph_from_registries(projects, sources, files, relations)
    lines = [
        "---",
        "type: research_os_home",
        *(fingerprint_frontmatter(fingerprint)),
        "tags:",
        "  - research-os/home",
        "---",
        "",
        "# Research OS",
        "",
        "## Visual Explorer",
        "",
        "- [Open visual explorer](../../visual/index.html)",
        f"- Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges",
        "",
        "## LLM Wiki",
        "",
        "- [Wiki index](index.md)",
        "- [Wiki log](log.md)",
        "- [Integration inbox](wiki/inbox.md)",
        f"- Pending wiki integrations: {wiki_pending}",
        f"- Maintained wiki pages: {wiki_pages}",
        "",
        "## Folder Guide",
        "",
        folder_guide_markdown_table(include_maintainer=True),
        "",
        "## Projects",
        "",
        "| Project | Status | Zotero Collections | Sources | Tags |",
        "| --- | --- | --- | ---: | --- |",
    ]
    lines.extend(project_table_rows(projects, sources))
    lines.extend(
        [
            "",
            "## Zotero Collections",
            "",
            *collection_lines(projects),
            "",
            "## Recent Sources",
            "",
            *source_lines(sources),
            "",
            "## Context Readiness",
            "",
            *fingerprint_lines(fingerprint),
            f"- Pending inbox proposals: {count_pending_inbox(inbox)}",
            f"- Confirmed indexed files: {len(files)}",
            f"- Projects with folders: {count_projects_with_folders(projects)}",
            "",
            "## Needs Attention",
            "",
            f"- Projects with no Zotero collection: {count_projects_without_collections(projects)}",
            f"- Sources with no linked project: {count_sources_without_projects(sources)}",
            f"- Sources with no concepts: {count_sources_without_concepts(sources)}",
            "",
        ]
    )
    return "\n".join(lines)


def fingerprint_frontmatter(fingerprint: str | None) -> list[str]:
    if fingerprint is None:
        return []
    return [
        f"{FINGERPRINT_KEY}: {fingerprint}",
        f"{FINGERPRINT_VERSION_KEY}: {FINGERPRINT_VERSION}",
    ]


def fingerprint_lines(fingerprint: str | None) -> list[str]:
    if fingerprint is None:
        return []
    return [f"- Home context fingerprint: `{fingerprint}`"]


def project_table_rows(projects: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[str]:
    if not projects:
        return ["| No projects yet |  |  | 0 |  |"]
    return [project_table_row(project, sources) for project in projects]


def project_table_row(project: dict[str, Any], sources: list[dict[str, Any]]) -> str:
    project_id = string_value(project.get("id"), "unknown")
    title = string_value(project.get("title"), project_id)
    status = markdown_table_cell(string_value(project.get("status"), ""))
    note_link = obsidian_link(note_target(project.get("obsidian_note"), f"Projects/{project_id}"), title)
    collections = markdown_table_cell(collection_links(project.get("zotero_collections")))
    source_count = sum(1 for source in sources if project_id in string_list(source.get("projects")))
    tags = markdown_table_cell(", ".join(string_list(project.get("tags"))))
    return f"| {markdown_table_cell(note_link)} | {status} | {collections} | {source_count} | {tags} |"


def collection_lines(projects: list[dict[str, Any]]) -> list[str]:
    linked_projects: dict[str, set[str]] = defaultdict(set)
    for project in projects:
        project_id = project.get("id")
        if not isinstance(project_id, str) or not project_id:
            continue
        for collection in string_list(project.get("zotero_collections")):
            linked_projects[collection].add(project_id)
    if not linked_projects:
        return ["- No Zotero collections linked yet."]
    return [
        f"- {collection_link(collection)}: {len(project_ids)} linked {plural('project', len(project_ids))}"
        for collection, project_ids in sorted(linked_projects.items(), key=lambda item: item[0].casefold())
    ]


def source_lines(sources: list[dict[str, Any]]) -> list[str]:
    if not sources:
        return ["- No sources yet."]
    return [source_line(source) for source in sources]


def source_line(source: dict[str, Any]) -> str:
    title = string_value(source.get("title"), "Untitled Source")
    target = f"Sources/Papers/{source_note_stem(source)}"
    return f"- {obsidian_link(target, title)}"


def source_note_stem(source: dict[str, Any]) -> str:
    citation_key = source.get("citation_key")
    if isinstance(citation_key, str) and citation_key:
        return safe_filename(citation_key)
    source_id = source.get("id")
    if isinstance(source_id, str) and source_id:
        return safe_filename(source_id.removeprefix("paper:"))
    return "untitled"


def collection_links(value: Any) -> str:
    collections = string_list(value)
    if not collections:
        return ""
    return ", ".join(collection_link(collection) for collection in collections)


def collection_link(collection: str) -> str:
    return obsidian_link(f"Sources/Collections/{safe_filename(collection)}", collection)


def obsidian_link(target: str, label: str) -> str:
    return f"[[{target}|{label}]]"


def markdown_table_cell(value: str) -> str:
    return value.replace("|", r"\|")


def note_target(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value:
        return fallback
    return value.removesuffix(".md")


def count_projects_without_collections(projects: list[dict[str, Any]]) -> int:
    return sum(1 for project in projects if not string_list(project.get("zotero_collections")))


def count_sources_without_projects(sources: list[dict[str, Any]]) -> int:
    return sum(1 for source in sources if not string_list(source.get("projects")))


def count_sources_without_concepts(sources: list[dict[str, Any]]) -> int:
    return sum(1 for source in sources if not string_list(source.get("concepts")))


def count_pending_inbox(inbox: list[dict[str, Any]]) -> int:
    return sum(1 for item in inbox if item.get("status", "pending") == "pending")


def count_projects_with_folders(projects: list[dict[str, Any]]) -> int:
    return sum(1 for project in projects if isinstance(project.get("folders"), dict) and bool(project["folders"]))


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def string_value(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and value else fallback


def plural(word: str, count: int) -> str:
    return word if count == 1 else f"{word}s"


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "untitled"


def write_text_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")
