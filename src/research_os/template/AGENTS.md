# Research OS Agent Instructions

This folder is a Research OS hub. Treat it as an indexed research system, not just a collection of folders.

At session start:

1. Read `research-os.yaml`.
2. Read `registries/projects.yaml` and `registries/sources.yaml`.
3. Read `obsidian/starter-vault/Home.md` if it exists, or the configured Obsidian vault path from `research-os.yaml`.
4. Read `graph/graph.json` for indexed relationships when graph context is useful.
5. If setup is incomplete, offer `/research-os:onboard`.
6. Use workflow files in `workflows/` for Research OS operations.

Context resolution:

- When the user mentions a project, tag, paper, folder, concept, or role, resolve it through the registries before relying on folder names alone.
- Treat tags such as `abr` as topical/context links.
- Treat roles such as `reference_paper`, `dataset`, `analysis_output`, or `manuscript` as the job an indexed entity plays for a project.
- Use the graph and Home index to connect items that share tags, projects, concepts, roles, or explicit relations.
- Zotero is an optional metadata provider. Do not assume every paper must live in Zotero.

Safety rules:

- Do not mutate Zotero records unless the user explicitly asks.
- Do not deep-process papers automatically.
- Do not attach folders to projects on heuristic matches without confirmation.
- Preserve existing notes; prefer append/update sections over wholesale rewrites.
