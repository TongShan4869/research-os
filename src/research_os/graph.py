from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research_os.config import Hub, load_projects, load_sources

Graph = dict[str, list[dict[str, Any]]]


def build_graph(hub: Hub) -> Graph:
    projects = load_projects(hub)
    sources = load_sources(hub)
    return graph_from_registries(projects, sources)


def graph_from_registries(projects: list[dict[str, Any]], sources: list[dict[str, Any]]) -> Graph:
    nodes: list[dict[str, Any]] = []
    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    known_collection_keys = collection_keys_by_name(projects)

    for project in projects:
        project_id = string_value(project.get("id"))
        title = project.get("title")
        if project_id is None or not isinstance(title, str):
            continue

        project_node_id = f"project:{project_id}"
        collections = string_list(project.get("zotero_collections"))
        collection_keys = aligned_string_list(project.get("zotero_collection_keys"))
        project_collections = collection_items(project.get("zotero_collections"), project.get("zotero_collection_keys"))
        project_collection_key_by_name = first_collection_key_by_name(project_collections)
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

        for collection, collection_key, has_explicit_blank_key in project_collections:
            stable_key = collection_key or (
                None if has_explicit_blank_key else project_collection_key_by_name.get(collection)
            )
            collection_id = collection_node_id(collection, stable_key)
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": collection_id,
                    "type": "Collection",
                    "title": collection,
                    "metadata": clean_metadata({"zotero_collection_key": collection_key}),
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
        source_collections = collection_items(source.get("zotero_collections"), source.get("zotero_collection_keys"))
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
                edges.append(edge(f"project:{project_id}", concept_node_id(concept), "has_concept"))

        for concept in concepts:
            concept_id = concept_node_id(concept)
            add_node(nodes, nodes_by_id, {"id": concept_id, "type": "Concept", "title": concept_title(concept)})
            edges.append(edge(source_id, concept_id, "has_concept"))

        for collection, collection_key, has_explicit_blank_key in source_collections:
            known_key = collection_key or (None if has_explicit_blank_key else known_collection_keys.get(collection))
            collection_id = collection_node_id(collection, known_key)
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": collection_id,
                    "type": "Collection",
                    "title": collection,
                    "metadata": clean_metadata({"zotero_collection_key": known_key}),
                },
            )
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


def collection_items(collections_value: Any, keys_value: Any) -> list[tuple[str, str | None, bool]]:
    if not isinstance(collections_value, list):
        return []
    keys = keys_value if isinstance(keys_value, list) else []
    items: list[tuple[str, str | None, bool]] = []
    for index, item in enumerate(collections_value):
        collection = string_value(item)
        if collection is not None:
            raw_key = list_value_at(keys, index)
            has_explicit_blank_key = isinstance(raw_key, str) and string_value(raw_key) is None
            collection_key = string_value(raw_key)
            items.append((collection, collection_key, has_explicit_blank_key))
    return items


def first_collection_key_by_name(collections: list[tuple[str, str | None, bool]]) -> dict[str, str]:
    keys_by_name: dict[str, str] = {}
    for collection, collection_key, _has_explicit_blank_key in collections:
        if collection_key is not None and collection not in keys_by_name:
            keys_by_name[collection] = collection_key
    return keys_by_name


def collection_keys_by_name(projects: list[dict[str, Any]]) -> dict[str, str]:
    keys_by_name: dict[str, set[str]] = {}
    names_with_explicit_blank: set[str] = set()
    for project in projects:
        for collection, collection_key, has_explicit_blank_key in collection_items(
            project.get("zotero_collections"), project.get("zotero_collection_keys")
        ):
            if has_explicit_blank_key:
                names_with_explicit_blank.add(collection)
            if collection_key is None:
                continue
            keys_by_name.setdefault(collection, set()).add(collection_key)
    return {
        name: next(iter(keys))
        for name, keys in keys_by_name.items()
        if len(keys) == 1 and name not in names_with_explicit_blank
    }


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


def collection_node_id(collection: str, collection_key: str | None = None) -> str:
    stable_value = collection_key or collection
    return f"collection:{safe_id(stable_value)}"


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


def read_graph(hub: Hub) -> Graph:
    graph_path = hub.path / "graph" / "graph.json"
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"nodes": [], "edges": []}
    nodes = data.get("nodes")
    edges = data.get("edges")
    return {
        "nodes": nodes if isinstance(nodes, list) else [],
        "edges": edges if isinstance(edges, list) else [],
    }
