# Research OS Visual Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first visual explorer generated from Research OS hub graph data and linked from Obsidian `Home.md`.

**Architecture:** Enrich `graph/graph.json` from explicit registry fields, then generate a self-contained `visual/index.html` from that graph. The CLI owns generation, Obsidian links to the generated dashboard, and the first dashboard has no server, build step, network call, or external frontend dependency.

**Tech Stack:** Python 3.11, argparse, PyYAML, stdlib `json`/`html`, generated HTML/CSS/vanilla JavaScript, pytest.

---

## File Structure

- Modify `src/research_os/graph.py`: build enriched nodes and edges for projects, sources, concepts, collections, and folders.
- Create `src/research_os/visual.py`: render and write the self-contained visual explorer HTML.
- Modify `src/research_os/cli.py`: add `build-visual` command.
- Modify `src/research_os/index.py`: add a Visual Explorer section to generated Obsidian `Home.md`.
- Modify `tests/test_graph_doctor.py`: cover enriched graph nodes, metadata, and explicit edges.
- Create `tests/test_visual.py`: cover visual HTML generation and CLI behavior.
- Modify `tests/test_index.py`: cover the Visual Explorer link and graph counts in `Home.md`.
- Modify `tests/test_demo.py`: cover demo visual generation.
- Regenerate demo artifacts under `examples/demo-research-workspace/graph/graph.json`, `examples/demo-research-workspace/visual/index.html`, and `examples/demo-research-workspace/obsidian/starter-vault/Home.md`.

## Task 1: Enrich Graph Generation

**Files:**
- Modify: `src/research_os/graph.py`
- Test: `tests/test_graph_doctor.py`

- [ ] **Step 1: Write the failing graph enrichment test**

Append this test to `tests/test_graph_doctor.py`:

```python
def test_build_graph_emits_research_context_nodes_and_edges(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "status": "active",
            "obsidian_note": "Projects/auditory-demo.md",
            "folders": {"analysis": "projects/auditory-demo/analysis"},
            "zotero_collections": ["ABR"],
            "zotero_collection_keys": ["G6CDLFHD"],
            "tags": ["auditory-neuroscience"],
        }
    ]
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "citation_key": "smith2024demo",
            "zotero_item_key": "ABCD1234",
            "zotero_attachment_key": "PDF1234",
            "doi": "10.1000/demo",
            "projects": ["auditory-demo"],
            "concepts": ["auditory-brainstem-response"],
            "zotero_collections": ["ABR"],
            "roles": ["reference_paper"],
            "tags": ["abr"],
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert nodes_by_id["project:auditory-demo"]["metadata"]["tags"] == ["auditory-neuroscience"]
    assert nodes_by_id["project:auditory-demo"]["metadata"]["obsidian_note"] == "Projects/auditory-demo.md"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["citation_key"] == "smith2024demo"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["roles"] == ["reference_paper"]
    assert nodes_by_id["concept:auditory-brainstem-response"]["title"] == "auditory brainstem response"
    assert nodes_by_id["collection:ABR"]["metadata"]["zotero_collection_key"] == "G6CDLFHD"
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["path"] == "projects/auditory-demo/analysis"

    assert {"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"} in graph["edges"]
    assert {"source": "paper:smith-2024", "target": "concept:auditory-brainstem-response", "type": "has_concept"} in graph["edges"]
    assert {"source": "project:auditory-demo", "target": "collection:ABR", "type": "in_collection"} in graph["edges"]
    assert {"source": "paper:smith-2024", "target": "collection:ABR", "type": "in_collection"} in graph["edges"]
    assert {"source": "project:auditory-demo", "target": "folder:auditory-demo:analysis", "type": "attached_folder"} in graph["edges"]
```

Update the existing exact node assertions in `tests/test_graph_doctor.py` so enriched metadata does not make them brittle. In `test_build_graph_emits_project_nodes`, replace the final assertion with:

```python
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["project:auditory-demo"]["type"] == "Project"
    assert nodes_by_id["project:auditory-demo"]["title"] == "Auditory Demo"
```

In `test_build_graph_links_sources_to_projects`, replace the exact source node assertion with:

```python
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["paper:smith-2024"]["type"] == "Paper"
    assert nodes_by_id["paper:smith-2024"]["title"] == "Auditory Brainstem Responses"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_graph_doctor.py::test_build_graph_emits_research_context_nodes_and_edges -v
```

Expected: FAIL because concept, collection, folder nodes and node metadata are not generated yet.

- [ ] **Step 3: Implement enriched graph generation**

Replace `src/research_os/graph.py` with this implementation:

```python
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
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    for project in projects:
        project_id = project.get("id")
        title = project.get("title")
        if not isinstance(project_id, str) or not isinstance(title, str):
            continue
        graph_id = f"project:{project_id}"
        add_node(
            nodes,
            graph_id,
            "Project",
            title,
            metadata={
                "status": string_value(project.get("status")),
                "tags": string_list(project.get("tags")),
                "obsidian_note": string_value(project.get("obsidian_note")),
                "zotero_collections": string_list(project.get("zotero_collections")),
                "zotero_collection_keys": string_list(project.get("zotero_collection_keys")),
            },
        )
        for concept in string_list(project.get("concepts")):
            concept_id = concept_node_id(concept)
            add_node(nodes, concept_id, "Concept", concept_title(concept))
            edges.append(edge(graph_id, concept_id, "has_concept"))
        for index, collection in enumerate(string_list(project.get("zotero_collections"))):
            collection_id = collection_node_id(collection)
            collection_key = string_list(project.get("zotero_collection_keys"))
            add_node(
                nodes,
                collection_id,
                "Collection",
                collection,
                metadata={"zotero_collection_key": list_value_at(collection_key, index)},
            )
            edges.append(edge(graph_id, collection_id, "in_collection"))
        for folder_kind, folder_path in folder_items(project.get("folders")):
            folder_id = f"folder:{project_id}:{safe_id(folder_kind)}"
            add_node(
                nodes,
                folder_id,
                "Folder",
                f"{title} {folder_kind}",
                metadata={"kind": folder_kind, "path": folder_path},
            )
            edges.append(edge(graph_id, folder_id, "attached_folder"))

    for source in sources:
        source_id = source.get("id")
        source_type = source.get("type", "Paper")
        title = source.get("title")
        if not isinstance(source_id, str) or not isinstance(title, str):
            continue
        node_type = source_type if isinstance(source_type, str) else "Paper"
        add_node(
            nodes,
            source_id,
            node_type,
            title,
            metadata={
                "citation_key": string_value(source.get("citation_key")),
                "zotero_item_key": string_value(source.get("zotero_item_key")),
                "zotero_attachment_key": string_value(source.get("zotero_attachment_key")),
                "doi": string_value(source.get("doi")),
                "tags": string_list(source.get("tags")),
                "roles": string_list(source.get("roles")),
                "projects": string_list(source.get("projects")),
                "concepts": string_list(source.get("concepts")),
                "zotero_collections": string_list(source.get("zotero_collections")),
            },
        )
        for project_id in string_list(source.get("projects")):
            edges.append(edge(f"project:{project_id}", source_id, "uses"))
        for concept in string_list(source.get("concepts")):
            concept_id = concept_node_id(concept)
            add_node(nodes, concept_id, "Concept", concept_title(concept))
            edges.append(edge(source_id, concept_id, "has_concept"))
        for collection in string_list(source.get("zotero_collections")):
            collection_id = collection_node_id(collection)
            add_node(nodes, collection_id, "Collection", collection)
            edges.append(edge(source_id, collection_id, "in_collection"))

    return {"nodes": list(nodes.values()), "edges": dedupe_edges(edges)}


def add_node(
    nodes: dict[str, dict[str, Any]],
    node_id: str,
    node_type: str,
    title: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    existing = nodes.get(node_id)
    cleaned_metadata = clean_metadata(metadata or {})
    if existing is None:
        node: dict[str, Any] = {"id": node_id, "type": node_type, "title": title}
        if cleaned_metadata:
            node["metadata"] = cleaned_metadata
        nodes[node_id] = node
        return
    if cleaned_metadata:
        merged = dict(existing.get("metadata", {}))
        merged.update({key: value for key, value in cleaned_metadata.items() if value not in ("", [], None)})
        existing["metadata"] = merged


def edge(source: str, target: str, edge_type: str) -> dict[str, str]:
    return {"source": source, "target": target, "type": edge_type}


def dedupe_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for item in edges:
        key = (item["source"], item["target"], item["type"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metadata.items() if value not in ("", [], None)}


def folder_items(value: Any) -> list[tuple[str, str]]:
    if not isinstance(value, dict):
        return []
    return [(key, item) for key, item in value.items() if isinstance(key, str) and isinstance(item, str) and item]


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def string_value(value: Any) -> str:
    return value if isinstance(value, str) and value else ""


def list_value_at(values: list[str], index: int) -> str:
    return values[index] if index < len(values) else ""


def concept_node_id(value: str) -> str:
    return f"concept:{safe_id(value)}"


def collection_node_id(value: str) -> str:
    return f"collection:{safe_id(value)}"


def concept_title(value: str) -> str:
    return value.replace("-", " ")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-") or "untitled"


def write_graph(hub: Hub, graph: Graph) -> Path:
    graph_path = hub.path / "graph" / "graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return graph_path
```

- [ ] **Step 4: Run graph tests**

Run:

```bash
python -m pytest tests/test_graph_doctor.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit graph enrichment**

Run:

```bash
git add src/research_os/graph.py tests/test_graph_doctor.py
git commit -m "Enrich Research OS graph data"
```

## Task 2: Generate Self-Contained Visual Explorer

**Files:**
- Create: `src/research_os/visual.py`
- Create: `tests/test_visual.py`

- [ ] **Step 1: Write failing visual writer tests**

Create `tests/test_visual.py`:

```python
from pathlib import Path
import json

from research_os.cli import main
from research_os.config import Hub
from research_os.visual import render_visual_html, write_visual


def test_render_visual_html_embeds_graph_data():
    graph = {
        "nodes": [{"id": "project:demo", "type": "Project", "title": "Demo Project"}],
        "edges": [{"source": "project:demo", "target": "paper:demo", "type": "uses"}],
    }

    html = render_visual_html(graph)

    assert "<title>Research OS Visual Explorer</title>" in html
    assert "const graphData =" in html
    assert json.dumps(graph, sort_keys=True) in html
    assert "Project" in html
    assert "Paper" in html
    assert "Concept" in html
    assert "Collection" in html
    assert "Folder" in html


def test_write_visual_creates_visual_index(tmp_path: Path):
    hub = Hub(path=tmp_path, config={})
    graph = {"nodes": [], "edges": []}

    visual_path = write_visual(hub, graph)

    assert visual_path == tmp_path / "visual" / "index.html"
    assert visual_path.is_file()
    assert "Research OS Visual Explorer" in visual_path.read_text(encoding="utf-8")


def test_build_visual_cli_rebuilds_graph_and_writes_dashboard(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0

    exit_code = main(["build-visual", "--hub", str(hub)])

    assert exit_code == 0
    assert (hub / "graph" / "graph.json").is_file()
    html = (hub / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Auditory Demo" in html
    assert "project:auditory-demo" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_visual.py -v
```

Expected: FAIL because `research_os.visual` and `build-visual` do not exist.

- [ ] **Step 3: Implement visual HTML generation**

Create `src/research_os/visual.py`:

```python
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from research_os.config import Hub


def write_visual(hub: Hub, graph: dict[str, list[dict[str, Any]]]) -> Path:
    visual_path = hub.path / "visual" / "index.html"
    visual_path.parent.mkdir(parents=True, exist_ok=True)
    visual_path.write_text(render_visual_html(graph), encoding="utf-8")
    return visual_path


def render_visual_html(graph: dict[str, list[dict[str, Any]]]) -> str:
    graph_json = json.dumps(graph, sort_keys=True)
    escaped_graph_json = html.escape(graph_json, quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research OS Visual Explorer</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #111315;
      --panel: #191c20;
      --panel-2: #22262c;
      --text: #f4f1ea;
      --muted: #a7a095;
      --line: #38312a;
      --accent: #d7ad78;
      --project: #7cb7ff;
      --paper: #8bd9b0;
      --concept: #d7ad78;
      --collection: #c99cff;
      --folder: #f08fa3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .app {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      grid-template-rows: auto minmax(0, 1fr);
      height: 100vh;
    }}
    header {{
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: auto minmax(260px, 1fr) auto;
      gap: 16px;
      align-items: center;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(17, 19, 21, 0.96);
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 650;
      letter-spacing: 0;
    }}
    input {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #0d0f11;
      color: var(--text);
      padding: 10px 12px;
      font-size: 14px;
    }}
    .filters {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .filters button {{
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--muted);
      padding: 8px 10px;
      cursor: pointer;
    }}
    .filters button.active {{
      color: var(--text);
      border-color: var(--accent);
    }}
    main {{
      position: relative;
      min-width: 0;
      overflow: hidden;
    }}
    svg {{
      display: block;
      width: 100%;
      height: 100%;
      background:
        linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 40px 40px;
    }}
    aside {{
      overflow: auto;
      border-left: 1px solid var(--line);
      background: var(--panel);
      padding: 18px;
    }}
    .summary {{
      display: flex;
      gap: 14px;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 18px;
    }}
    .node {{
      cursor: pointer;
    }}
    .node circle {{
      stroke: rgba(255,255,255,0.64);
      stroke-width: 1.4;
    }}
    .node text {{
      fill: var(--text);
      font-size: 12px;
      paint-order: stroke;
      stroke: rgba(17, 19, 21, 0.9);
      stroke-width: 4px;
      stroke-linejoin: round;
    }}
    line {{
      stroke: rgba(215, 173, 120, 0.34);
      stroke-width: 1.2;
    }}
    .muted {{
      color: var(--muted);
    }}
    .metadata {{
      display: grid;
      gap: 10px;
      margin: 18px 0;
    }}
    .metadata div {{
      padding: 10px;
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    .metadata strong {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .neighbors {{
      display: grid;
      gap: 8px;
    }}
    .neighbor {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px;
      background: #15181b;
      cursor: pointer;
    }}
    @media (max-width: 860px) {{
      .app {{
        grid-template-columns: 1fr;
        grid-template-rows: auto 58vh auto;
        height: auto;
        min-height: 100vh;
      }}
      header {{
        grid-template-columns: 1fr;
      }}
      aside {{
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
      .filters {{
        justify-content: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>Research OS Visual Explorer</h1>
      <input id="search" type="search" aria-label="Search graph">
      <div class="filters" id="filters"></div>
    </header>
    <main>
      <svg id="graph" role="img" aria-label="Research OS graph"></svg>
    </main>
    <aside>
      <div class="summary">
        <span id="node-count"></span>
        <span id="edge-count"></span>
      </div>
      <section id="inspector">
        <h2>Select a node</h2>
        <p class="muted">Search or click a graph node to inspect its metadata and direct neighbors.</p>
      </section>
    </aside>
  </div>
  <script>
    const graphData = {escaped_graph_json};
    const types = ["Project", "Paper", "Concept", "Collection", "Folder"];
    const activeTypes = new Set(types);
    const colors = {{
      Project: "var(--project)",
      Paper: "var(--paper)",
      Concept: "var(--concept)",
      Collection: "var(--collection)",
      Folder: "var(--folder)"
    }};
    const svg = document.getElementById("graph");
    const inspector = document.getElementById("inspector");
    const search = document.getElementById("search");
    const filters = document.getElementById("filters");
    document.getElementById("node-count").textContent = `${{graphData.nodes.length}} nodes`;
    document.getElementById("edge-count").textContent = `${{graphData.edges.length}} edges`;

    for (const type of types) {{
      const button = document.createElement("button");
      button.textContent = type;
      button.className = "active";
      button.addEventListener("click", () => {{
        if (activeTypes.has(type)) {{
          activeTypes.delete(type);
          button.classList.remove("active");
        }} else {{
          activeTypes.add(type);
          button.classList.add("active");
        }}
        render();
      }});
      filters.appendChild(button);
    }}

    search.addEventListener("input", render);
    window.addEventListener("resize", render);

    function filteredNodes() {{
      const query = search.value.trim().toLowerCase();
      return graphData.nodes.filter((node) => {{
        if (!activeTypes.has(node.type)) return false;
        if (!query) return true;
        return JSON.stringify(node).toLowerCase().includes(query);
      }});
    }}

    function render() {{
      const nodes = filteredNodes();
      const visible = new Set(nodes.map((node) => node.id));
      const edges = graphData.edges.filter((item) => visible.has(item.source) && visible.has(item.target));
      const width = svg.clientWidth || 900;
      const height = svg.clientHeight || 600;
      svg.innerHTML = "";
      const positions = layout(nodes, width, height);

      for (const item of edges) {{
        const source = positions.get(item.source);
        const target = positions.get(item.target);
        if (!source || !target) continue;
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", source.x);
        line.setAttribute("y1", source.y);
        line.setAttribute("x2", target.x);
        line.setAttribute("y2", target.y);
        svg.appendChild(line);
      }}

      for (const node of nodes) {{
        const point = positions.get(node.id);
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("class", "node");
        group.addEventListener("click", () => inspect(node.id));

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", point.x);
        circle.setAttribute("cy", point.y);
        circle.setAttribute("r", node.type === "Project" ? 18 : 13);
        circle.setAttribute("fill", colors[node.type] || "var(--muted)");
        group.appendChild(circle);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", point.x + 18);
        label.setAttribute("y", point.y + 4);
        label.textContent = node.title.length > 46 ? `${{node.title.slice(0, 43)}}...` : node.title;
        group.appendChild(label);
        svg.appendChild(group);
      }}
    }}

    function layout(nodes, width, height) {{
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.max(120, Math.min(width, height) * 0.36);
      const positions = new Map();
      nodes.forEach((node, index) => {{
        if (node.type === "Project" && nodes.length > 1) {{
          positions.set(node.id, {{ x: centerX, y: centerY }});
          return;
        }}
        const angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1) - Math.PI / 2;
        positions.set(node.id, {{
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        }});
      }});
      return positions;
    }}

    function inspect(nodeId) {{
      const node = graphData.nodes.find((item) => item.id === nodeId);
      const neighbors = graphData.edges
        .filter((item) => item.source === nodeId || item.target === nodeId)
        .map((item) => {{
          const otherId = item.source === nodeId ? item.target : item.source;
          return {{ edge: item, node: graphData.nodes.find((candidate) => candidate.id === otherId) }};
        }})
        .filter((item) => item.node);
      const metadata = Object.entries(node.metadata || {{}});
      inspector.innerHTML = `
        <p class="muted">${{escapeHtml(node.type)}} · ${{escapeHtml(node.id)}}</p>
        <h2>${{escapeHtml(node.title)}}</h2>
        <div class="metadata">
          ${{metadata.map(([key, value]) => `<div><strong>${{escapeHtml(key)}}</strong>${{escapeHtml(formatValue(value))}}</div>`).join("") || "<p class='muted'>No metadata recorded.</p>"}}
        </div>
        <h3>Neighbors</h3>
        <div class="neighbors">
          ${{neighbors.map((item) => `<div class="neighbor" data-node-id="${{escapeHtml(item.node.id)}}"><strong>${{escapeHtml(item.node.title)}}</strong><br><span class="muted">${{escapeHtml(item.edge.type)}} · ${{escapeHtml(item.node.type)}}</span></div>`).join("") || "<p class='muted'>No direct neighbors.</p>"}}
        </div>
      `;
      inspector.querySelectorAll("[data-node-id]").forEach((item) => {{
        item.addEventListener("click", () => inspect(item.getAttribute("data-node-id")));
      }});
    }}

    function formatValue(value) {{
      return Array.isArray(value) ? value.join(", ") : String(value);
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    render();
  </script>
</body>
</html>
"""
```

- [ ] **Step 4: Run visual tests**

Run:

```bash
python -m pytest tests/test_visual.py -v
```

Expected: first two tests PASS, CLI test still FAIL until Task 3 adds the command.

- [ ] **Step 5: Commit visual renderer**

Run:

```bash
git add src/research_os/visual.py tests/test_visual.py
git commit -m "Add Research OS visual renderer"
```

## Task 3: Add `build-visual` CLI Command

**Files:**
- Modify: `src/research_os/cli.py`
- Test: `tests/test_visual.py`

- [ ] **Step 1: Confirm CLI test still fails for the command**

Run:

```bash
python -m pytest tests/test_visual.py::test_build_visual_cli_rebuilds_graph_and_writes_dashboard -v
```

Expected: FAIL because argparse rejects `build-visual`.

- [ ] **Step 2: Wire the command**

Modify imports in `src/research_os/cli.py`:

```python
from research_os.visual import write_visual
```

Add this parser block after the `build-index` parser block:

```python
    build_visual_parser = subparsers.add_parser("build-visual", help="Build visual/index.html from Research OS graph data.")
    add_hub_argument(build_visual_parser)
    build_visual_parser.set_defaults(handler=run_build_visual)
```

Add this handler after `run_build_index`:

```python
def run_build_visual(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        graph = build_graph(hub)
        graph_path = write_graph(hub, graph)
        visual_path = write_visual(hub, graph)
    except HubError as error:
        print(error)
        return 1
    print(f"wrote graph: {graph_path}")
    print(f"wrote visual explorer: {visual_path}")
    print(f"nodes: {len(graph['nodes'])}")
    print(f"edges: {len(graph['edges'])}")
    return 0
```

- [ ] **Step 3: Run visual CLI tests**

Run:

```bash
python -m pytest tests/test_visual.py -v
```

Expected: PASS.

- [ ] **Step 4: Run CLI help smoke test**

Run:

```bash
PYTHONPATH=src python -m research_os.cli --help
```

Expected: output includes `build-visual`.

- [ ] **Step 5: Commit CLI command**

Run:

```bash
git add src/research_os/cli.py tests/test_visual.py
git commit -m "Add build-visual command"
```

## Task 4: Add Obsidian Home Link

**Files:**
- Modify: `src/research_os/index.py`
- Modify: `tests/test_index.py`

- [ ] **Step 1: Write failing Home link test**

Append these assertions to `test_build_index_creates_home_note_from_registries` in `tests/test_index.py` after reading `text`:

```python
    assert "## Visual Explorer" in text
    assert "[Open visual explorer](../../visual/index.html)" in text
    assert "Graph: " in text
```

- [ ] **Step 2: Run index test to verify it fails**

Run:

```bash
python -m pytest tests/test_index.py::test_build_index_creates_home_note_from_registries -v
```

Expected: FAIL because the Visual Explorer section is not rendered yet.

- [ ] **Step 3: Render the Visual Explorer section**

Modify the `render_home` lines in `src/research_os/index.py` so the section appears after `# Research OS`:

```python
        "# Research OS",
        "",
        "## Visual Explorer",
        "",
        "- [Open visual explorer](../../visual/index.html)",
        f"- Graph: {graph_node_count(projects, sources)} nodes, {graph_edge_count(projects, sources)} edges",
        "",
        "## Projects",
```

Add these helper functions near the count helpers:

```python
def graph_node_count(projects: list[dict[str, Any]], sources: list[dict[str, Any]]) -> int:
    concepts = {
        concept
        for project in projects
        for concept in string_list(project.get("concepts"))
    }
    concepts.update(
        concept
        for source in sources
        for concept in string_list(source.get("concepts"))
    )
    collections = {
        collection
        for project in projects
        for collection in string_list(project.get("zotero_collections"))
    }
    collections.update(
        collection
        for source in sources
        for collection in string_list(source.get("zotero_collections"))
    )
    folders = sum(len(project.get("folders", {})) for project in projects if isinstance(project.get("folders"), dict))
    return len(projects) + len(sources) + len(concepts) + len(collections) + folders


def graph_edge_count(projects: list[dict[str, Any]], sources: list[dict[str, Any]]) -> int:
    project_concept_edges = sum(len(string_list(project.get("concepts"))) for project in projects)
    project_collection_edges = sum(len(string_list(project.get("zotero_collections"))) for project in projects)
    project_folder_edges = sum(len(project.get("folders", {})) for project in projects if isinstance(project.get("folders"), dict))
    source_project_edges = sum(len(string_list(source.get("projects"))) for source in sources)
    source_concept_edges = sum(len(string_list(source.get("concepts"))) for source in sources)
    source_collection_edges = sum(len(string_list(source.get("zotero_collections"))) for source in sources)
    return project_concept_edges + project_collection_edges + project_folder_edges + source_project_edges + source_concept_edges + source_collection_edges
```

- [ ] **Step 4: Run index tests**

Run:

```bash
python -m pytest tests/test_index.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Home link**

Run:

```bash
git add src/research_os/index.py tests/test_index.py
git commit -m "Link visual explorer from Home index"
```

## Task 5: Demo Refresh And Demo Tests

**Files:**
- Modify: `tests/test_demo.py`
- Modify generated: `examples/demo-research-workspace/graph/graph.json`
- Create generated: `examples/demo-research-workspace/visual/index.html`
- Modify generated: `examples/demo-research-workspace/obsidian/starter-vault/Home.md`

- [ ] **Step 1: Write failing demo visual test**

Append this test to `tests/test_demo.py`:

```python
def test_demo_workspace_builds_visual_explorer():
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo-research-workspace"

    assert main(["build-visual", "--hub", str(demo)]) == 0
    assert (demo / "visual" / "index.html").is_file()
    visual_html = (demo / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Research OS Visual Explorer" in visual_html
    assert "Auditory Demo Project" in visual_html
```

- [ ] **Step 2: Run demo visual test**

Run:

```bash
python -m pytest tests/test_demo.py::test_demo_workspace_builds_visual_explorer -v
```

Expected: PASS and writes `examples/demo-research-workspace/visual/index.html`.

- [ ] **Step 3: Regenerate demo graph and Home index**

Run:

```bash
PYTHONPATH=src python -m research_os.cli build-graph --hub examples/demo-research-workspace
PYTHONPATH=src python -m research_os.cli build-index --hub examples/demo-research-workspace
PYTHONPATH=src python -m research_os.cli build-visual --hub examples/demo-research-workspace
```

Expected:

```text
wrote graph: ...
wrote index: ...
wrote visual explorer: ...
```

- [ ] **Step 4: Run demo tests**

Run:

```bash
python -m pytest tests/test_demo.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit demo refresh**

Run:

```bash
git add tests/test_demo.py examples/demo-research-workspace/graph/graph.json examples/demo-research-workspace/visual/index.html examples/demo-research-workspace/obsidian/starter-vault/Home.md
git commit -m "Refresh demo visual explorer"
```

## Task 6: Final Verification And Browser Check

**Files:**
- Inspect only unless verification reveals a bug.

- [ ] **Step 1: Run full pytest**

Run:

```bash
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 2: Run compile check**

Run:

```bash
python -m compileall -q src
```

Expected: no output and exit code 0.

- [ ] **Step 3: Run CLI help check**

Run:

```bash
PYTHONPATH=src python -m research_os.cli --help
```

Expected: output includes `build-visual`.

- [ ] **Step 4: Open generated demo dashboard in browser**

Open this local file:

```text
/Users/tongshan/Documents/research-os-dev/examples/demo-research-workspace/visual/index.html
```

Expected:

- graph nodes are visible
- type filter buttons work
- search narrows the graph
- clicking a node updates the inspector
- no network access is required

- [ ] **Step 5: Inspect final git state**

Run:

```bash
git status --short
```

Expected: only intended visual explorer changes are present. The pre-existing untracked file may remain:

```text
?? examples/demo-research-workspace/obsidian/starter-vault/Untitled.base
```

- [ ] **Step 6: Commit verification fixes if needed**

If verification revealed and fixed a bug, run:

```bash
git add src tests examples/demo-research-workspace/graph/graph.json examples/demo-research-workspace/visual/index.html examples/demo-research-workspace/obsidian/starter-vault/Home.md
git commit -m "Verify visual explorer"
```

Expected: commit is created only when files changed during verification.

## Self-Review

Spec coverage:

- Enriched graph generation is covered by Task 1.
- Static dashboard generation is covered by Task 2.
- `build-visual` CLI is covered by Task 3.
- Obsidian `Home.md` link and graph count line are covered by Task 4.
- Demo regeneration is covered by Task 5.
- Full verification and browser inspection are covered by Task 6.

Deferred-marker scan:

- The plan contains no deferred markers, incomplete task references, or unbounded test instructions.

Type consistency:

- Graph nodes use `id`, `type`, `title`, and optional `metadata`.
- Graph edges use `source`, `target`, and `type`.
- The visual writer accepts `dict[str, list[dict[str, Any]]]`, matching `build_graph`.
- CLI command name is consistently `build-visual`.
