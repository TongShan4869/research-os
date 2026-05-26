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
      color-scheme: light dark;
      --bg: #eef1f4;
      --dot: rgba(17, 24, 39, 0.24);
      --dot-soft: rgba(17, 24, 39, 0.13);
      --panel: #fbfcfd;
      --panel-strong: #ffffff;
      --panel-soft: #f2f5f7;
      --ink: #111827;
      --muted: #667085;
      --line: #d2d8df;
      --line-strong: #a8b3bf;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --accent-soft: #ccfbf1;
      --chip: #eef4f4;
      --shadow: 0 18px 60px rgba(17, 24, 39, 0.10);
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --edge: rgba(82, 98, 113, 0.42);
      --edge-focus: rgba(15, 118, 110, 0.72);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f1216;
        --dot: rgba(237, 242, 247, 0.20);
        --dot-soft: rgba(237, 242, 247, 0.11);
        --panel: #171b21;
        --panel-strong: #1f242c;
        --panel-soft: #12161c;
        --ink: #f3f6f8;
        --muted: #a3adb9;
        --line: #303843;
        --line-strong: #4a5564;
        --accent: #4fd1c5;
        --accent-strong: #8ee7df;
        --accent-soft: rgba(79, 209, 197, 0.13);
        --chip: #202832;
        --shadow: 0 18px 80px rgba(0, 0, 0, 0.44);
        --edge: rgba(183, 197, 211, 0.24);
        --edge-focus: rgba(79, 209, 197, 0.76);
      }}
    }}
    html[data-theme="light"] {{
      color-scheme: light;
      --bg: #eef1f4;
      --dot: rgba(17, 24, 39, 0.24);
      --dot-soft: rgba(17, 24, 39, 0.13);
      --panel: #fbfcfd;
      --panel-strong: #ffffff;
      --panel-soft: #f2f5f7;
      --ink: #111827;
      --muted: #667085;
      --line: #d2d8df;
      --line-strong: #a8b3bf;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --accent-soft: #ccfbf1;
      --chip: #eef4f4;
      --shadow: 0 18px 60px rgba(17, 24, 39, 0.10);
      --edge: rgba(82, 98, 113, 0.42);
      --edge-focus: rgba(15, 118, 110, 0.72);
    }}
    html[data-theme="dark"] {{
      color-scheme: dark;
      --bg: #0f1216;
      --dot: rgba(237, 242, 247, 0.20);
      --dot-soft: rgba(237, 242, 247, 0.11);
      --panel: #171b21;
      --panel-strong: #1f242c;
      --panel-soft: #12161c;
      --ink: #f3f6f8;
      --muted: #a3adb9;
      --line: #303843;
      --line-strong: #4a5564;
      --accent: #4fd1c5;
      --accent-strong: #8ee7df;
      --accent-soft: rgba(79, 209, 197, 0.13);
      --chip: #202832;
      --shadow: 0 18px 80px rgba(0, 0, 0, 0.44);
      --edge: rgba(183, 197, 211, 0.24);
      --edge-focus: rgba(79, 209, 197, 0.76);
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
      grid-template-columns: minmax(0, 1fr) 360px;
      grid-template-rows: auto minmax(0, 1fr);
      height: 100dvh;
      min-height: 100vh;
      overflow: hidden;
    }}
    header {{
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: auto auto minmax(220px, 1fr) auto;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel) 94%, transparent);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 3;
    }}
    .brand {{
      min-width: 178px;
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .subtitle {{
      margin-top: 2px;
      color: var(--muted);
      font-size: 12px;
    }}
    .mode-toggle {{
      display: inline-flex;
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
    }}
    .mode-toggle button,
    .theme-toggle {{
      border: 0;
      border-radius: calc(var(--radius-sm) - 3px);
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      padding: 8px 10px;
      white-space: nowrap;
    }}
    .mode-toggle button.active,
    .theme-toggle {{
      background: var(--panel-strong);
      color: var(--ink);
      box-shadow: 0 1px 0 rgba(17, 24, 39, 0.08);
    }}
    .theme-toggle {{
      border: 1px solid var(--line);
      background: var(--panel-strong);
    }}
    .search {{
      flex: 1;
      min-width: 160px;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      font: inherit;
      color: var(--ink);
      background: var(--panel-strong);
      outline: none;
    }}
    .search:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }}
    .filters {{
      grid-column: 1 / -1;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
    }}
    .filters label {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--chip);
      padding: 6px 9px;
    }}
    .filters input {{
      accent-color: var(--accent);
    }}
    main {{
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      min-width: 0;
      min-height: 0;
      padding: 12px;
      gap: 12px;
      overflow: hidden;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
      gap: 8px;
    }}
    .stat {{
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: color-mix(in srgb, var(--panel-strong) 88%, transparent);
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
      min-height: 0;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background:
        radial-gradient(circle, var(--dot-soft) 1.35px, transparent 1.85px),
        var(--panel);
      background-size: 18px 18px, auto;
      overflow: hidden;
      box-shadow: var(--shadow);
      position: relative;
    }}
    svg {{
      display: block;
      width: 100%;
      height: 100%;
      min-height: 0;
      cursor: grab;
      touch-action: none;
      user-select: none;
    }}
    svg.panning {{
      cursor: grabbing;
    }}
    .edge {{
      fill: none;
      stroke: var(--edge);
      stroke-width: 0.85;
      stroke-linecap: round;
      opacity: 0.78;
    }}
    .edge.focused {{
      stroke: var(--edge-focus);
      stroke-width: 1.25;
      opacity: 0.95;
    }}
    .edge-label {{
      fill: var(--muted);
      font-size: 11px;
      font-weight: 700;
    }}
    .edge-label-bg {{
      fill: var(--panel-strong);
      stroke: var(--line);
      stroke-width: 1;
    }}
    .anchor-dot {{
      fill: var(--line-strong);
      opacity: 0.85;
    }}
    .category-label {{
      fill: var(--muted);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .node {{
      cursor: grab;
      transition: opacity 160ms ease;
    }}
    .node.dimmed {{
      opacity: 0.28;
    }}
    .node circle {{
      stroke: var(--panel-strong);
      stroke-width: 2;
      filter: drop-shadow(0 8px 18px rgba(16, 24, 40, 0.18));
    }}
    .node text {{
      pointer-events: none;
      fill: var(--ink);
      font-size: 12px;
      font-weight: 650;
    }}
    .node .label-bg {{
      fill: color-mix(in srgb, var(--panel-strong) 90%, transparent);
      stroke: var(--line);
      stroke-width: 1;
    }}
    .node.selected circle {{
      stroke: var(--accent);
      stroke-width: 4;
    }}
    .group-card {{
      cursor: grab;
      transition: opacity 160ms ease;
    }}
    .group-card.dimmed {{
      opacity: 0.42;
    }}
    .group-card rect.card {{
      fill: color-mix(in srgb, var(--panel-strong) 90%, transparent);
      stroke: var(--line);
      stroke-width: 1;
      filter: drop-shadow(0 18px 26px rgba(16, 24, 40, 0.14));
    }}
    .group-card rect.stripe {{
      opacity: 0.82;
    }}
    .group-card.selected rect.card {{
      stroke: var(--accent);
      stroke-width: 2;
    }}
    .group-kind {{
      fill: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .group-badge {{
      fill: var(--ink);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
    }}
    .group-title {{
      fill: var(--ink);
      font-size: 18px;
      font-weight: 720;
    }}
    .group-description,
    .group-count {{
      fill: var(--muted);
      font-size: 12px;
    }}
    aside {{
      border-left: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel) 95%, transparent);
      padding: 16px;
      min-height: 0;
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
      grid-template-columns: 110px minmax(0, 1fr);
      gap: 8px 12px;
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
      background: var(--panel-soft);
      border-radius: 4px;
      padding: 1px 4px;
    }}
    .neighbor-list {{
      list-style: none;
      padding: 0;
      display: grid;
      gap: 8px;
    }}
    .neighbor-list li {{
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
      padding: 9px 10px;
    }}
    @media (max-width: 880px) {{
      .app {{
        grid-template-columns: 1fr;
        height: auto;
        overflow: visible;
      }}
      header {{
        align-items: flex-start;
        grid-template-columns: 1fr;
      }}
      .search {{
        width: 100%;
        max-width: none;
      }}
      aside {{
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
      main {{
        overflow: visible;
      }}
      .graph-shell {{
        min-height: 460px;
      }}
      svg {{
        min-height: 460px;
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="brand">
        <h1>Research OS</h1>
        <div class="subtitle">Visual Explorer</div>
      </div>
      <div class="mode-toggle" aria-label="Map view">
        <button type="button" data-view="project" class="active">Project Map</button>
        <button type="button" data-view="category">Category Map</button>
        <button type="button" data-view="group">Group View</button>
      </div>
      <input class="search" id="search" type="search" placeholder="Search graph">
      <button class="theme-toggle" id="theme-toggle" type="button">Theme: System</button>
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
      Folder: "#475467",
      Dataset: "#0e7490",
      Figure: "#be123c",
      Manuscript: "#9333ea",
      Codebase: "#0369a1",
      Note: "#64748b"
    }};
    const groupDetails = {{
      Project: {{
        title: "Research Projects",
        kind: "Project",
        badge: "active",
        description: "Registered Research OS projects linking literature, concepts, folders, and outputs.",
        itemLabel: "projects"
      }},
      Paper: {{
        title: "Reference Papers",
        kind: "Reference",
        badge: "literature",
        description: "Zotero-backed papers and readings connected to active research work.",
        itemLabel: "papers"
      }},
      Concept: {{
        title: "Wiki Concepts",
        kind: "Wiki",
        badge: "concept",
        description: "Concept nodes, tags, and glossary terms shared across projects.",
        itemLabel: "concepts"
      }},
      Collection: {{
        title: "Source Collections",
        kind: "Source",
        badge: "Zotero",
        description: "Imported source collections that organize reference material.",
        itemLabel: "collections"
      }},
      Folder: {{
        title: "Workspace Folders",
        kind: "Local",
        badge: "files",
        description: "Attached local folders for analysis, code, data, and manuscripts.",
        itemLabel: "folders"
      }},
      Codebase: {{
        title: "Codebases",
        kind: "Code",
        badge: "repo",
        description: "Source repositories and computational work connected to projects.",
        itemLabel: "codebases"
      }},
      Manuscript: {{
        title: "Manuscripts",
        kind: "Writing",
        badge: "draft",
        description: "Drafts, papers, and authored outputs under development.",
        itemLabel: "manuscripts"
      }},
      Dataset: {{
        title: "Datasets",
        kind: "Data",
        badge: "evidence",
        description: "Structured data sources used for analysis and figures.",
        itemLabel: "datasets"
      }},
      Figure: {{
        title: "Figures",
        kind: "Output",
        badge: "visual",
        description: "Visual outputs and figure artifacts produced by the workspace.",
        itemLabel: "figures"
      }},
      Note: {{
        title: "Research Notes",
        kind: "Note",
        badge: "vault",
        description: "Obsidian notes, memos, and local research context.",
        itemLabel: "notes"
      }}
    }};
    const state = {{
      search: "",
      activeTypes: new Set(nodeTypes),
      selectedId: null,
      selectedGroup: null,
      view: "project",
      theme: loadTheme(),
      panByView: {{}},
      manualPositions: new Map(),
      drag: null,
      suppressClick: false
    }};
    const svg = document.getElementById("graph");
    let graphLayer = svg;
    const summary = document.getElementById("summary");
    const inspector = document.getElementById("inspector");
    const searchInput = document.getElementById("search");
    const filters = document.getElementById("filters");
    const themeToggle = document.getElementById("theme-toggle");

    applyTheme();
    applyView();

    searchInput.addEventListener("input", function (event) {{
      state.search = event.target.value.trim().toLowerCase();
      draw();
    }});

    document.querySelectorAll(".mode-toggle [data-view]").forEach(function (button) {{
      button.addEventListener("click", function () {{
        const nextView = button.getAttribute("data-view") || "project";
        if (nextView !== state.view) {{
          state.selectedId = null;
          state.selectedGroup = null;
        }}
        state.view = nextView;
        applyView();
        draw();
      }});
    }});

    themeToggle.addEventListener("click", function () {{
      state.theme = state.theme === "system" ? "light" : state.theme === "light" ? "dark" : "system";
      localStorage.setItem("research-os-theme", state.theme);
      applyTheme();
    }});

    svg.addEventListener("pointerdown", function (event) {{
      if (event.target.closest(".node, .group-card")) return;
      startPan(event);
    }});
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", finishPointerDrag);
    window.addEventListener("pointercancel", finishPointerDrag);

    renderFilters();

    function loadTheme() {{
      return localStorage.getItem("research-os-theme") || "system";
    }}

    function applyTheme() {{
      if (state.theme === "system") {{
        document.documentElement.removeAttribute("data-theme");
      }} else {{
        document.documentElement.setAttribute("data-theme", state.theme);
      }}
      themeToggle.textContent = "Theme: " + capitalize(state.theme);
    }}

    function applyView() {{
      document.documentElement.setAttribute("data-view", state.view);
      document.querySelectorAll(".mode-toggle [data-view]").forEach(function (item) {{
        item.classList.toggle("active", item.getAttribute("data-view") === state.view);
      }});
    }}

    function currentPan() {{
      if (!state.panByView[state.view]) {{
        state.panByView[state.view] = {{ x: 0, y: 0 }};
      }}
      return state.panByView[state.view];
    }}

    function panTransform() {{
      const pan = currentPan();
      return "translate(" + pan.x + " " + pan.y + ")";
    }}

    function positionKey(id) {{
      return state.view + ":" + id;
    }}

    function applyManualPositions(positions) {{
      Array.from(positions.keys()).forEach(function (id) {{
        const manual = state.manualPositions.get(positionKey(id));
        if (manual) positions.set(id, {{ x: manual.x, y: manual.y }});
      }});
    }}

    function setManualPosition(id, point) {{
      state.manualPositions.set(positionKey(id), {{ x: point.x, y: point.y }});
    }}

    function appendGraph(element) {{
      graphLayer.appendChild(element);
      return element;
    }}

    function svgPoint(event) {{
      const rect = svg.getBoundingClientRect();
      const viewBox = svg.viewBox.baseVal;
      const width = viewBox && viewBox.width ? viewBox.width : rect.width;
      const height = viewBox && viewBox.height ? viewBox.height : rect.height;
      return {{
        x: (event.clientX - rect.left) * width / Math.max(1, rect.width),
        y: (event.clientY - rect.top) * height / Math.max(1, rect.height)
      }};
    }}

    function graphPoint(event) {{
      const point = svgPoint(event);
      const pan = currentPan();
      return {{ x: point.x - pan.x, y: point.y - pan.y }};
    }}

    function startPan(event) {{
      event.preventDefault();
      const point = svgPoint(event);
      const pan = currentPan();
      state.drag = {{
        kind: "pan",
        startX: point.x,
        startY: point.y,
        originX: pan.x,
        originY: pan.y,
        moved: false
      }};
      svg.classList.add("panning");
    }}

    function startItemDrag(event, kind, id, point) {{
      event.preventDefault();
      event.stopPropagation();
      const cursor = graphPoint(event);
      state.drag = {{
        kind: kind,
        id: id,
        offsetX: cursor.x - point.x,
        offsetY: cursor.y - point.y,
        startX: cursor.x,
        startY: cursor.y,
        moved: false
      }};
      svg.classList.add("panning");
    }}

    function handlePointerMove(event) {{
      if (!state.drag) return;
      event.preventDefault();
      if (state.drag.kind === "pan") {{
        const point = svgPoint(event);
        const dx = point.x - state.drag.startX;
        const dy = point.y - state.drag.startY;
        if (Math.abs(dx) + Math.abs(dy) > 3) state.drag.moved = true;
        state.panByView[state.view] = {{
          x: state.drag.originX + dx,
          y: state.drag.originY + dy
        }};
        draw();
        return;
      }}
      const cursor = graphPoint(event);
      const dx = cursor.x - state.drag.startX;
      const dy = cursor.y - state.drag.startY;
      if (Math.abs(dx) + Math.abs(dy) > 3) state.drag.moved = true;
      setManualPosition(state.drag.id, {{
        x: cursor.x - state.drag.offsetX,
        y: cursor.y - state.drag.offsetY
      }});
      draw();
    }}

    function finishPointerDrag() {{
      if (!state.drag) return;
      const drag = state.drag;
      state.drag = null;
      svg.classList.remove("panning");
      state.suppressClick = true;
      if (!drag.moved) {{
        if (drag.kind === "node") {{
          state.selectedId = drag.id;
          state.selectedGroup = null;
        }} else if (drag.kind === "group") {{
          state.selectedGroup = drag.id;
          state.selectedId = null;
        }}
      }}
      draw();
      window.setTimeout(function () {{
        state.suppressClick = false;
      }}, 0);
    }}

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
      if (state.selectedGroup && !nodes.some(function (node) {{ return (node.type || "Paper") === state.selectedGroup; }})) {{
        state.selectedGroup = null;
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
      graphLayer = makeSvg("g", {{ class: "graph-viewport", transform: panTransform() }});
      svg.appendChild(graphLayer);

      if (!nodes.length) {{
        const empty = makeSvg("text", {{ x: width / 2, y: height / 2, "text-anchor": "middle", fill: "#667085" }});
        empty.textContent = "No matching nodes";
        svg.appendChild(empty);
        return;
      }}

      if (state.view === "group") {{
        renderGroupGraph(nodes, edges, width, height);
        return;
      }}

      const positions = state.view === "category"
        ? categoryLayout(nodes, width, height)
        : projectLayout(nodes, width, height);
      applyManualPositions(positions);
      if (state.view === "category") {{
        drawCategoryLabels(nodes, width);
      }}
      const focusedIds = focusedNodeIds();
      edges.forEach(function (edge) {{
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        if (!source || !target) return;
        const focused = state.selectedId && focusedIds.has(edge.source) && focusedIds.has(edge.target);
        appendGraph(makeSvg("path", {{
          class: "edge" + (focused ? " focused" : ""),
          d: curvePath(source, target)
        }}));
      }});

      nodes.forEach(function (node) {{
        const point = positions.get(node.id);
        const dimmed = state.selectedId && !focusedIds.has(node.id);
        const group = makeSvg("g", {{
          class: "node" + (node.id === state.selectedId ? " selected" : "") + (dimmed ? " dimmed" : ""),
          transform: "translate(" + point.x + " " + point.y + ")",
          tabindex: "0"
        }});
        group.addEventListener("pointerdown", function (event) {{
          startItemDrag(event, "node", node.id, point);
        }});
        group.addEventListener("click", function () {{
          if (state.suppressClick) return;
          state.selectedId = node.id;
          state.selectedGroup = null;
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
          r: node.type === "Project" ? 18 : 14,
          fill: colors[node.type] || "#64748b"
        }}));
        const label = nodeLabel(node, point, width);
        if (label.background) {{
          group.appendChild(makeSvg("rect", label.background));
        }}
        const text = makeSvg("text", label.textAttributes);
        const title = shortLabel(node.title || node.id, label.maxLength);
        text.textContent = title;
        group.appendChild(text);
        appendGraph(group);
      }});
    }}

    function projectLayout(nodes, width, height) {{
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.max(92, Math.min(width, height) * 0.36);
      const positions = new Map();
      const projects = nodes.filter(function (node) {{ return node.type === "Project"; }});
      const others = nodes.filter(function (node) {{ return node.type !== "Project"; }});
      projects.forEach(function (node, index) {{
        const offset = (index - (projects.length - 1) / 2) * 62;
        positions.set(node.id, {{ x: centerX + offset, y: centerY - 20 }});
      }});
      others.forEach(function (node, index) {{
        const angle = others.length === 1 ? -Math.PI / 2 : (Math.PI * 2 * index) / others.length - Math.PI / 2;
        positions.set(node.id, {{
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        }});
      }});
      if (!projects.length) {{
        nodes.forEach(function (node, index) {{
          const angle = nodes.length === 1 ? -Math.PI / 2 : (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
          positions.set(node.id, {{
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius
          }});
        }});
      }}
      return positions;
    }}

    function categoryLayout(nodes, width, height) {{
      const positions = new Map();
      const grouped = nodeTypes
        .map(function (type) {{ return [type, nodes.filter(function (node) {{ return (node.type || "Paper") === type; }})]; }})
        .filter(function (entry) {{ return entry[1].length > 0; }});
      const columns = Math.max(1, grouped.length);
      const columnWidth = width / columns;
      const top = 86;
      const bottom = 66;
      grouped.forEach(function (entry, columnIndex) {{
        const items = entry[1];
        const x = columnWidth * columnIndex + columnWidth / 2;
        items.forEach(function (node, itemIndex) {{
          const usableHeight = Math.max(160, height - top - bottom);
          const singleOffset = 0.18 + (columnIndex % 3) * 0.28;
          const step = items.length === 1 ? 0 : usableHeight / (items.length - 1);
          const y = items.length === 1 ? top + usableHeight * singleOffset : top + step * itemIndex;
          const stagger = items.length > 1 && itemIndex % 2 ? Math.min(18, columnWidth * 0.10) : 0;
          positions.set(node.id, {{ x: x - stagger, y: y }});
        }});
      }});
      return positions;
    }}

    function visibleCategoryTypes(nodes) {{
      return nodeTypes.filter(function (type) {{
        return nodes.some(function (node) {{ return (node.type || "Paper") === type; }});
      }});
    }}

    function drawCategoryLabels(nodes, width) {{
      const types = visibleCategoryTypes(nodes);
      const columnWidth = width / Math.max(1, types.length);
      types.forEach(function (type, index) {{
        const label = makeSvg("text", {{
          class: "category-label",
          x: columnWidth * index + columnWidth / 2,
          y: 36,
          "text-anchor": "middle"
        }});
        label.textContent = type;
        appendGraph(label);
      }});
    }}

    function renderGroupGraph(nodes, edges, width, height) {{
      const groups = buildGroups(nodes);
      const groupMap = new Map(groups.map(function (group) {{ return [group.type, group]; }}));
      const cardSize = groupCardSize(width);
      const positions = groupLayout(groups, width, height, cardSize);
      applyManualPositions(positions);
      const groupedEdges = groupEdges(edges, nodes);
      const focusedGroups = focusedGroupTypes(groupedEdges);

      groupedEdges.forEach(function (edge) {{
        const source = positions.get(edge.source);
        const target = positions.get(edge.target);
        if (!source || !target) return;
        const focused = state.selectedGroup && (focusedGroups.has(edge.source) || focusedGroups.has(edge.target));
        drawGroupEdge(source, target, edge.count, focused, cardSize);
      }});

      groups.forEach(function (group) {{
        const point = positions.get(group.type);
        if (!point) return;
        const dimmed = state.selectedGroup && !focusedGroups.has(group.type);
        drawGroupCard(groupMap.get(group.type), point, dimmed, cardSize);
      }});
    }}

    function buildGroups(nodes) {{
      return nodeTypes
        .map(function (type) {{
          const items = nodes.filter(function (node) {{ return (node.type || "Paper") === type; }});
          if (!items.length) return null;
          const details = groupInfo(type);
          return {{
            type: type,
            title: details.title,
            kind: details.kind,
            badge: details.badge,
            description: details.description,
            itemLabel: details.itemLabel,
            count: items.length,
            items: items
          }};
        }})
        .filter(Boolean);
    }}

    function groupCardSize(width) {{
      return {{
        width: Math.max(280, Math.min(340, width * 0.34)),
        height: 132
      }};
    }}

    function groupLayout(groups, width, height, cardSize) {{
      const positions = new Map();
      const byType = new Map(groups.map(function (group) {{ return [group.type, group]; }}));
      const preferred = [
        ["Project", width * 0.50, height * 0.20],
        ["Paper", width * 0.28, height * 0.50],
        ["Concept", width * 0.72, height * 0.50],
        ["Collection", width * 0.30, height * 0.78],
        ["Folder", width * 0.68, height * 0.78]
      ];
      preferred.forEach(function (entry) {{
        if (byType.has(entry[0])) {{
          positions.set(entry[0], clampCard({{ x: entry[1], y: entry[2] }}, cardSize.width, cardSize.height, width, height));
        }}
      }});
      const remaining = groups.filter(function (group) {{ return !positions.has(group.type); }});
      const columns = Math.min(3, Math.max(1, remaining.length));
      remaining.forEach(function (group, index) {{
        const row = Math.floor(index / columns);
        const column = index % columns;
        const x = width * (column + 1) / (columns + 1);
        const y = height * 0.28 + row * (cardSize.height + 44);
        positions.set(group.type, clampCard({{ x: x, y: y }}, cardSize.width, cardSize.height, width, height));
      }});
      return positions;
    }}

    function clampCard(point, cardWidth, cardHeight, width, height) {{
      const margin = 28;
      return {{
        x: Math.max(margin + cardWidth / 2, Math.min(width - margin - cardWidth / 2, point.x)),
        y: Math.max(54 + cardHeight / 2, Math.min(height - margin - cardHeight / 2, point.y))
      }};
    }}

    function groupEdges(edges, nodes) {{
      const nodeType = new Map(nodes.map(function (node) {{ return [node.id, node.type || "Paper"]; }}));
      const counts = new Map();
      edges.forEach(function (edge) {{
        const sourceType = nodeType.get(edge.source);
        const targetType = nodeType.get(edge.target);
        if (!sourceType || !targetType || sourceType === targetType) return;
        const key = sourceType + "->" + targetType;
        counts.set(key, {{
          source: sourceType,
          target: targetType,
          count: (counts.get(key) ? counts.get(key).count : 0) + 1
        }});
      }});
      return Array.from(counts.values());
    }}

    function drawGroupEdge(source, target, count, focused, cardSize) {{
      const start = groupAnchor(source, target, cardSize.width, cardSize.height);
      const end = groupAnchor(target, source, cardSize.width, cardSize.height);
      appendGraph(makeSvg("path", {{
        class: "edge" + (focused ? " focused" : ""),
        d: curvePath(start, end)
      }}));
      appendGraph(makeSvg("circle", {{ class: "anchor-dot", cx: start.x, cy: start.y, r: 4 }}));
      appendGraph(makeSvg("circle", {{ class: "anchor-dot", cx: end.x, cy: end.y, r: 4 }}));
      const labelText = String(count);
      const labelWidth = labelText.length * 7 + 14;
      const label = edgeLabelPoint(start, end);
      appendGraph(makeSvg("rect", {{
        class: "edge-label-bg",
        x: label.x - labelWidth / 2,
        y: label.y - 13,
        width: labelWidth,
        height: 22,
        rx: 5
      }}));
      const text = makeSvg("text", {{ class: "edge-label", x: label.x, y: label.y + 2, "text-anchor": "middle" }});
      text.textContent = labelText;
      appendGraph(text);
    }}

    function drawGroupCard(group, point, dimmed, cardSize) {{
      const width = cardSize.width;
      const height = cardSize.height;
      const x = point.x - width / 2;
      const y = point.y - height / 2;
      const selected = state.selectedGroup === group.type;
      const clipId = "group-card-clip-" + safeDomId(group.type);
      const card = makeSvg("g", {{
        class: "group-card" + (selected ? " selected" : "") + (dimmed ? " dimmed" : ""),
        transform: "translate(" + x + " " + y + ")",
        tabindex: "0"
      }});
      card.addEventListener("pointerdown", function (event) {{
        startItemDrag(event, "group", group.type, point);
      }});
      card.addEventListener("click", function () {{
        if (state.suppressClick) return;
        state.selectedGroup = group.type;
        state.selectedId = null;
        draw();
      }});
      card.addEventListener("keydown", function (event) {{
        if (event.key === "Enter" || event.key === " ") {{
          event.preventDefault();
          state.selectedGroup = group.type;
          state.selectedId = null;
          draw();
        }}
      }});
      const defs = makeSvg("defs", {{}});
      const clipPath = makeSvg("clipPath", {{ id: clipId }});
      clipPath.appendChild(makeSvg("rect", {{ x: 0, y: 0, width: width, height: height, rx: 13 }}));
      defs.appendChild(clipPath);
      card.appendChild(defs);
      card.appendChild(makeSvg("rect", {{ class: "card", x: 0, y: 0, width: width, height: height, rx: 13 }}));
      card.appendChild(makeSvg("rect", {{
        class: "stripe",
        x: 0,
        y: 0,
        width: 8,
        height: height,
        "clip-path": "url(#" + clipId + ")",
        fill: colors[group.type] || "#64748b"
      }}));
      const kind = makeSvg("text", {{ class: "group-kind", x: 22, y: 32 }});
      kind.textContent = group.kind;
      card.appendChild(kind);
      const badge = makeSvg("text", {{ class: "group-badge", x: width - 18, y: 32, "text-anchor": "end" }});
      badge.textContent = group.badge;
      card.appendChild(badge);
      const title = makeSvg("text", {{ class: "group-title", x: 22, y: 62 }});
      title.textContent = shortLabel(group.title, Math.floor((width - 44) / 9.5));
      card.appendChild(title);
      wrapText(group.description, Math.floor((width - 44) / 7.4), 2).forEach(function (line, index) {{
        const description = makeSvg("text", {{ class: "group-description", x: 22, y: 86 + index * 17 }});
        description.textContent = line;
        card.appendChild(description);
      }});
      const count = makeSvg("text", {{ class: "group-count", x: 22, y: 119 }});
      count.textContent = group.count + " " + group.itemLabel;
      card.appendChild(count);
      appendGraph(card);
    }}

    function groupAnchor(source, target, width, height) {{
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      if (Math.abs(dy) >= Math.abs(dx)) {{
        return {{ x: source.x, y: source.y + (dy >= 0 ? height / 2 : -height / 2) }};
      }}
      return {{ x: source.x + (dx >= 0 ? width / 2 : -width / 2), y: source.y }};
    }}

    function edgeLabelPoint(source, target) {{
      return {{
        x: source.x + (target.x - source.x) * 0.50,
        y: source.y + (target.y - source.y) * 0.50 - 6
      }};
    }}

    function focusedGroupTypes(groupedEdges) {{
      if (!state.selectedGroup) return new Set(nodeTypes);
      const types = new Set([state.selectedGroup]);
      groupedEdges.forEach(function (edge) {{
        if (edge.source === state.selectedGroup) types.add(edge.target);
        if (edge.target === state.selectedGroup) types.add(edge.source);
      }});
      return types;
    }}

    function groupInfo(type) {{
      return groupDetails[type] || {{
        title: type,
        kind: "Category",
        badge: "custom",
        description: "Custom Research OS category discovered from the indexed graph.",
        itemLabel: type.toLowerCase() + " nodes"
      }};
    }}

    function nodeLabel(node, point, width) {{
      if (state.view === "category") {{
        const anchorLeft = point.x > width * 0.72;
        const textX = anchorLeft ? -20 : 20;
        const categoryCount = Math.max(1, visibleCategoryTypes(visibleNodes()).length);
        const maxLength = Math.max(18, Math.min(30, Math.floor(width / categoryCount / 7)));
        const rectWidth = maxLength * 6.4 + 18;
        return {{
          maxLength: maxLength,
          textAttributes: {{
            x: textX,
            y: 4,
            "text-anchor": anchorLeft ? "end" : "start"
          }},
          background: {{
            class: "label-bg",
            x: anchorLeft ? -rectWidth - 14 : 14,
            y: -12,
            width: rectWidth,
            height: 23,
            rx: 6
          }}
        }};
      }}
      return {{
        maxLength: 28,
        textAttributes: {{ x: 0, y: 31, "text-anchor": "middle" }},
        background: null
      }};
    }}

    function curvePath(source, target) {{
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      if (Math.abs(dy) >= Math.abs(dx) * 0.72) {{
        const controlY = Math.max(34, Math.abs(dy) * 0.52);
        return "M " + source.x + " " + source.y +
          " C " + source.x + " " + (source.y + Math.sign(dy || 1) * controlY) +
          " " + target.x + " " + (target.y - Math.sign(dy || 1) * controlY) +
          " " + target.x + " " + target.y;
      }}
      const controlX = Math.max(34, Math.abs(dx) * 0.52);
      return "M " + source.x + " " + source.y +
        " C " + (source.x + Math.sign(dx || 1) * controlX) + " " + source.y +
        " " + (target.x - Math.sign(dx || 1) * controlX) + " " + target.y +
        " " + target.x + " " + target.y;
    }}

    function focusedNodeIds() {{
      if (!state.selectedId) return new Set(graphData.nodes.map(function (node) {{ return node.id; }}));
      const ids = new Set([state.selectedId]);
      graphData.edges.forEach(function (edge) {{
        if (edge.source === state.selectedId) ids.add(edge.target);
        if (edge.target === state.selectedId) ids.add(edge.source);
      }});
      return ids;
    }}

    function renderInspector() {{
      if (state.selectedGroup) {{
        renderGroupInspector(state.selectedGroup);
        return;
      }}
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

    function renderGroupInspector(type) {{
      const nodes = visibleNodes().filter(function (node) {{ return (node.type || "Paper") === type; }});
      const details = groupInfo(type);
      const nodeIds = new Set(visibleNodes().map(function (node) {{ return node.id; }}));
      const relationships = groupEdges(visibleEdges(nodeIds), visibleNodes()).filter(function (edge) {{
        return edge.source === type || edge.target === type;
      }});
      inspector.innerHTML =
        '<h2 class="inspector-title">' + escapeHtml(details.title) + '</h2>' +
        '<p class="inspector-subtitle"><code>group:' + escapeHtml(type) + '</code></p>' +
        '<div class="section"><h2>Category</h2><dl>' +
        '<dt>Type</dt><dd>' + escapeHtml(type) + '</dd>' +
        '<dt>Kind</dt><dd>' + escapeHtml(details.kind) + '</dd>' +
        '<dt>Count</dt><dd>' + escapeHtml(String(nodes.length)) + '</dd>' +
        '</dl></div>' +
        '<div class="section"><h2>Role</h2><p class="inspector-subtitle">' + escapeHtml(details.description) + '</p></div>' +
        '<div class="section"><h2>Connected Groups</h2>' + renderGroupRelationships(relationships, type) + '</div>' +
        '<div class="section"><h2>Examples</h2>' + renderGroupExamples(nodes) + '</div>';
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
      return '<ul class="neighbor-list">' + neighbors.map(function (neighbor) {{
        return '<li><strong>' + escapeHtml(neighbor.title || neighbor.id) + '</strong><br><code>' +
          escapeHtml(neighbor.id) + '</code><br>' + escapeHtml(neighbor.relation) + '</li>';
      }}).join("") + '</ul>';
    }}

    function renderGroupRelationships(relationships, type) {{
      if (!relationships.length) return '<p class="inspector-subtitle">No visible cross-category links.</p>';
      return '<ul class="neighbor-list">' + relationships.map(function (relationship) {{
        const otherType = relationship.source === type ? relationship.target : relationship.source;
        return '<li><strong>' + escapeHtml(groupInfo(otherType).title) + '</strong><br><code>' +
          escapeHtml(type + " -> " + otherType) + '</code><br>' + escapeHtml(String(relationship.count)) +
          ' visible links</li>';
      }}).join("") + '</ul>';
    }}

    function renderGroupExamples(nodes) {{
      if (!nodes.length) return '<p class="inspector-subtitle">No visible nodes in this group.</p>';
      return '<ul class="neighbor-list">' + nodes.slice(0, 8).map(function (node) {{
        return '<li><strong>' + escapeHtml(node.title || node.id) + '</strong><br><code>' +
          escapeHtml(node.id) + '</code></li>';
      }}).join("") + '</ul>';
    }}

    function formatValue(value) {{
      if (Array.isArray(value)) return value.join(", ");
      if (value && typeof value === "object") return JSON.stringify(value);
      return String(value);
    }}

    function shortLabel(value, maxLength) {{
      const limit = maxLength || 28;
      return value.length > limit ? value.slice(0, Math.max(1, limit - 3)) + "..." : value;
    }}

    function safeDomId(value) {{
      return String(value).replace(/[^a-zA-Z0-9_-]/g, "-");
    }}

    function wrapText(value, maxLength, maxLines) {{
      const words = String(value).split(" ");
      const lines = [];
      let current = "";
      words.forEach(function (word) {{
        const next = current ? current + " " + word : word;
        if (next.length > maxLength && current) {{
          lines.push(current);
          current = word;
        }} else {{
          current = next;
        }}
      }});
      if (current) lines.push(current);
      return lines.slice(0, maxLines).map(function (line, index) {{
        if (index === maxLines - 1 && lines.length > maxLines) {{
          return shortLabel(line, maxLength);
        }}
        return line;
      }});
    }}

    function capitalize(value) {{
      return value.charAt(0).toUpperCase() + value.slice(1);
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
