# Research OS Workspace Template Design

Date: 2026-05-22

## Purpose

Research OS is a local-first scientific research knowledge-base setup built around Codex, Obsidian, Zotero, and existing project folders.

It is not a single research skill package. It is an installable operating-system-style workspace template that gives Codex a durable research context to operate in. Users can add domain-specific skills later, but the base system provides the shared structure: project identity, source management, wiki conventions, graph indexing, and session continuity.

The design follows the principle behind Andrej Karpathy's LLM wiki: raw sources remain authoritative, the wiki becomes a persistent compounding artifact, and the agent maintains summaries, links, indexes, and logs so knowledge does not need to be rediscovered each session.

## Scope For V1

V1 ships a local-first, single-researcher control-plane template.

It coordinates existing tools instead of replacing them:

- Codex is the primary conversational interface.
- Obsidian is the running text-based wiki.
- Zotero is the reference and paper library.
- Project folders contain code, data, notebooks, figures, manuscripts, and analysis outputs.
- A local graph index exposes the research context across those surfaces.

The v1 deliverable is an installable template plus small CLI helper, not a full desktop app or hosted service.

## Architecture

The shippable system is a control-plane folder that references existing user locations.

```text
research-os/
  AGENTS.md
  research-os.yaml
  GETTING_STARTED.md
  registries/
    projects.yaml
    sources.yaml
  schemas/
    project.schema.yaml
    graph.schema.yaml
    note-types.yaml
  workflows/
    onboard.md
    ingest-paper.md
    deep-process-paper.md
    start-project.md
    wrap-session.md
    lint-knowledge-base.md
  graph/
    graph.json
    graph.duckdb
  obsidian/
    templates/
    starter-vault/
```

External locations are referenced in `research-os.yaml` and project registry entries:

```text
Obsidian vault  -> readable wiki, project notes, source notes, daily notes
Zotero Desktop  -> paper metadata, PDFs, citation keys, source identity
Project folders -> code, data, figures, notebooks, outputs, manuscripts
Codex           -> main interface that follows AGENTS.md and workflow files
```

Markdown remains the durable human layer. The CLI provides deterministic support for validation, graph building, project resolution, scaffolding, and Zotero checks.

## Installation

The primary installation path uses `uv`.

```bash
uv tool install research-os
research-os init ~/ResearchOS
```

Users can try it without installing:

```bash
uvx research-os init ~/ResearchOS
```

Developer install:

```bash
git clone https://github.com/research-os/research-os
cd research-os
uv tool install -e .
```

Fallback install:

```bash
pipx install research-os
```

Transparent template-only install:

```bash
git clone https://github.com/research-os/research-os-template ~/ResearchOS
```

The Python package ships the `research-os` CLI and bundles template files as package data. `research-os init` creates the hub but does not run a long terminal wizard.

## Cold Start And Onboarding

Cold start is intentionally split between a minimal CLI bootstrap and Codex-native onboarding.

First command:

```bash
uvx research-os init ~/ResearchOS
```

This creates a bootable hub containing `research-os.yaml`, `AGENTS.md`, `workflows/onboard.md`, registries, schemas, and starter template files.

The CLI then prints:

```text
Open Codex in ~/ResearchOS and run:
/research-os:onboard
```

Natural-language fallback:

```text
Initialize my Research OS workspace.
```

Both triggers use the same workflow: `workflows/onboard.md`.

Codex conducts the onboarding conversation. The CLI only performs deterministic work when Codex asks it to.

Codex onboarding covers:

- Whether the user already has an Obsidian vault.
- Whether to connect an existing vault, create a starter vault, or skip Obsidian for now.
- Whether Zotero Desktop is installed and the local API is available.
- Whether Codex may inspect Zotero collections.
- Which project roots already exist.
- Whether to create the first project entry.
- Whether to install Obsidian note templates.
- Whether to create a demo project.
- Whether to build the initial graph.

Onboarding is resumable:

```text
/research-os:onboard
/research-os:status
/research-os:doctor
```

## Slash-Style Commands

The template should define slash-style commands when the user's Codex setup supports them, but the system must not depend on them. Every command also has a natural-language fallback and a workflow markdown file.

Initial command set:

```text
/research-os:onboard
/research-os:status
/research-os:new-project
/research-os:attach-folder
/research-os:ingest-paper
/research-os:deep-process-paper
/research-os:wrap-session
/research-os:build-graph
/research-os:doctor
```

The durable mechanisms are:

- `AGENTS.md`
- `research-os.yaml`
- workflow markdown files
- registries and schemas
- local CLI helpers

## Project Registry

Canonical project identity lives in `registries/projects.yaml`.

Example:

```yaml
- id: music-speech-abr
  title: Subcortical responses to music and speech
  status: active
  obsidian_note: Projects/music-speech-abr.md
  folders:
    code: /path/to/code
    data: /path/to/data
    analysis: /path/to/analysis
    figures: /path/to/figures
    manuscript: /path/to/manuscript
  zotero_collections:
    - ABR
    - Music Processing
  tags:
    - auditory-neuroscience
    - eeg
    - speech
  created: 2026-05-22
```

Projects may span multiple physical folders. A project is not assumed to be a single repository.

## Project Resolution

Codex should only enter project-specific Research OS behavior when it can resolve a project.

Resolution order:

1. Strong marker resolution: current folder or parent contains `.research-os-project.yaml`.
2. Registry path resolution: current path is under a folder listed in `registries/projects.yaml`.
3. Heuristic resolution: Codex compares folder name, README, git remote, local filenames, Obsidian project titles, and registry entries.

Heuristic matches are never applied silently. The workflow is:

```text
infer -> ask -> attach -> remember
```

If the user approves, Codex asks the CLI to write `.research-os-project.yaml` or update `projects.yaml`.

Example marker:

```yaml
workspace: /path/to/research-os
project_id: music-speech-abr
folder_kind: analysis
```

## Obsidian Wiki Model

Obsidian is the readable knowledge surface.

Recommended note families:

```text
Projects/
Sources/Papers/
Concepts/
Claims/
Methods/
Datasets/
Code/
Questions/
Results/
Daily/
Ontology/
```

Daily notes and project logs both exist:

- `Daily/YYYY-MM-DD.md` captures chronology, session summaries, and lab-notebook style records.
- Project notes and logs capture continuity, decisions, project state, next actions, and linked artifacts.

Codex updates both when a session creates durable research value.

## Zotero Integration

Zotero is the reference source of truth.

Research OS uses Zotero item keys, exported citation keys, collection names, attachment metadata, and optionally indexed full text.

Rules:

- Default work is read-only against Zotero.
- Zotero library writes require explicit user intent.
- Full-text/PDF reading is only performed when requested by the user or a workflow explicitly requires it and the user has approved that workflow.
- Source notes store both Zotero item key and citation key when available.

Default paper intake creates a lightweight source note.

Deep processing is opt-in and creates richer research objects.

## Paper Workflows

### Ingest Paper

Default path for a Zotero paper.

Outputs:

- Lightweight source note under `Sources/Papers/`.
- Zotero item key and citation key.
- Metadata, short summary, and links to relevant projects and concepts.
- Graph edges from paper to project/concepts.

### Deep Process Paper

Opt-in path.

Outputs may include:

- Claim notes.
- Evidence notes.
- Method notes.
- Dataset notes.
- Result notes.
- Limitation and contradiction notes.
- Project relevance section.
- Graph nodes and edges for those objects.

This workflow can be triggered by `/research-os:deep-process-paper` or a natural request such as "deep process this Zotero paper for my ASD speech project."

## Knowledge Graph

V1 uses a hybrid graph design.

Obsidian remains the readable source material. The hub builds a machine-readable graph index from registry entries, markdown frontmatter, links, Zotero keys, and project manifests.

Core research graph node types:

```text
Project
Paper
Concept
Claim
Evidence
Method
Dataset
CodeArtifact
Question
Result
```

Full ontology overlay node types:

```text
Field
Subfield
Person
Institution
Venue
Theory
Protocol
Tool
Task
Decision
Output
TimelineEvent
```

The research graph is required. The full ontology is an optional big-picture overlay that can grow over time.

Primary edge types:

```text
project uses paper
paper supports claim
paper introduces method
project produces result
result uses dataset
code analyzes dataset
claim relates_to concept
question motivates project
method implemented_by code
ontology_node contextualizes research_node
```

Graph outputs:

```text
graph/graph.json
graph/graph.duckdb
```

`graph.json` is required in v1. `graph.duckdb` is optional and only created when the CLI is run with a graph database option.

## CLI Responsibilities

The CLI is the deterministic helper layer. It is not the main user interface.

Initial commands:

```text
research-os init <path>
research-os status
research-os validate
research-os doctor
research-os resolve-project <path>
research-os attach-folder <project-id> <path> --kind <kind>
research-os new-project <id>
research-os build-graph
research-os zotero-status
research-os zotero-sync
```

Codex calls these commands inside workflows. Users may also run them manually.

The CLI should avoid clever interpretation. It should validate, scaffold, parse, serialize, and report actionable blockers.

## Codex Session Behavior

Inside Research OS hub mode:

```text
1. Detect research-os.yaml.
2. Read AGENTS.md.
3. Read research-os.yaml and registry summaries.
4. Offer status or onboarding if setup is incomplete.
5. Use workflows for user-requested operations.
```

Inside registered project mode:

```text
1. Resolve active project.
2. Read relevant project registry entry.
3. Read project note, project log, daily note, and graph slice.
4. Work in project folder normally.
5. Update project log and daily note when research state changes.
6. Run validate/build-graph after note, registry, or schema changes.
```

Outside Research OS:

```text
Codex behaves normally.
```

## Activation And Safety

Activation paths:

```text
1. Hub mode: current folder contains research-os.yaml.
2. Project mode: current folder or parent contains .research-os-project.yaml.
3. Registry path mode: current path is under a registered project folder.
4. Uncertain mode: Codex suspects a match and must ask before attaching.
```

Safety rules:

- Never mutate Zotero records unless explicitly requested.
- Never deep-process a paper automatically.
- Never attach a folder to a project without confirmation unless marker/path match is exact.
- Never overwrite Obsidian notes without preserving existing content.
- Prefer append/update sections over rewriting notes wholesale.
- Run validation after registry, note-schema, or graph-relevant changes.
- Explain blockers by naming the exact missing gate: no hub, bad config, missing vault, Zotero unavailable, unresolved project, invalid schema, or unsafe write.

## Open-Source Deliverables

The public repo should include:

```text
research-os/
  cli/
    research_os/
  template/
    AGENTS.md
    research-os.yaml.example
    GETTING_STARTED.md
    registries/
    schemas/
    workflows/
    obsidian/
    graph/
  examples/
    demo-research-workspace/
  docs/
    quickstart.md
    concepts.md
    installation.md
    codex.md
    obsidian.md
    zotero.md
    project-folders.md
    graph.md
```

Public package contents:

- Python CLI package installable by `uv tool install research-os`.
- Bundled workspace template.
- Obsidian note templates.
- Workflow markdown files.
- Demo workspace.
- Documentation.
- Tests for initialization, validation, project resolution, graph building, and Zotero-unavailable behavior.

## Validation And Tests

V1 should test:

- `research-os init` creates a valid hub.
- `research-os validate` catches missing paths, invalid YAML, and schema errors.
- `research-os resolve-project` works by marker, registry path, and uncertain heuristic result.
- `research-os build-graph` emits valid `graph.json`.
- Zotero unavailable produces a helpful blocker, not a crash.
- Obsidian vault missing produces repair instructions.
- Deep processing is opt-in.
- Existing notes are appended or updated safely.
- Demo workspace can complete the loop from init to graph build.

Demo loop:

```text
init -> configure fake vault -> register project -> ingest fake paper metadata
-> create source note -> deep-process paper -> build graph -> validate
```

## Non-Goals For V1

- Hosted sync service.
- Team/lab collaboration features.
- Full desktop app.
- Required graph database server.
- Mandatory full ontology classification for every note.
- Automatic mutation of Zotero libraries.
- Automatic deep processing of every paper.

## Design Decisions Summary

- Shippable artifact: workspace template plus local CLI.
- Primary interface: Codex.
- Primary install path: `uv tool install` or `uvx`.
- Initial activation: `research-os init`, then `/research-os:onboard` in Codex.
- Architecture: hub/control plane referencing external vault/library/project folders.
- Project identity: central `registries/projects.yaml`.
- Project resolution: marker, registry path, or confirmed heuristic attach.
- Wiki model: Obsidian-readable markdown.
- Graph model: required research graph plus optional full ontology overlay.
- Paper intake: lightweight by default; deep processing is opt-in.
- Daily running surface: daily notes plus project logs.
- CLI role: deterministic helper, not main interface.
