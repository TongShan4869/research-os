from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research_os.config import Hub


PREFERRED_NODE_TYPES = ("Project", "Paper", "Concept", "Collection", "Folder")


def write_visual(hub: Hub, graph: dict[str, list[dict[str, Any]]]) -> Path:
    visual_path = hub.path / "visual" / "index.html"
    visual_path.parent.mkdir(parents=True, exist_ok=True)
    visual_path.write_text(render_visual_html(graph), encoding="utf-8")
    return visual_path


def script_json(value: Any) -> str:
    return (
        json.dumps(value, sort_keys=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render_visual_html(graph: dict[str, list[dict[str, Any]]]) -> str:
    graph_json = script_json(graph)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research OS Visual Explorer</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #1f2937;
      --muted: #667085;
      --line: #d0d5dd;
      --accent: #0f766e;
      --accent-soft: #ccfbf1;
      --shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
    }}
    .app {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      grid-template-rows: auto minmax(0, 1fr);
      min-height: 100vh;
    }}
    header {{
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .search {{
      flex: 1;
      min-width: 160px;
      max-width: 520px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      color: var(--muted);
    }}
    .filters label {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }}
    main {{
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      min-width: 0;
      padding: 12px;
      gap: 12px;
    }}
    .summary {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .stat {{
      min-width: 96px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .stat strong {{
      display: block;
      font-size: 18px;
      line-height: 1.1;
    }}
    .stat span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .graph-shell {{
      min-height: 520px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    svg {{
      display: block;
      width: 100%;
      height: 100%;
      min-height: 520px;
    }}
    .edge {{
      stroke: #98a2b3;
      stroke-width: 1.4;
    }}
    .node {{
      cursor: pointer;
    }}
    .node circle {{
      stroke: #ffffff;
      stroke-width: 2;
      filter: drop-shadow(0 1px 1px rgba(16, 24, 40, 0.18));
    }}
    .node text {{
      pointer-events: none;
      fill: var(--ink);
      font-size: 12px;
      font-weight: 650;
    }}
    .node.selected circle {{
      stroke: var(--accent);
      stroke-width: 4;
    }}
    aside {{
      border-left: 1px solid var(--line);
      background: var(--panel);
      padding: 16px;
      overflow: auto;
    }}
    .inspector-title {{
      margin: 0 0 4px;
      font-size: 18px;
    }}
    .inspector-subtitle {{
      margin: 0 0 16px;
      color: var(--muted);
      overflow-wrap: anywhere;
    }}
    .section {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
      margin-top: 12px;
    }}
    .section h2 {{
      margin: 0 0 8px;
      font-size: 13px;
      text-transform: uppercase;
      color: var(--muted);
    }}
    dl {{
      margin: 0;
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 6px 10px;
    }}
    dt {{
      color: var(--muted);
    }}
    dd {{
      margin: 0;
      overflow-wrap: anywhere;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin-bottom: 6px;
      overflow-wrap: anywhere;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      background: #f2f4f7;
      border-radius: 4px;
      padding: 1px 4px;
    }}
    @media (max-width: 880px) {{
      .app {{
        grid-template-columns: 1fr;
      }}
      header {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .search {{
        width: 100%;
        max-width: none;
      }}
      aside {{
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>Research OS Visual Explorer</h1>
      <input class="search" id="search" type="search" placeholder="Search graph">
      <div class="filters" id="filters" aria-label="Node type filters">
      </div>
    </header>
    <main>
      <div class="summary" id="summary"></div>
      <div class="graph-shell">
        <svg id="graph" role="img" aria-label="Research graph"></svg>
      </div>
    </main>
    <aside id="inspector" aria-label="Inspector">
      <h2 class="inspector-title">Select a node</h2>
      <p class="inspector-subtitle">Node details and direct neighbors appear here.</p>
    </aside>
  </div>
  <script>
    const graphData = {graph_json};
    const preferredNodeTypes = {json.dumps(list(PREFERRED_NODE_TYPES))};
    const nodeTypes = deriveNodeTypes(graphData.nodes);
    const colors = {{
      Project: "#0f766e",
      Paper: "#2563eb",
      Concept: "#7c3aed",
      Collection: "#b45309",
      Folder: "#475467"
    }};
    const state = {{
      search: "",
      activeTypes: new Set(nodeTypes),
      selectedId: null
    }};
    const svg = document.getElementById("graph");
    const summary = document.getElementById("summary");
    const inspector = document.getElementById("inspector");
    const searchInput = document.getElementById("search");
    const filters = document.getElementById("filters");

    searchInput.addEventListener("input", function (event) {{
      state.search = event.target.value.trim().toLowerCase();
      draw();
    }});

    renderFilters();

    function renderFilters() {{
      filters.innerHTML = nodeTypes.map(function (nodeType) {{
        return '<label><input type="checkbox" value="' + escapeHtml(nodeType) + '" checked> ' +
          escapeHtml(nodeType) + '</label>';
      }}).join("");
      Array.from(filters.querySelectorAll("input")).forEach(function (input) {{
        input.addEventListener("change", function () {{
          if (input.checked) {{
            state.activeTypes.add(input.value);
          }} else {{
            state.activeTypes.delete(input.value);
          }}
          draw();
        }});
      }});
    }}

    function deriveNodeTypes(nodes) {{
      const discovered = new Set(nodes.map(function (node) {{ return node.type || "Paper"; }}));
      const preferred = preferredNodeTypes.filter(function (nodeType) {{ return discovered.has(nodeType); }});
      const custom = Array.from(discovered)
        .filter(function (nodeType) {{ return !preferredNodeTypes.includes(nodeType); }})
        .sort(function (left, right) {{ return left.localeCompare(right); }});
      return preferred.concat(custom);
    }}

    function visibleNodes() {{
      return graphData.nodes.filter(function (node) {{
        const type = node.type || "Paper";
        const matchesType = state.activeTypes.has(type);
        const matchesSearch = !state.search || JSON.stringify(node).toLowerCase().includes(state.search);
        return matchesType && matchesSearch;
      }});
    }}

    function visibleEdges(nodeIds) {{
      return graphData.edges.filter(function (edge) {{
        return nodeIds.has(edge.source) && nodeIds.has(edge.target);
      }});
    }}

    function draw() {{
      const nodes = visibleNodes();
      const nodeIds = new Set(nodes.map(function (node) {{ return node.id; }}));
      const edges = visibleEdges(nodeIds);
      if (state.selectedId && !nodeIds.has(state.selectedId)) {{
        state.selectedId = null;
      }}
      renderSummary(nodes, edges);
      renderGraph(nodes, edges);
      renderInspector();
    }}

    function renderSummary(nodes, edges) {{
      const counts = Object.fromEntries(nodeTypes.map(function (type) {{ return [type, 0]; }}));
      nodes.forEach(function (node) {{
        const type = node.type || "Paper";
        counts[type] = (counts[type] || 0) + 1;
      }});
      const stats = [
        ["Nodes", nodes.length],
        ["Edges", edges.length]
      ].concat(nodeTypes.map(function (type) {{ return [type, counts[type] || 0]; }}));
      summary.innerHTML = stats.map(function (stat) {{
        return '<div class="stat"><strong>' + escapeHtml(String(stat[1])) + '</strong><span>' + escapeHtml(stat[0]) + '</span></div>';
      }}).join("");
    }}

    function renderGraph(nodes, edges) {{
      const width = svg.clientWidth || 900;
      const height = svg.clientHeight || 540;
      svg.setAttribute("viewBox", "0 0 " + width + " " + height);
      svg.innerHTML = "";

      if (!nodes.length) {{
        const empty = makeSvg("text", {{ x: width / 2, y: height / 2, "text-anchor": "middle", fill: "#667085" }});
        empty.textContent = "No matching nodes";
        svg.appendChild(empty);
        return;
      }}

      const positions = layout(nodes, width, height);
      edges.forEach(function (edge) {{
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        if (!source || !target) return;
        svg.appendChild(makeSvg("line", {{
          class: "edge",
          x1: source.x,
          y1: source.y,
          x2: target.x,
          y2: target.y
        }}));
      }});

      nodes.forEach(function (node) {{
        const point = positions.get(node.id);
        const group = makeSvg("g", {{
          class: "node" + (node.id === state.selectedId ? " selected" : ""),
          transform: "translate(" + point.x + " " + point.y + ")",
          tabindex: "0"
        }});
        group.addEventListener("click", function () {{
          state.selectedId = node.id;
          draw();
        }});
        group.addEventListener("keydown", function (event) {{
          if (event.key === "Enter" || event.key === " ") {{
            event.preventDefault();
            state.selectedId = node.id;
            draw();
          }}
        }});
        group.appendChild(makeSvg("circle", {{
          r: 15,
          fill: colors[node.type] || "#475467"
        }}));
        const title = shortLabel(node.title || node.id);
        const text = makeSvg("text", {{ x: 0, y: 31, "text-anchor": "middle" }});
        text.textContent = title;
        group.appendChild(text);
        svg.appendChild(group);
      }});
    }}

    function layout(nodes, width, height) {{
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.max(80, Math.min(width, height) * 0.36);
      const positions = new Map();
      nodes.forEach(function (node, index) {{
        const angle = nodes.length === 1 ? -Math.PI / 2 : (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
        positions.set(node.id, {{
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        }});
      }});
      return positions;
    }}

    function renderInspector() {{
      const node = graphData.nodes.find(function (item) {{ return item.id === state.selectedId; }});
      if (!node) {{
        inspector.innerHTML = '<h2 class="inspector-title">Select a node</h2><p class="inspector-subtitle">Node details and direct neighbors appear here.</p>';
        return;
      }}
      const metadata = node.metadata && typeof node.metadata === "object" ? node.metadata : {{}};
      const neighbors = directNeighbors(node.id);
      inspector.innerHTML =
        '<h2 class="inspector-title">' + escapeHtml(node.title || node.id) + '</h2>' +
        '<p class="inspector-subtitle"><code>' + escapeHtml(node.id) + '</code></p>' +
        '<div class="section"><h2>Node</h2><dl>' +
        '<dt>Type</dt><dd>' + escapeHtml(node.type || "") + '</dd>' +
        '<dt>ID</dt><dd>' + escapeHtml(node.id) + '</dd>' +
        '<dt>Title</dt><dd>' + escapeHtml(node.title || "") + '</dd>' +
        '</dl></div>' +
        '<div class="section"><h2>Metadata</h2>' + renderMetadata(metadata) + '</div>' +
        '<div class="section"><h2>Neighbors</h2>' + renderNeighbors(neighbors) + '</div>';
    }}

    function directNeighbors(nodeId) {{
      return graphData.edges
        .filter(function (edge) {{ return edge.source === nodeId || edge.target === nodeId; }})
        .map(function (edge) {{
          const neighborId = edge.source === nodeId ? edge.target : edge.source;
          const neighbor = graphData.nodes.find(function (node) {{ return node.id === neighborId; }});
          return {{
            id: neighborId,
            title: neighbor ? neighbor.title : neighborId,
            type: neighbor ? neighbor.type : "",
            relation: edge.type
          }};
        }});
    }}

    function renderMetadata(metadata) {{
      const entries = Object.entries(metadata);
      if (!entries.length) return '<p class="inspector-subtitle">No metadata.</p>';
      return '<dl>' + entries.map(function (entry) {{
        return '<dt>' + escapeHtml(entry[0]) + '</dt><dd>' + escapeHtml(formatValue(entry[1])) + '</dd>';
      }}).join("") + '</dl>';
    }}

    function renderNeighbors(neighbors) {{
      if (!neighbors.length) return '<p class="inspector-subtitle">No direct neighbors.</p>';
      return '<ul>' + neighbors.map(function (neighbor) {{
        return '<li><strong>' + escapeHtml(neighbor.title || neighbor.id) + '</strong><br><code>' +
          escapeHtml(neighbor.id) + '</code><br>' + escapeHtml(neighbor.relation) + '</li>';
      }}).join("") + '</ul>';
    }}

    function formatValue(value) {{
      if (Array.isArray(value)) return value.join(", ");
      if (value && typeof value === "object") return JSON.stringify(value);
      return String(value);
    }}

    function shortLabel(value) {{
      return value.length > 28 ? value.slice(0, 25) + "..." : value;
    }}

    function escapeHtml(value) {{
      return value.replace(/[&<>"']/g, function (character) {{
        return {{
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;"
        }}[character];
      }});
    }}

    function makeSvg(tag, attributes) {{
      const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
      Object.entries(attributes).forEach(function (entry) {{
        element.setAttribute(entry[0], entry[1]);
      }});
      return element;
    }}

    window.addEventListener("resize", draw);
    draw();
  </script>
</body>
</html>
"""
