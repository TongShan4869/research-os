import React, { memo, useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./styles.css";

const TYPE_ORDER = ["Project", "Paper", "Concept", "Collection", "Folder", "Dataset", "Figure", "Manuscript", "Codebase", "Note"];

const TYPE_THEME = {
  Project: { color: "#177d72", label: "project" },
  Paper: { color: "#2f6fed", label: "paper" },
  Concept: { color: "#8b5cf6", label: "concept" },
  Collection: { color: "#c77d36", label: "collection" },
  Folder: { color: "#657487", label: "folder" },
  Dataset: { color: "#1686a7", label: "dataset" },
  Figure: { color: "#d64d71", label: "figure" },
  Manuscript: { color: "#a855f7", label: "manuscript" },
  Codebase: { color: "#2778b8", label: "codebase" },
  Note: { color: "#64748b", label: "note" },
};

const BLOCKS = {
  zotero: {
    id: "block:zotero",
    title: "Zotero Library",
    eyebrow: "Library",
    status: "collections first",
    description: "Imported paper collections. Roles and tags act as filters over the generated graph snapshot.",
    color: TYPE_THEME.Collection.color,
  },
  wiki: {
    id: "block:wiki",
    title: "Global Wiki",
    eyebrow: "Wiki",
    status: "concept clusters",
    description: "Shared concepts and tags, overlaid by the projects that use them.",
    color: TYPE_THEME.Concept.color,
  },
  context: {
    id: "block:context",
    title: "Context Surfaces",
    eyebrow: "Files",
    status: "indexed surfaces",
    description: "Folders, datasets, figures, manuscripts, notes, and code surfaces attached to research work.",
    color: TYPE_THEME.Folder.color,
  },
};

function loadGraphData() {
  const element = document.getElementById("research-os-graph-data");
  if (!element) return { nodes: [], edges: [] };
  try {
    return JSON.parse(element.textContent || '{"nodes":[],"edges":[]}');
  } catch {
    return { nodes: [], edges: [] };
  }
}

function normalizeGraph(graph) {
  const nodes = Array.isArray(graph.nodes) ? graph.nodes.map((node) => ({
    ...node,
    searchText: searchableText(node),
  })) : [];
  const edges = Array.isArray(graph.edges) ? graph.edges : [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  return { nodes, edges, byId };
}

function searchableText(value) {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value).toLowerCase();
  if (Array.isArray(value)) return value.map(searchableText).join(" ");
  if (typeof value === "object") return Object.values(value).map(searchableText).join(" ");
  return "";
}

function nodeType(node) {
  return node?.type || "Paper";
}

function nodeTitle(node) {
  return node?.title || node?.id || "Untitled";
}

function nodeDescription(node, fallback = "Indexed item in the research graph.") {
  return node?.description || fallback;
}

function plural(count, singular, pluralText) {
  return `${count} ${count === 1 ? singular : pluralText || `${singular}s`}`;
}

function truncate(text, max = 42) {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max - 1)}...` : text;
}

function projectIdsForPaper(graph, paper) {
  const projectIds = new Set();
  for (const edge of graph.edges) {
    if (edge.target === paper.id && nodeType(graph.byId.get(edge.source)) === "Project") {
      projectIds.add(edge.source);
    }
  }
  return Array.from(projectIds);
}

function makeEdgeId(source, target, label) {
  return `${source}->${target}:${label || ""}`;
}

function buildProjectConnections(graph, visibleIds) {
  const projectNodes = graph.nodes.filter((node) => nodeType(node) === "Project" && visibleIds.has(node.id));
  const paperNodes = graph.nodes.filter((node) => nodeType(node) === "Paper" && visibleIds.has(node.id));
  const conceptNodes = graph.nodes.filter((node) => nodeType(node) === "Concept" && visibleIds.has(node.id));
  const collectionNodes = graph.nodes.filter((node) => nodeType(node) === "Collection" && visibleIds.has(node.id));

  const papersByProject = new Map(projectNodes.map((node) => [node.id, []]));
  const conceptsByProject = new Map(projectNodes.map((node) => [node.id, []]));
  const collectionsByProject = new Map(projectNodes.map((node) => [node.id, []]));

  for (const edge of graph.edges) {
    const source = graph.byId.get(edge.source);
    const target = graph.byId.get(edge.target);
    if (!source || !target) continue;
    if (!visibleIds.has(edge.source) || !visibleIds.has(edge.target)) continue;
    if (nodeType(source) === "Project" && nodeType(target) === "Paper") papersByProject.get(source.id)?.push(target);
    if (nodeType(source) === "Project" && nodeType(target) === "Concept") conceptsByProject.get(source.id)?.push(target);
    if (nodeType(source) === "Project" && nodeType(target) === "Collection") collectionsByProject.get(source.id)?.push(target);
  }

  for (const concept of conceptNodes) {
    for (const edge of graph.edges) {
      if (edge.target === concept.id && graph.byId.get(edge.source)?.type === "Project") {
        conceptsByProject.get(edge.source)?.push(concept);
      }
    }
  }

  for (const [projectId, projectPapers] of papersByProject.entries()) {
    for (const paper of projectPapers) {
      for (const edge of graph.edges) {
        if (edge.source !== paper.id) continue;
        const target = graph.byId.get(edge.target);
        if (target && nodeType(target) === "Concept" && visibleIds.has(target.id)) {
          conceptsByProject.get(projectId)?.push(target);
        }
      }
    }
  }

  const dedupeMap = (map) => {
    for (const [key, values] of map.entries()) {
      map.set(key, Array.from(new Map(values.map((item) => [item.id, item])).values()));
    }
  };
  dedupeMap(papersByProject);
  dedupeMap(conceptsByProject);
  dedupeMap(collectionsByProject);

  return { projectNodes, paperNodes, conceptNodes, collectionNodes, papersByProject, conceptsByProject, collectionsByProject };
}

function contextualNodes(graph, visibleIds) {
  return graph.nodes
    .filter((node) => visibleIds.has(node.id))
    .filter((node) => !["Project", "Paper", "Concept", "Collection"].includes(nodeType(node)))
    .sort((left, right) => nodeType(left).localeCompare(nodeType(right)) || nodeTitle(left).localeCompare(nodeTitle(right)));
}

function visibleGraphIds(graph, activeTypes, query) {
  const activeIds = new Set(graph.nodes.filter((node) => activeTypes.has(nodeType(node))).map((node) => node.id));
  if (!query) return activeIds;

  const matchingIds = new Set(
    graph.nodes
      .filter((node) => activeIds.has(node.id))
      .filter((node) => node.searchText.includes(query))
      .map((node) => node.id),
  );
  const visibleIds = new Set(matchingIds);

  for (const edge of graph.edges) {
    if (matchingIds.has(edge.source) && activeIds.has(edge.target)) visibleIds.add(edge.target);
    if (matchingIds.has(edge.target) && activeIds.has(edge.source)) visibleIds.add(edge.source);
  }

  return visibleIds;
}

function collectionGroups(graph, visibleIds) {
  const collections = graph.nodes.filter((node) => nodeType(node) === "Collection" && visibleIds.has(node.id));
  const byTitle = new Map(collections.map((node) => [nodeTitle(node), { collection: node, papers: [] }]));
  const byId = new Map(collections.map((node) => [node.id, byTitle.get(nodeTitle(node))]));

  function addPaper(group, paper) {
    if (!group || !paper || !visibleIds.has(paper.id)) return;
    if (!group.papers.some((item) => item.id === paper.id)) group.papers.push(paper);
  }

  const papersByProject = new Map();
  const collectionProjects = new Map();
  for (const edge of graph.edges) {
    const source = graph.byId.get(edge.source);
    const target = graph.byId.get(edge.target);
    if (!source || !target) continue;

    if (edge.type === "uses" && nodeType(source) === "Project" && nodeType(target) === "Paper") {
      if (!papersByProject.has(source.id)) papersByProject.set(source.id, []);
      papersByProject.get(source.id).push(target);
    }

    if (edge.type === "in_collection" && nodeType(source) === "Project" && nodeType(target) === "Collection") {
      if (!collectionProjects.has(target.id)) collectionProjects.set(target.id, []);
      collectionProjects.get(target.id).push(source.id);
    }

    if (edge.type === "in_collection" && nodeType(source) === "Paper" && nodeType(target) === "Collection") {
      addPaper(byId.get(target.id), source);
    }
  }

  for (const [collectionId, projectIds] of collectionProjects.entries()) {
    const group = byId.get(collectionId);
    for (const projectId of projectIds) {
      for (const paper of papersByProject.get(projectId) || []) addPaper(group, paper);
    }
  }

  return Array.from(byTitle.values()).sort((left, right) => nodeTitle(left.collection).localeCompare(nodeTitle(right.collection)));
}

function conceptClusters(graph, visibleIds) {
  const concepts = graph.nodes.filter((node) => nodeType(node) === "Concept" && visibleIds.has(node.id));
  const byConcept = new Map(concepts.map((node) => [nodeTitle(node).toLowerCase(), { concept: node, papers: [], projects: new Set() }]));

  for (const edge of graph.edges) {
    const source = graph.byId.get(edge.source);
    const target = graph.byId.get(edge.target);
    if (!source || !target) continue;
    if (nodeType(target) === "Concept" && byConcept.has(nodeTitle(target).toLowerCase())) {
      const cluster = byConcept.get(nodeTitle(target).toLowerCase());
      if (nodeType(source) === "Paper") cluster.papers.push(source);
      if (nodeType(source) === "Project") cluster.projects.add(source.id);
    }
  }

  return Array.from(byConcept.values()).map((cluster) => ({
    ...cluster,
    papers: Array.from(new Map(cluster.papers.map((item) => [item.id, item])).values()),
    projects: Array.from(cluster.projects),
  }));
}

function boardNode(id, position, data) {
  return { id, type: "board", position, data };
}

function boardEdge(source, target, label, options = {}) {
  return {
    id: makeEdgeId(source, target, label),
    source,
    target,
    type: "default",
    animated: Boolean(options.animated),
    label,
    labelBgPadding: [8, 4],
    labelBgBorderRadius: 6,
    className: options.focused ? "edge-focused" : "edge-muted",
    style: {
      strokeWidth: options.focused ? 1.35 : 0.8,
      stroke: options.color || "var(--edge)",
    },
  };
}

function buildBoard(graph, state) {
  const query = state.search.trim().toLowerCase();
  const activeNodeIds = new Set(graph.nodes.filter((node) => state.activeTypes.has(nodeType(node))).map((node) => node.id));
  const visibleIds = visibleGraphIds(graph, state.activeTypes, query);

  const {
    projectNodes,
    paperNodes,
    conceptNodes,
    collectionNodes,
    papersByProject,
    conceptsByProject,
  } = buildProjectConnections(graph, visibleIds);
  const collectionData = collectionGroups(graph, visibleIds);
  const wikiClusters = conceptClusters(graph, visibleIds);
  const contextNodes = contextualNodes(graph, visibleIds);

  const nodes = [];
  const edges = [];
  const renderedEntityIds = new Set();
  function addVisibleNode(node) {
    const entityId = node.data?.node?.id || node.id;
    if (renderedEntityIds.has(entityId)) return false;
    renderedEntityIds.add(entityId);
    nodes.push(node);
    return true;
  }
  const projectSpacing = Math.max(210, Math.min(280, 520 / Math.max(1, projectNodes.length)));
  const projectStart = -((projectNodes.length - 1) * projectSpacing) / 2;

  addVisibleNode(boardNode(BLOCKS.zotero.id, { x: -540, y: -110 }, {
      variant: "block",
      ...BLOCKS.zotero,
      count: plural(paperNodes.length, "paper"),
      expanded: state.expanded.has(BLOCKS.zotero.id),
    }));
  addVisibleNode(boardNode(BLOCKS.wiki.id, { x: 250, y: -110 }, {
      variant: "block",
      ...BLOCKS.wiki,
      count: plural(conceptNodes.length, "concept"),
      expanded: state.expanded.has(BLOCKS.wiki.id),
    }));
  addVisibleNode(boardNode(BLOCKS.context.id, { x: -145, y: 260 }, {
      variant: "block",
      ...BLOCKS.context,
      count: plural(contextNodes.length, "surface"),
      expanded: state.expanded.has(BLOCKS.context.id),
    }));

  projectNodes.forEach((project, index) => {
    const x = projectNodes.length === 1 ? -145 : projectStart + index * projectSpacing;
    const id = project.id;
    const paperCount = papersByProject.get(id)?.length || 0;
    const conceptCount = conceptsByProject.get(id)?.length || 0;
    addVisibleNode(boardNode(id, { x, y: -10 }, {
      variant: "project",
      node: project,
      title: nodeTitle(project),
      eyebrow: "Project",
      status: project.metadata?.status || "active",
      description: nodeDescription(project),
      color: TYPE_THEME.Project.color,
      expanded: state.expanded.has(id),
    }));

    if (paperCount) edges.push(boardEdge(BLOCKS.zotero.id, id, plural(paperCount, "paper"), { color: TYPE_THEME.Collection.color, focused: state.focusId === BLOCKS.zotero.id || state.focusId === id }));
    if (conceptCount) edges.push(boardEdge(BLOCKS.wiki.id, id, plural(conceptCount, "concept"), { color: TYPE_THEME.Concept.color, focused: state.focusId === BLOCKS.wiki.id || state.focusId === id }));
    const projectContextNodes = contextNodes.filter((contextNode) => graph.edges.some((edge) => edge.source === id && edge.target === contextNode.id));
    if (projectContextNodes.length) {
      edges.push(boardEdge(id, BLOCKS.context.id, plural(projectContextNodes.length, "surface"), {
        color: TYPE_THEME.Folder.color,
        focused: state.focusId === BLOCKS.context.id || state.focusId === id,
      }));
    }
  });

  if (state.expanded.has(BLOCKS.zotero.id)) {
    collectionData.forEach((group, index) => {
      const itemId = `library:${group.collection.id}`;
      const itemExpanded = state.expanded.has(itemId);
      const y = 120 + index * (itemExpanded ? 320 : 82);
      addVisibleNode(boardNode(itemId, { x: -660, y }, {
        variant: "cluster",
        node: group.collection,
        title: nodeTitle(group.collection),
        eyebrow: "Collection",
        status: plural(group.papers.length, "paper"),
        description: nodeDescription(group.collection),
        color: TYPE_THEME.Collection.color,
        expanded: itemExpanded,
        expandable: true,
      }));
      edges.push(boardEdge(BLOCKS.zotero.id, itemId, group.papers.length ? String(group.papers.length) : "", { color: TYPE_THEME.Collection.color }));

      if (itemExpanded) {
        group.papers.forEach((paper, paperIndex) => {
          const paperId = `${itemId}:paper:${paper.id}`;
          const added = addVisibleNode(boardNode(paperId, { x: -660 + (paperIndex % 2) * 170, y: y + 115 + Math.floor(paperIndex / 2) * 52 }, {
            variant: "pill",
            node: paper,
            title: nodeTitle(paper),
            eyebrow: "Paper",
            color: TYPE_THEME.Paper.color,
          }));
          if (added) {
            edges.push(boardEdge(itemId, paperId, "", { color: TYPE_THEME.Paper.color }));
            for (const projectId of projectIdsForPaper(graph, paper)) {
              if (visibleIds.has(projectId)) {
                edges.push(boardEdge(projectId, paperId, "", {
                  color: TYPE_THEME.Paper.color,
                  focused: state.focusId === projectId || state.focusId === paperId,
                }));
              }
            }
          }
        });
      }
    });
  }

  if (state.expanded.has(BLOCKS.wiki.id)) {
    wikiClusters.forEach((cluster, index) => {
      const itemId = `wiki:${cluster.concept.id}`;
      const y = 120 + index * 76;
      addVisibleNode(boardNode(itemId, { x: 560, y }, {
        variant: "cluster",
        node: cluster.concept,
        title: nodeTitle(cluster.concept),
        eyebrow: "Concept",
        status: plural(cluster.projects.length, "project"),
        description: nodeDescription(cluster.concept),
        color: TYPE_THEME.Concept.color,
      }));
      edges.push(boardEdge(BLOCKS.wiki.id, itemId, cluster.projects.length ? String(cluster.projects.length) : "", { color: TYPE_THEME.Concept.color }));
      for (const projectId of cluster.projects) {
        if (visibleIds.has(projectId)) {
          edges.push(boardEdge(itemId, projectId, "", {
            color: TYPE_THEME.Concept.color,
            focused: state.focusId === itemId || state.focusId === projectId,
          }));
        }
      }
    });
  }

  if (state.expanded.has(BLOCKS.context.id)) {
    contextNodes.forEach((contextNode, index) => {
      const contextId = `context:${contextNode.id}`;
      const x = -320 + (index % 3) * 210;
      const y = 430 + Math.floor(index / 3) * 74;
      const theme = TYPE_THEME[nodeType(contextNode)] || TYPE_THEME.Folder;
      addVisibleNode(boardNode(contextId, { x, y }, {
        variant: "pill",
        node: contextNode,
        title: nodeTitle(contextNode),
        eyebrow: nodeType(contextNode),
        description: nodeDescription(contextNode),
        color: theme.color,
      }));
      edges.push(boardEdge(BLOCKS.context.id, contextId, "", { color: theme.color }));
      for (const edge of graph.edges) {
        if (edge.target === contextNode.id && visibleIds.has(edge.source)) {
          edges.push(boardEdge(edge.source, contextId, edge.type === "attached_folder" ? "" : edge.type, {
            color: theme.color,
            focused: state.focusId === edge.source || state.focusId === contextId,
          }));
        }
      }
    });
  }

  if (state.focusId) {
    const focusNeighbors = new Set([state.focusId]);
    for (const edge of edges) {
      if (edge.source === state.focusId) focusNeighbors.add(edge.target);
      if (edge.target === state.focusId) focusNeighbors.add(edge.source);
    }
    for (const node of nodes) {
      node.data.dimmed = !focusNeighbors.has(node.id);
    }
  }

  const counts = {
    nodes: graph.nodes.length,
    edges: graph.edges.length,
    visibleNodes: visibleIds.size,
    activeNodes: activeNodeIds.size,
    projects: projectNodes.length,
    papers: paperNodes.length,
    concepts: conceptNodes.length,
    collections: collectionNodes.length,
    context: contextNodes.length,
  };

  return { nodes, edges, counts, visibleIds };
}

const BoardNode = memo(function BoardNode({ id, data, selected }) {
  const variant = data.variant || "card";
  const canExpand = variant === "block" || variant === "project" || data.expandable;
  const expandLabel = variant === "project"
    ? (data.expanded ? "context open" : "open context")
    : (data.expanded ? "expanded" : "click to expand");
  const classes = ["board-node", `node-${variant}`];
  if (selected) classes.push("selected");
  if (data.dimmed) classes.push("dimmed");
  if (data.expanded) classes.push("expanded");

  return (
    <div className={classes.join(" ")} style={{ "--rail": data.color }}>
      <Handle type="target" position={Position.Top} className="node-handle" />
      <Handle type="source" position={Position.Bottom} className="node-handle" />
      <Handle type="target" position={Position.Left} className="node-handle side" />
      <Handle type="source" position={Position.Right} className="node-handle side" />
      <div className="node-rail" />
      <div className="node-content">
        <div className="node-meta">
          <span>{data.eyebrow}</span>
          <code>{data.status || data.count || TYPE_THEME[nodeType(data.node)]?.label || "node"}</code>
        </div>
        <div className="node-title">{truncate(data.title, variant === "pill" ? 32 : 52)}</div>
        {variant !== "pill" && (
          <div className="node-description">{truncate(data.description || nodeDescription(data.node), 118)}</div>
        )}
        {variant !== "pill" && (
          <div className="node-footer">
            <span>{data.count || data.node?.id}</span>
            {canExpand ? <span>{expandLabel}</span> : <span>select for details</span>}
          </div>
        )}
      </div>
    </div>
  );
});

function FitController({ fitSignal }) {
  const flow = useReactFlow();
  useEffect(() => {
    const timer = window.setTimeout(() => flow.fitView({ padding: 0.18, duration: 420, maxZoom: 1.1 }), 30);
    return () => window.clearTimeout(timer);
  }, [fitSignal, flow]);
  return null;
}

function GraphSnapshot({ counts }) {
  return (
    <section className="graph-snapshot">
      <h3>Graph Snapshot</h3>
      <div className="snapshot-grid">
        <div><strong>{counts.visibleNodes}</strong><span>Shown</span></div>
        <div><strong>{counts.activeNodes}</strong><span>In Filters</span></div>
        <div><strong>{counts.nodes}</strong><span>Nodes</span></div>
        <div><strong>{counts.edges}</strong><span>Edges</span></div>
        <div><strong>{counts.projects}</strong><span>Projects</span></div>
        <div><strong>{counts.papers}</strong><span>Papers</span></div>
        <div><strong>{counts.concepts}</strong><span>Concepts</span></div>
        <div><strong>{counts.collections}</strong><span>Collections</span></div>
        <div><strong>{counts.context}</strong><span>Surfaces</span></div>
      </div>
    </section>
  );
}

function Inspector({ selected, graph, counts, onToggleExpanded, onFocus, focusId }) {
  if (!selected) {
    return (
      <aside className="inspector">
        <h2>Select a card</h2>
        <p>Details, links, and preview chips appear here while the board stays in place.</p>
        <GraphSnapshot counts={counts} />
      </aside>
    );
  }

  const data = selected.data || {};
  const canExpand = data.variant === "block" || data.variant === "project" || data.expandable;
  const expandAction = data.variant === "project"
    ? (data.expanded ? "Close Context" : "Open Context")
    : (data.expanded ? "Collapse" : "Expand");
  const sourceNode = data.node;
  const realId = sourceNode?.id || selected.id;
  const neighbors = graph.edges
    .filter((edge) => edge.source === realId || edge.target === realId)
    .map((edge) => ({
      edge,
      node: graph.byId.get(edge.source === realId ? edge.target : edge.source),
    }))
    .filter((item) => item.node)
    .slice(0, 10);

  return (
    <aside className="inspector">
      <p className="inspector-eyebrow">{data.eyebrow || nodeType(sourceNode)}</p>
      <h2>{data.title || nodeTitle(sourceNode)}</h2>
      <p className="inspector-description">{data.description || nodeDescription(sourceNode, sourceNode?.id || selected.id)}</p>
      <div className="inspector-actions">
        {canExpand ? <button type="button" onClick={() => onToggleExpanded(selected.id)}>{expandAction}</button> : null}
        <button type="button" onClick={() => onFocus(selected.id)}>{focusId === selected.id ? "Clear Focus" : "Focus"}</button>
      </div>
      <section>
        <h3>Metadata</h3>
        <dl>
          <dt>Type</dt>
          <dd>{data.eyebrow || nodeType(sourceNode)}</dd>
          <dt>ID</dt>
          <dd><code>{realId}</code></dd>
          {sourceNode?.metadata?.description_source?.path ? (
            <>
              <dt>Description</dt>
              <dd>
                {sourceNode.metadata.description_source.path}
                {sourceNode.metadata.description_source.section ? ` / ${sourceNode.metadata.description_source.section}` : ""}
              </dd>
            </>
          ) : null}
          {sourceNode?.metadata?.roles?.length ? (
            <>
              <dt>Roles</dt>
              <dd>{sourceNode.metadata.roles.join(", ")}</dd>
            </>
          ) : null}
          {sourceNode?.metadata?.tags?.length ? (
            <>
              <dt>Tags</dt>
              <dd>{sourceNode.metadata.tags.join(", ")}</dd>
            </>
          ) : null}
        </dl>
      </section>
      <section>
        <h3>Direct Neighbors</h3>
        {neighbors.length ? (
          <div className="preview-list">
            {neighbors.map(({ edge, node }) => (
              <div className="preview-chip" key={`${edge.source}-${edge.target}-${edge.type}`}>
                <span>{nodeType(node)}</span>
                <strong>{truncate(nodeTitle(node), 44)}</strong>
                <code>{edge.type}</code>
              </div>
            ))}
          </div>
        ) : (
          <p>No direct graph neighbors in this generated snapshot.</p>
        )}
      </section>
      <GraphSnapshot counts={counts} />
    </aside>
  );
}

function App() {
  const graph = useMemo(() => normalizeGraph(loadGraphData()), []);
  const [theme, setTheme] = useState(() => localStorage.getItem("research-os-visual-theme") || "system");
  const [inspectorWidth, setInspectorWidth] = useState(() => {
    const stored = Number(localStorage.getItem("research-os-inspector-width"));
    return Number.isFinite(stored) ? Math.min(640, Math.max(320, stored)) : 390;
  });
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(() => new Set());
  const [activeTypes, setActiveTypes] = useState(() => new Set(TYPE_ORDER.filter((type) => graph.nodes.some((node) => nodeType(node) === type))));
  const [selectedId, setSelectedId] = useState(null);
  const [focusId, setFocusId] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [positionOverrides, setPositionOverrides] = useState(() => new Map());
  const [fitSignal, setFitSignal] = useState(0);

  const boardState = useMemo(() => ({ search, expanded, activeTypes, focusId }), [search, expanded, activeTypes, focusId]);
  const board = useMemo(() => buildBoard(graph, boardState), [graph, boardState]);

  useEffect(() => {
    setNodes(board.nodes.map((node) => ({
      ...node,
      position: positionOverrides.get(node.id) || node.position,
    })));
  }, [board.nodes, positionOverrides]);

  useEffect(() => {
    if (theme === "system") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("research-os-visual-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("research-os-inspector-width", String(inspectorWidth));
  }, [inspectorWidth]);

  const selected = nodes.find((node) => node.id === selectedId) || null;
  const availableTypes = useMemo(() => TYPE_ORDER.filter((type) => graph.nodes.some((node) => nodeType(node) === type)), [graph.nodes]);

  const toggleExpanded = useCallback((id) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
        if (id.startsWith("project:")) {
          next.add(BLOCKS.zotero.id);
          next.add(BLOCKS.wiki.id);
          next.add(BLOCKS.context.id);
        }
      }
      return next;
    });
    setFitSignal((value) => value + 1);
  }, []);

  const toggleType = useCallback((type) => {
    setActiveTypes((current) => {
      const next = new Set(current);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }, []);

  const handleNodeClick = useCallback((event, node) => {
    setSelectedId(node.id);
    if (node.data?.variant !== "pill") toggleExpanded(node.id);
  }, [toggleExpanded]);

  const handleFocus = useCallback((id) => {
    setFocusId((current) => (current === id ? null : id));
  }, []);

  const handleNodesChange = useCallback((changes) => {
    setNodes((currentNodes) => applyNodeChanges(changes, currentNodes));
  }, []);

  const handleNodeDragStop = useCallback((event, node) => {
    setPositionOverrides((current) => {
      const next = new Map(current);
      next.set(node.id, node.position);
      return next;
    });
  }, []);

  const handleInspectorResize = useCallback((event) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = inspectorWidth;
    document.body.classList.add("is-resizing-inspector");

    const handlePointerMove = (moveEvent) => {
      const nextWidth = startWidth - (moveEvent.clientX - startX);
      setInspectorWidth(Math.min(640, Math.max(320, nextWidth)));
    };
    const handlePointerUp = () => {
      document.body.classList.remove("is-resizing-inspector");
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp, { once: true });
  }, [inspectorWidth]);

  const handleInspectorResizeKey = useCallback((event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const direction = event.key === "ArrowLeft" ? 1 : -1;
    setInspectorWidth((width) => Math.min(640, Math.max(320, width + direction * 24)));
  }, []);

  return (
    <div className="app-shell" style={{ "--inspector-width": `${inspectorWidth}px` }}>
      <header className="topbar">
        <div className="brand">
          <strong>Research OS</strong>
          <span>Visual Explorer</span>
        </div>
        <div className="mode-chip">Universe</div>
        <div className="mode-chip">{board.counts.visibleNodes}/{board.counts.nodes} shown</div>
        <input
          className="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search projects, papers, concepts, files"
          type="search"
        />
        <button type="button" onClick={() => setFitSignal((value) => value + 1)}>Reset View</button>
        <button type="button" className={focusId ? "active" : ""} disabled={!focusId} onClick={() => setFocusId(null)}>
          {focusId ? "Clear Focus" : "Focus Mode"}
        </button>
        <button
          type="button"
          onClick={() => setTheme(theme === "system" ? "light" : theme === "light" ? "dark" : "system")}
        >
          Theme: {theme[0].toUpperCase() + theme.slice(1)}
        </button>
        <details className="filter-menu">
          <summary>{activeTypes.size}/{availableTypes.length} Types</summary>
          <div className="filters">
            {availableTypes.map((type) => (
              <label key={type}>
                <input type="checkbox" checked={activeTypes.has(type)} onChange={() => toggleType(type)} />
                <span>{type}</span>
              </label>
            ))}
          </div>
        </details>
      </header>
      <main className="main-area">
        <div className="canvas-shell">
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={board.edges}
              nodeTypes={{ board: BoardNode }}
              onNodesChange={handleNodesChange}
              onNodeDragStop={handleNodeDragStop}
              onNodeClick={handleNodeClick}
              onPaneClick={() => setSelectedId(null)}
              fitView
              fitViewOptions={{ padding: 0.18, maxZoom: 1.05 }}
              minZoom={0.15}
              maxZoom={1.8}
              nodesDraggable
              nodesConnectable={false}
              edgesFocusable={false}
              colorMode={theme === "dark" ? "dark" : "light"}
            >
              <Background variant={BackgroundVariant.Dots} gap={16} size={1.2} color="var(--dot)" />
              <Controls />
              <MiniMap pannable zoomable nodeColor={(node) => node.data?.color || "var(--panel-strong)"} maskColor="var(--minimap-mask)" />
              <FitController fitSignal={fitSignal} />
            </ReactFlow>
          </ReactFlowProvider>
        </div>
      </main>
      <div
        aria-label="Resize details panel"
        className="inspector-resizer"
        onPointerDown={handleInspectorResize}
        onKeyDown={handleInspectorResizeKey}
        role="separator"
        tabIndex={0}
      />
      <Inspector
        selected={selected}
        graph={graph}
        counts={board.counts}
        focusId={focusId}
        onToggleExpanded={toggleExpanded}
        onFocus={handleFocus}
      />
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
