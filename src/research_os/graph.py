from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_os.config import Hub, load_projects, load_sources


def build_graph(hub: Hub) -> dict[str, list[dict[str, Any]]]:
    projects = load_projects(hub)
    sources = load_sources(hub)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for project in projects:
        project_id = project.get("id")
        title = project.get("title")
        if isinstance(project_id, str) and isinstance(title, str):
            nodes.append({"id": f"project:{project_id}", "type": "Project", "title": title})

    for source in sources:
        source_id = source.get("id")
        source_type = source.get("type", "Paper")
        title = source.get("title")
        if not isinstance(source_id, str) or not isinstance(title, str):
            continue
        node_type = source_type if isinstance(source_type, str) else "Paper"
        nodes.append({"id": source_id, "type": node_type, "title": title})
        for project_id in source.get("projects", []):
            if isinstance(project_id, str):
                edges.append({"source": f"project:{project_id}", "target": source_id, "type": "uses"})

    return {"nodes": nodes, "edges": edges}


def write_graph(hub: Hub, graph: dict[str, list[dict[str, Any]]]) -> Path:
    graph_path = hub.path / "graph" / "graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return graph_path
