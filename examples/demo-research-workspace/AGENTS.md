# Research OS Demo Agent Instructions

This folder is a demo Research OS hub. Treat it as an indexed research system, not just a collection of folders.

At session start:

1. Read `research-os.yaml`.
2. Read `registries/projects.yaml` and `registries/sources.yaml`.
3. Read `obsidian/starter-vault/Home.md` if it exists.
4. Read `graph/graph.json` for indexed relationships when graph context is useful.
5. Use `research-os validate`, `research-os status`, `research-os build-index`, and `research-os build-graph` to inspect it.

Context resolution:

- When the user mentions a project, tag, paper, folder, concept, or role, resolve it through the registries before relying on folder names alone.
- Use tags such as `abr` and roles such as `reference_paper` to connect related papers, notes, folders, and projects.
- Zotero is an optional metadata provider. Do not assume every paper must live in Zotero.
