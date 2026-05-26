from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research_os.config import Hub, load_projects, load_sources


def build_graph(hub: Hub) -> dict[str, list[dict[str, Any]]]:
    projects = load_projects(hub)
    sources = load_sources(hub)
    nodes: list[dict[str, Any]] = []
    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for project in projects:
        project_id = string_value(project.get("id"))
        title = project.get("title")
        if project_id is None or not isinstance(title, str):
            continue

        project_node_id = f"project:{project_id}"
        collections = string_list(project.get("zotero_collections"))
        collection_keys = aligned_string_list(project.get("zotero_collection_keys"))
        project_collections = collection_items(project.get("zotero_collections"), project.get("zotero_collection_keys"))
        concepts = string_list(project.get("concepts"))
        add_node(
            nodes,
            nodes_by_id,
            {
                "id": project_node_id,
                "type": "Project",
                "title": title,
                "metadata": clean_metadata(
                    {
                        "status": string_value(project.get("status")),
                        "tags": string_list(project.get("tags")),
                        "obsidian_note": string_value(project.get("obsidian_note")),
                        "zotero_collections": collections,
                        "zotero_collection_keys": collection_keys,
                    }
                ),
            },
        )

        for concept in concepts:
            concept_id = concept_node_id(concept)
            add_node(nodes, nodes_by_id, {"id": concept_id, "type": "Concept", "title": concept_title(concept)})
            edges.append(edge(project_node_id, concept_id, "has_concept"))

        for collection, collection_key in project_collections:
            collection_id = collection_node_id(collection)
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": collection_id,
                    "type": "Collection",
                    "title": collection,
                    "metadata": clean_metadata(
                        {"zotero_collection_key": collection_key}
                    ),
                },
            )
            edges.append(edge(project_node_id, collection_id, "in_collection"))

        for kind, folder_path in folder_items(project.get("folders")):
            folder_id = f"folder:{project_id}:{safe_id(kind)}"
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": folder_id,
                    "type": "Folder",
                    "title": kind,
                    "metadata": clean_metadata({"kind": kind, "path": folder_path}),
                },
            )
            edges.append(edge(project_node_id, folder_id, "attached_folder"))

    for source in sources:
        source_id = string_value(source.get("id"))
        source_type = source.get("type", "Paper")
        title = source.get("title")
        if source_id is None or not isinstance(title, str):
            continue
        node_type = source_type if isinstance(source_type, str) else "Paper"
        projects_for_source = string_list(source.get("projects"))
        concepts = string_list(source.get("concepts"))
        collections = string_list(source.get("zotero_collections"))
        add_node(
            nodes,
            nodes_by_id,
            {
                "id": source_id,
                "type": node_type,
                "title": title,
                "metadata": clean_metadata(
                    {
                        "citation_key": string_value(source.get("citation_key")),
                        "zotero_item_key": string_value(source.get("zotero_item_key")),
                        "zotero_attachment_key": string_value(source.get("zotero_attachment_key")),
                        "doi": string_value(source.get("doi")),
                        "tags": string_list(source.get("tags")),
                        "roles": string_list(source.get("roles")),
                        "projects": projects_for_source,
                        "concepts": concepts,
                        "zotero_collections": collections,
                    }
                ),
            },
        )

        for project_id in projects_for_source:
            edges.append(edge(f"project:{project_id}", source_id, "uses"))

        for concept in concepts:
            concept_id = concept_node_id(concept)
            add_node(nodes, nodes_by_id, {"id": concept_id, "type": "Concept", "title": concept_title(concept)})
            edges.append(edge(source_id, concept_id, "has_concept"))

        for collection in collections:
            collection_id = collection_node_id(collection)
            add_node(nodes, nodes_by_id, {"id": collection_id, "type": "Collection", "title": collection})
            edges.append(edge(source_id, collection_id, "in_collection"))

    return {"nodes": nodes, "edges": dedupe_edges(edges)}


def add_node(
    nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    node: dict[str, Any],
) -> None:
    node_id = string_value(node.get("id"))
    if node_id is None:
        return

    if node_id not in nodes_by_id:
        clean_node = clean_metadata(node)
        nodes_by_id[node_id] = clean_node
        nodes.append(clean_node)
        return

    existing = nodes_by_id[node_id]
    if "metadata" in node:
        metadata = clean_metadata(node.get("metadata"))
        if metadata:
            existing_metadata = existing.setdefault("metadata", {})
            if isinstance(existing_metadata, dict):
                existing_metadata.update({key: value for key, value in metadata.items() if key not in existing_metadata})


def edge(source: str, target: str, edge_type: str) -> dict[str, str]:
    return {"source": source, "target": target, "type": edge_type}


def dedupe_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for item in edges:
        key = (item["source"], item["target"], item["type"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def clean_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: item for key, item in value.items() if item not in (None, [], {})}


def folder_items(value: Any) -> list[tuple[str, str]]:
    if not isinstance(value, dict):
        return []
    items: list[tuple[str, str]] = []
    for key, item in value.items():
        kind = string_value(key)
        path = string_value(item)
        if kind is not None and path is not None:
            items.append((kind, path))
    return items


def collection_items(collections_value: Any, keys_value: Any) -> list[tuple[str, str | None]]:
    if not isinstance(collections_value, list):
        return []
    keys = keys_value if isinstance(keys_value, list) else []
    items: list[tuple[str, str | None]] = []
    for index, item in enumerate(collections_value):
        collection = string_value(item)
        if collection is not None:
            items.append((collection, string_value(list_value_at(keys, index))))
    return items


def aligned_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    strings: list[str] = []
    for item in value:
        strings.append(item.strip() if isinstance(item, str) else "")
    return strings


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    strings: list[str] = []
    for item in value:
        string = string_value(item)
        if string is not None:
            strings.append(string)
    return strings


def string_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def list_value_at(values: list[Any], index: int) -> Any:
    if 0 <= index < len(values):
        return values[index]
    return None


def concept_node_id(concept: str) -> str:
    return f"concept:{safe_id(concept)}"


def collection_node_id(collection: str) -> str:
    return f"collection:{safe_id(collection)}"


def concept_title(concept: str) -> str:
    return concept.replace("-", " ")


def safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    return safe or "unknown"


def write_graph(hub: Hub, graph: dict[str, list[dict[str, Any]]]) -> Path:
    graph_path = hub.path / "graph" / "graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return graph_path
