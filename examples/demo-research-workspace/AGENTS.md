# Research OS Demo Agent Instructions

This folder is a demo Research OS hub. Treat it as an indexed research system, not just a collection of folders.

At session start:

1. Read `research-os.yaml`.
2. Read `registries/projects.yaml`, `registries/sources.yaml`, `registries/files.yaml`, `registries/relations.yaml`, and `registries/inbox.yaml`.
3. Read `obsidian/starter-vault/Home.md` if it exists, or the configured Obsidian vault path from `research-os.yaml`.
4. Read `graph/graph.json` for indexed relationships when graph context is useful.
5. Use `research-os validate`, `research-os status`, `research-os build-index`, and `research-os build-graph` to inspect it.

Knowledge model:

- Raw sources and provider records are the immutable source of truth.
- Registries are the machine-readable control plane for projects, sources, files, relations, and pending proposals.
- The Obsidian wiki core is the LLM-maintained synthesis layer: `index.md`, `log.md`, `Synthesis/`, `Entities/`, `Concepts/`, `Claims/`, `Methods/`, `Datasets/`, and `Results/`.
- Humans curate sources and goals; the LLM maintains summaries, cross-links, index entries, and log entries when workflows ask it to.

Context resolution:

- When the user mentions a project, tag, paper, folder, concept, or role, resolve it through the registries before relying on folder names alone.
- Use tags such as `abr` and roles such as `reference_paper` to connect related papers, notes, folders, and projects.
- Prefer `research-os context <query>` when you need an agent-ready packet for the demo project or a source.
- Use `research-os scan --hub <path>` to propose local file assignments; only use `--apply` when the user wants pending inbox proposals written.
- Use `research-os confirm-proposal <proposal-id> --hub <path>` only after the user confirms one pending proposal should become a file registry entry.
- Use `workflows/integrate-source.md` for confirmed Stage 2 wiki integration from `wiki/inbox.md`.
- Zotero is an optional metadata provider. Do not assume every paper must live in Zotero.
