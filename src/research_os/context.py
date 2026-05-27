from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_os.config import Hub, HubError, load_files, load_inbox, load_projects, load_relations, load_sources
from research_os.graph import graph_from_registries
from research_os.paths import obsidian_vault_path
from research_os.wiki import wiki_pages_for_query


def build_context_packet(hub: Hub, query: str) -> dict[str, Any]:
    projects = load_projects(hub)
    sources = load_sources(hub)
    files = load_files(hub)
    relations = load_relations(hub)
    inbox = load_inbox(hub)

    wiki_pages = enrich_wiki_pages(hub, wiki_pages_for_query(hub, query))
    match = match_query(query, projects, sources, files, wiki_pages)
    if match is None:
        raise HubError(f"context unresolved: {query}")

    project_ids = related_project_ids(match, projects, sources, files)
    source_ids = related_source_ids(project_ids, match, sources)
    file_ids = related_file_ids(project_ids, match, files)
    related_node_ids = {f"project:{project_id}" for project_id in project_ids} | source_ids | file_ids
    related_items = [
        *[project for project in projects if project.get("id") in project_ids],
        *[source for source in sources if source.get("id") in source_ids],
        *[file_entry for file_entry in files if file_entry.get("id") in file_ids],
    ]
    graph = graph_from_registries(projects, sources, files, relations)

    return {
        "query": query,
        "match": match,
        "projects": [project for project in projects if project.get("id") in project_ids],
        "sources": [source for source in sources if source.get("id") in source_ids],
        "files": [file_entry for file_entry in files if file_entry.get("id") in file_ids],
        "relations": [
            relation
            for relation in relations
            if relation.get("source") in related_node_ids or relation.get("target") in related_node_ids
        ],
        "concepts": sorted({concept for item in related_items for concept in string_list(item.get("concepts"))}),
        "inbox": [
            proposal
            for proposal in inbox
            if proposal.get("proposed_project") in project_ids and proposal.get("status", "pending") == "pending"
        ],
        "wiki_pages": wiki_pages,
        "graph_neighbors": graph_neighbors(graph, related_node_ids),
    }


def render_context_json(packet: dict[str, Any]) -> str:
    return json.dumps(packet, indent=2, sort_keys=True, default=str) + "\n"


def render_context_markdown(packet: dict[str, Any]) -> str:
    title = packet["match"].get("title") or packet["query"]
    lines = [
        f"# Context Packet: {title}",
        "",
        "## Projects",
        "",
        *[f"- {project.get('id')}: {project.get('title')}" for project in packet["projects"]],
        "",
        "## Sources",
        "",
        *item_lines(packet["sources"]),
        "",
        "## Files",
        "",
        *item_lines(packet["files"]),
        "",
        "## Concepts",
        "",
        *([f"- {concept}" for concept in packet["concepts"]] or ["- None"]),
        "",
        "## Inbox",
        "",
        *([f"- {proposal.get('path')} -> {proposal.get('proposed_type')}" for proposal in packet["inbox"]] or ["- None"]),
        "",
        "## Wiki Pages",
        "",
        *wiki_page_lines(packet["wiki_pages"]),
        "",
        "## Graph Neighbors",
        "",
        *graph_neighbor_lines(packet["graph_neighbors"]),
        "",
    ]
    return "\n".join(lines)


def item_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item.get('id')}: {item.get('title')}" for item in items]


def wiki_page_lines(pages: list[dict[str, str]]) -> list[str]:
    if not pages:
        return ["- None"]
    lines: list[str] = []
    for page in pages:
        line = f"- {page.get('path')}: {page.get('summary')}"
        excerpt = page.get("excerpt")
        if excerpt:
            line += f" - {excerpt}"
        lines.append(line)
    return lines


def graph_neighbor_lines(neighbors: list[dict[str, str]]) -> list[str]:
    if not neighbors:
        return ["- None"]
    return [
        f"- {neighbor.get('node_id')}: {neighbor.get('title')} "
        f"({neighbor.get('type')}, {neighbor.get('relation')})"
        for neighbor in neighbors
    ]


def match_query(
    query: str,
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    files: list[dict[str, Any]],
    wiki_pages: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    normalized = normalized_query(query)
    for project in projects:
        project_id = string_value(project.get("id"))
        title = string_value(project.get("title"))
        if normalized in project_match_terms(project):
            return {"id": f"project:{project_id}", "type": "Project", "title": title or project_id}
    for source in sources:
        if query_matches_item(query, source):
            return {"id": source.get("id"), "type": source.get("type", "Source"), "title": source.get("title")}
    for file_entry in files:
        if query_matches_item(query, file_entry):
            return {"id": file_entry.get("id"), "type": file_entry.get("type", "File"), "title": file_entry.get("title")}
    for page in wiki_pages or []:
        if normalized in wiki_page_match_terms(page):
            return {"id": f"wiki:{page['path']}", "type": "WikiPage", "title": page.get("title")}
    return None


def query_matches_item(query: str, item: dict[str, Any]) -> bool:
    candidates = [
        string_value(item.get("id")),
        string_value(item.get("title")),
        string_value(item.get("citation_key")),
        string_value(item.get("path")),
        *string_list(item.get("tags")),
        *string_list(item.get("concepts")),
        *string_list(item.get("zotero_collections")),
    ]
    return normalized_query(query) in {normalized_query(candidate) for candidate in candidates if candidate}


def project_match_terms(project: dict[str, Any]) -> set[str]:
    candidates = [
        string_value(project.get("id")),
        string_value(project.get("title")),
        *string_list(project.get("tags")),
        *string_list(project.get("concepts")),
        *string_list(project.get("zotero_collections")),
        *folder_values(project.get("folders")),
    ]
    return {normalized_query(candidate) for candidate in candidates if candidate}


def wiki_page_match_terms(page: dict[str, str]) -> set[str]:
    return {
        normalized_query(value)
        for value in (page.get("path"), page.get("title"), page.get("summary"), page.get("excerpt"))
        if value
    }


def enrich_wiki_pages(hub: Hub, pages: list[dict[str, str]]) -> list[dict[str, str]]:
    vault = obsidian_vault_path(hub)
    enriched = []
    for page in pages:
        item = dict(page)
        path = string_value(page.get("path"))
        if path is not None:
            excerpt = wiki_page_excerpt(vault / path)
            if excerpt:
                item["excerpt"] = excerpt
        enriched.append(item)
    return enriched


def wiki_page_excerpt(path: Path, max_chars: int = 360) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    body = strip_frontmatter(text)
    chunks: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        chunks.append(stripped)
        if len(" ".join(chunks)) >= max_chars:
            break
    excerpt = " ".join(chunks).strip()
    if not excerpt:
        return None
    if len(excerpt) <= max_chars:
        return excerpt
    return excerpt[: max_chars - 1].rstrip() + "..."


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 4 :]


def graph_neighbors(graph: dict[str, Any], seed_node_ids: set[str]) -> list[dict[str, str]]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return []
    nodes_by_id = {node.get("id"): node for node in nodes if isinstance(node, dict) and isinstance(node.get("id"), str)}
    neighbors: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = string_value(edge.get("source"))
        target = string_value(edge.get("target"))
        relation_type = string_value(edge.get("type"))
        if source is None or target is None or relation_type is None:
            continue
        if source in seed_node_ids and target not in seed_node_ids:
            add_graph_neighbor(neighbors, seen, nodes_by_id.get(target), relation_type, "out")
        elif target in seed_node_ids and source not in seed_node_ids:
            add_graph_neighbor(neighbors, seen, nodes_by_id.get(source), relation_type, "in")
    return neighbors


def add_graph_neighbor(
    neighbors: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    node: dict[str, Any] | None,
    relation_type: str,
    direction: str,
) -> None:
    if node is None:
        return
    node_id = string_value(node.get("id"))
    title = string_value(node.get("title"))
    node_type = string_value(node.get("type"))
    if node_id is None or title is None or node_type is None:
        return
    key = (node_id, relation_type, direction)
    if key in seen:
        return
    seen.add(key)
    relation = f"{direction}:{relation_type}"
    neighbors.append({"node_id": node_id, "title": title, "type": node_type, "relation": relation})


def related_project_ids(
    match: dict[str, Any],
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    files: list[dict[str, Any]],
) -> set[str]:
    match_id = match["id"]
    if isinstance(match_id, str) and match_id.startswith("project:"):
        return {match_id.removeprefix("project:")}
    for source in sources:
        if source.get("id") == match_id:
            return set(string_list(source.get("projects")))
    for file_entry in files:
        if file_entry.get("id") == match_id:
            return set(string_list(file_entry.get("projects")))
    if isinstance(match_id, str) and match_id.startswith("wiki:"):
        page_terms = wiki_page_match_terms(
            {
                "path": match_id.removeprefix("wiki:"),
                "title": string_value(match.get("title")) or "",
                "summary": "",
            }
        )
        matches = {
            project["id"]
            for project in projects
            if isinstance(project.get("id"), str) and project_match_terms(project) & page_terms
        }
        if matches:
            return matches
    return {project["id"] for project in projects if isinstance(project.get("id"), str)}


def related_source_ids(project_ids: set[str], match: dict[str, Any], sources: list[dict[str, Any]]) -> set[str]:
    ids = {
        source["id"]
        for source in sources
        if isinstance(source.get("id"), str) and set(string_list(source.get("projects"))) & project_ids
    }
    if isinstance(match.get("id"), str) and match["id"].startswith("paper:"):
        ids.add(match["id"])
    return ids


def related_file_ids(project_ids: set[str], match: dict[str, Any], files: list[dict[str, Any]]) -> set[str]:
    ids = {
        file_entry["id"]
        for file_entry in files
        if isinstance(file_entry.get("id"), str) and set(string_list(file_entry.get("projects"))) & project_ids
    }
    if isinstance(match.get("id"), str) and match["id"].startswith("file:"):
        ids.add(match["id"])
    return ids


def string_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def folder_values(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return [item.strip() for item in value.values() if isinstance(item, str) and item.strip()]


def normalized_query(value: str) -> str:
    return value.strip().casefold().removesuffix(".md")
