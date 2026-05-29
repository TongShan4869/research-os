from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from research_os.config import Hub, load_files, load_projects, load_relations, load_sources
from research_os.paths import obsidian_vault_path
from research_os.staleness import graph_with_fingerprint
from research_os.wiki import ensure_concept_notes

Graph = dict[str, Any]


def build_graph(hub: Hub) -> Graph:
    projects = load_projects(hub)
    sources = load_sources(hub)
    files = load_files(hub)
    relations = load_relations(hub)
    ensure_concept_notes(hub, registry_concepts(projects, sources, files))
    return graph_from_registries(projects, sources, files, relations, node_descriptions=load_node_descriptions(hub))


def registry_concepts(
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    files: list[dict[str, Any]],
) -> list[str]:
    concepts: list[str] = []
    for item in [*projects, *sources, *files]:
        concepts.extend(string_list(item.get("concepts")))
    return concepts


def graph_from_registries(
    projects: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    files: list[dict[str, Any]] | None = None,
    relations: list[dict[str, Any]] | None = None,
    node_descriptions: dict[str, dict[str, Any]] | None = None,
) -> Graph:
    nodes: list[dict[str, Any]] = []
    nodes_by_id: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    known_collection_keys = collection_keys_by_name(projects)
    files = files or []
    relations = relations or []
    node_descriptions = node_descriptions or {}

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
        project_description = description_payload(
            project_node_id,
            "Project",
            title,
            {
                "status": string_value(project.get("status")),
                "tags": string_list(project.get("tags")),
                "zotero_collections": collections,
            },
            explicit=string_value(project.get("description")) or string_value(project.get("summary")),
            node_descriptions=node_descriptions,
        )
        add_node(
            nodes,
            nodes_by_id,
            {
                "id": project_node_id,
                "type": "Project",
                "title": title,
                "description": project_description["description"],
                "metadata": clean_metadata(
                    {
                        "status": string_value(project.get("status")),
                        "tags": string_list(project.get("tags")),
                        "obsidian_note": string_value(project.get("obsidian_note")),
                        "zotero_collections": collections,
                        "zotero_collection_keys": collection_keys,
                        "description_source": mapping_value(project_description.get("source")),
                    }
                ),
            },
        )

        for concept in concepts:
            concept_id = add_concept_node(nodes, nodes_by_id, concept, node_descriptions)
            edges.append(edge(project_node_id, concept_id, "has_concept"))

        for collection, collection_key, has_explicit_blank_key in project_collections:
            stable_key = collection_key or (
                None if has_explicit_blank_key else project_collection_key_by_name.get(collection)
            )
            collection_id = collection_node_id(collection, stable_key)
            collection_description = description_payload(
                collection_id,
                "Collection",
                collection,
                {"zotero_collection_key": collection_key},
                node_descriptions=node_descriptions,
            )
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": collection_id,
                    "type": "Collection",
                    "title": collection,
                    "description": collection_description["description"],
                    "metadata": clean_metadata(
                        {
                            "zotero_collection_key": collection_key,
                            "description_source": mapping_value(collection_description.get("source")),
                        }
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
                    "description": node_description(
                        "Folder",
                        kind,
                        {"project_id": project_id, "kind": kind, "path": folder_path},
                    ),
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
        source_description = description_payload(
            source_id,
            node_type,
            title,
            {
                "abstract": string_value(source.get("abstract")),
                "projects": projects_for_source,
                "concepts": concepts,
                "roles": string_list(source.get("roles")),
                "publication_title": string_value(source.get("publication_title")),
            },
            explicit=string_value(source.get("description")) or string_value(source.get("summary")),
            node_descriptions=node_descriptions,
        )
        add_node(
            nodes,
            nodes_by_id,
            {
                "id": source_id,
                "type": node_type,
                "title": title,
                "description": source_description["description"],
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
                        "provider": mapping_value(source.get("provider")),
                        "description_source": mapping_value(source_description.get("source")),
                    }
                ),
            },
        )

        for project_id in projects_for_source:
            edges.append(edge(f"project:{project_id}", source_id, "uses"))
            for concept in concepts:
                edges.append(edge(f"project:{project_id}", concept_node_id(concept), "has_concept"))

        for concept in concepts:
            concept_id = add_concept_node(nodes, nodes_by_id, concept, node_descriptions)
            edges.append(edge(source_id, concept_id, "has_concept"))

        for collection, collection_key, has_explicit_blank_key in source_collections:
            known_key = collection_key or (None if has_explicit_blank_key else known_collection_keys.get(collection))
            collection_id = collection_node_id(collection, known_key)
            collection_description = description_payload(
                collection_id,
                "Collection",
                collection,
                {"zotero_collection_key": known_key},
                node_descriptions=node_descriptions,
            )
            add_node(
                nodes,
                nodes_by_id,
                {
                    "id": collection_id,
                    "type": "Collection",
                    "title": collection,
                    "description": collection_description["description"],
                    "metadata": clean_metadata(
                        {
                            "zotero_collection_key": known_key,
                            "description_source": mapping_value(collection_description.get("source")),
                        }
                    ),
                },
            )
            edges.append(edge(source_id, collection_id, "in_collection"))

    for file_entry in files:
        file_id = string_value(file_entry.get("id"))
        title = file_entry.get("title")
        if file_id is None or not isinstance(title, str):
            continue
        file_type = string_value(file_entry.get("type")) or "File"
        projects_for_file = string_list(file_entry.get("projects"))
        concepts = string_list(file_entry.get("concepts"))
        file_description = description_payload(
            file_id,
            file_type,
            title,
            {
                "path": string_value(file_entry.get("path")),
                "roles": string_list(file_entry.get("roles")),
                "projects": projects_for_file,
                "concepts": concepts,
            },
            explicit=string_value(file_entry.get("description")) or string_value(file_entry.get("summary")),
            node_descriptions=node_descriptions,
        )
        add_node(
            nodes,
            nodes_by_id,
            {
                "id": file_id,
                "type": file_type,
                "title": title,
                "description": file_description["description"],
                "metadata": clean_metadata(
                    {
                        "path": string_value(file_entry.get("path")),
                        "roles": string_list(file_entry.get("roles")),
                        "projects": projects_for_file,
                        "concepts": concepts,
                        "provider": mapping_value(file_entry.get("provider")),
                        "review": mapping_value(file_entry.get("review")),
                        "description_source": mapping_value(file_description.get("source")),
                    }
                ),
            },
        )

        for project_id in projects_for_file:
            edges.append(edge(f"project:{project_id}", file_id, "uses"))
        for concept in concepts:
            concept_id = add_concept_node(nodes, nodes_by_id, concept, node_descriptions)
            edges.append(edge(file_id, concept_id, "has_concept"))

    for relation in relations:
        source = string_value(relation.get("source"))
        target = string_value(relation.get("target"))
        relation_type = string_value(relation.get("type"))
        if source is None or target is None or relation_type is None:
            continue
        edges.append(edge(source, target, relation_type))

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
    description = string_value(node.get("description"))
    if description is not None and "description" not in existing:
        existing["description"] = description


def add_concept_node(
    nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    concept: str,
    node_descriptions: dict[str, dict[str, Any]],
) -> str:
    concept_id = concept_node_id(concept)
    concept_name = concept_title(concept)
    concept_description = description_payload(
        concept_id,
        "Concept",
        concept_name,
        {"concept": concept},
        node_descriptions=node_descriptions,
    )
    add_node(
        nodes,
        nodes_by_id,
        {
            "id": concept_id,
            "type": "Concept",
            "title": concept_name,
            "description": concept_description["description"],
            "metadata": clean_metadata(
                {
                    "description_source": mapping_value(concept_description.get("source")),
                }
            ),
        },
    )
    return concept_id


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


def description_payload(
    node_id: str,
    node_type: str,
    title: str,
    metadata: dict[str, Any] | None = None,
    *,
    explicit: str | None = None,
    node_descriptions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if explicit:
        return {
            "description": one_line(explicit, max_chars=1200),
            "source": {"kind": "registry", "field": "description"},
        }

    note_description = (node_descriptions or {}).get(node_id)
    if note_description:
        return {
            "description": one_line(string_value(note_description.get("description")) or "", max_chars=1200),
            "source": clean_metadata(
                {
                    "kind": "obsidian_note",
                    "path": string_value(note_description.get("path")),
                    "section": string_value(note_description.get("section")),
                }
            ),
        }

    return {
        "description": node_description(node_type, title, metadata),
        "source": {"kind": "generated", "reason": "missing canonical description"},
    }


def node_description(
    node_type: str,
    title: str,
    metadata: dict[str, Any] | None = None,
    *,
    explicit: str | None = None,
) -> str:
    if explicit:
        return one_line(explicit)

    metadata = metadata or {}
    if node_type == "Project":
        status = string_value(metadata.get("status")) or "indexed"
        tags = string_list(metadata.get("tags"))
        collections = string_list(metadata.get("zotero_collections"))
        parts = [f"{status.title()} research project"]
        if tags:
            parts.append(f"tagged {join_human(tags[:2])}")
        if collections:
            parts.append(f"linked to {join_human(collections[:2])}")
        return one_line("; ".join(parts) + ".")

    if node_type == "Paper":
        abstract = first_sentence(string_value(metadata.get("abstract")))
        if abstract:
            return one_line(abstract)
        concepts = [concept_title(concept) for concept in string_list(metadata.get("concepts"))]
        projects = [strip_prefix(project, "project:") for project in string_list(metadata.get("projects"))]
        if concepts and projects:
            return one_line(f"Paper linked to {join_human(projects[:2])} about {join_human(concepts[:2])}.")
        if concepts:
            return one_line(f"Paper about {join_human(concepts[:2])}.")
        return one_line("Indexed paper source in the research graph.")

    if node_type == "Concept":
        return one_line(f"Concept definition missing for {title}. Add it to the matching Concepts note.")

    if node_type == "Collection":
        key = string_value(metadata.get("zotero_collection_key"))
        suffix = f" with Zotero key {key}" if key else ""
        return one_line(f"Zotero collection{suffix} grouping related sources.")

    if node_type == "Folder":
        kind = string_value(metadata.get("kind")) or title
        project_id = string_value(metadata.get("project_id"))
        if project_id:
            return one_line(f"{kind.title()} folder attached to {project_id}.")
        return one_line(f"{kind.title()} folder indexed in the workspace.")

    roles = string_list(metadata.get("roles"))
    projects = [strip_prefix(project, "project:") for project in string_list(metadata.get("projects"))]
    path = string_value(metadata.get("path"))
    if roles and projects:
        return one_line(f"{node_type} serving as {join_human(roles[:2])} for {join_human(projects[:2])}.")
    if path:
        return one_line(f"{node_type} indexed from {path}.")
    return one_line(f"Indexed {node_type.lower()} in the research graph.")


def first_sentence(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    match = re.search(r"(.+?[.!?])(?:\s|$)", normalized)
    return match.group(1) if match else normalized


def one_line(value: str, max_chars: int = 150) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "..."


def join_human(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f" and {cleaned[-1]}"


def strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix) :] if value.startswith(prefix) else value


def load_node_descriptions(hub: Hub) -> dict[str, dict[str, Any]]:
    vault = obsidian_vault_path(hub)
    descriptions: dict[str, dict[str, Any]] = {}
    descriptions.update(load_note_descriptions(vault / "Projects", "project", ["Current State", "Summary"], allow_body_fallback=False))
    descriptions.update(load_note_descriptions(vault / "Concepts", "concept", ["Definition", "Summary"], allow_body_fallback=True))
    descriptions.update(load_note_descriptions(vault / "Sources" / "Papers", "paper", ["Summary"], allow_body_fallback=False))
    descriptions.update(load_collection_descriptions(vault / "Sources" / "Collections"))
    return descriptions


def load_note_descriptions(
    directory: Path,
    prefix: str,
    section_names: list[str],
    *,
    allow_body_fallback: bool,
) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        return {}
    descriptions: dict[str, dict[str, Any]] = {}
    for path in directory.glob("*.md"):
        description = note_description_from_sections(path, section_names, allow_body_fallback=allow_body_fallback)
        if not description:
            continue
        descriptions[f"{prefix}:{safe_id(path.stem)}"] = {
            "description": description["description"],
            "path": relative_note_path(path, directory),
            "section": description["section"],
        }
    return descriptions


def load_collection_descriptions(directory: Path) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        return {}
    descriptions: dict[str, dict[str, Any]] = {}
    for path in directory.glob("*.md"):
        frontmatter, _body = read_note_parts(path)
        key = string_value(frontmatter.get("zotero_collection_key"))
        node_id = collection_node_id(path.stem, key)
        description = note_description_from_sections(path, ["Summary"], allow_body_fallback=False)
        if not description:
            continue
        descriptions[node_id] = {
            "description": description["description"],
            "path": relative_note_path(path, directory),
            "section": description["section"],
        }
    return descriptions


def note_description_from_sections(
    path: Path,
    section_names: list[str],
    *,
    allow_body_fallback: bool,
) -> dict[str, str] | None:
    if not path.is_file():
        return None
    _frontmatter, body = read_note_parts(path)
    lines = body.splitlines()
    wanted = {f"## {name}".lower(): name for name in section_names}
    for index, line in enumerate(lines):
        section = wanted.get(line.strip().lower())
        if section is None:
            continue
        description = first_content_line(lines[index + 1 :])
        if description:
            return {"description": description, "section": section}
    if allow_body_fallback:
        fallback = first_content_line(lines)
        if fallback:
            return {"description": fallback, "section": "body"}
    return None


def read_note_parts(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    frontmatter_text = text[4:end]
    frontmatter = parse_simple_frontmatter(frontmatter_text)
    return frontmatter, text[end + 4 :]


def parse_simple_frontmatter(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value:
            values[key.strip()] = value.strip("\"'")
    return values


def relative_note_path(path: Path, directory: Path) -> str:
    base = directory.parent.parent if directory.parent.name == "Sources" else directory.parent
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 4 :]


def first_content_line(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            continue
        return stripped
    return None


def mapping_value(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return clean_metadata(value)


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


def write_graph(hub: Hub, graph: dict[str, Any]) -> Path:
    graph_path = hub.path / "graph" / "graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph_with_fingerprint(hub, graph), indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
