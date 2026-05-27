# Research OS Agent Instructions

This folder is a Research OS hub. Treat it as an indexed research system, not just a collection of folders.

At session start:

1. Read `research-os.yaml`.
2. Read `registries/projects.yaml`, `registries/sources.yaml`, `registries/files.yaml`, `registries/relations.yaml`, and `registries/inbox.yaml`.
3. Read `obsidian/starter-vault/Home.md` if it exists, or the configured Obsidian vault path from `research-os.yaml`.
4. Read `graph/graph.json` for indexed relationships when graph context is useful.
5. If setup is incomplete, offer `/research-os:onboard`.
6. Use workflow files in `workflows/` for Research OS operations.

Knowledge model:

- Raw sources and provider records are the immutable source of truth.
- Registries are the machine-readable control plane for projects, sources, files, relations, and pending proposals.
- The Obsidian wiki core is the LLM-maintained synthesis layer: `index.md`, `log.md`, `Synthesis/`, `Entities/`, `Concepts/`, `Claims/`, `Methods/`, `Datasets/`, and `Results/`.
- Humans curate sources and goals; the LLM maintains summaries, cross-links, index entries, and log entries when workflows ask it to.

Context resolution:

- When the user mentions a project, tag, paper, folder, concept, or role, resolve it through the registries before relying on folder names alone.
- Treat tags such as `abr` as topical/context links.
- Treat roles such as `reference_paper`, `dataset`, `analysis_output`, or `manuscript` as the job an indexed entity plays for a project.
- Use the graph and Home index to connect items that share tags, projects, concepts, roles, or explicit relations.
- Prefer `research-os context <query>` when you need an agent-ready packet for a project, source, tag, or file.
- Use `research-os scan --hub <path>` to propose local file assignments; only use `--apply` when the user wants pending inbox proposals written.
- Use `research-os confirm-proposal <proposal-id> --hub <path>` only after the user confirms one pending proposal should become a file registry entry.
- Use `workflows/integrate-source.md` for confirmed Stage 2 wiki integration from `wiki/inbox.md`.
- Zotero is an optional metadata provider. Do not assume every paper must live in Zotero.

Safety rules:

- Do not mutate Zotero records unless the user explicitly asks.
- Do not deep-process papers automatically.
- Do not attach folders to projects on heuristic matches without confirmation.
- Do not promote inbox proposals into confirmed registry entries without confirmation.
- Preserve existing notes; prefer append/update sections over wholesale rewrites.
