# Research OS Development Agent Instructions

This repository builds Research OS, a local-first indexed research workspace. Treat the product as an indexing layer over projects, papers, notes, folders, data, figures, and external tools.

When working in this repository:

1. Read `research-os.yaml` only when operating inside a generated hub or demo hub.
2. Keep `src/research_os/template/AGENTS.md` and `examples/demo-research-workspace/AGENTS.md` aligned when changing hub startup behavior.
3. Use `registries/projects.yaml`, `registries/sources.yaml`, `obsidian/starter-vault/Home.md`, and `graph/graph.json` as the core indexed context surfaces.
4. When the user mentions a project, tag, paper, folder, concept, or role, resolve it through the registries before relying on folder names alone.
5. Prefer small CLI commands that validate, index, render, or report state over hidden magic.

Safety rules:

- Do not mutate Zotero records unless the user explicitly asks.
- Do not deep-process papers automatically.
- Do not attach folders to projects on heuristic matches without confirmation.
- Preserve existing notes; prefer append/update sections over wholesale rewrites.
- Keep demo/template behavior tested before pushing changes.
