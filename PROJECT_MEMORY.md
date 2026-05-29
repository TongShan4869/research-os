# Research OS Project Memory

Last updated: 2026-05-27

This file is the durable memory for the Research OS development repo. Future Codex sessions should read it after `AGENTS.md` before planning or implementing changes.

## Product Direction

Research OS is a local-first indexing layer for scientific research. It is not primarily a paper manager, a Zotero replacement, or an Obsidian plugin.

The core model is:

```text
project folders + Obsidian + Zotero + PDFs + analysis outputs
        -> Research OS registries
        -> Home.md + graph.json
        -> Codex can resolve project context
```

Files and apps remain where they are. Research OS indexes what they mean and how they relate.

## Key Decisions

- Research OS should manage indexed context, not physically own every file.
- Projects may start as folders, but project identity lives in `registries/projects.yaml`.
- Sources such as papers live in `registries/sources.yaml`.
- Obsidian is the human-readable wiki and graph surface.
- `Home.md` is the Obsidian project cockpit generated from registries.
- `graph/graph.json` is the machine-readable relationship graph.
- Codex uses `AGENTS.md` as the workspace startup instruction file, similar in spirit to Claude Code's `CLAUDE.md`.
- Zotero is optional. It is a metadata provider for citation keys, item keys, PDF links, collections, and bibliographic metadata.
- Zotero should remain read-only unless the user explicitly asks to mutate Zotero records.
- The future architecture should evolve from "Zotero ingest" toward "source ingest" with multiple providers.
- Zotero ingest now captures metadata-only fields such as abstract note, publication title, date, creators, and Zotero tags, then assigns explainable Research OS concepts from title/abstract/tag evidence. It still does not read PDFs/full text.
- Research OS now has the first provider-neutral control-plane slice: `files.yaml`, `relations.yaml`, `inbox.yaml`, `research-os scan`, and `research-os context`.
- Research OS applies hash/staleness discipline to existing generated surfaces: `Home.md`, `graph/graph.json`, and `visual/index.html` are stamped with input fingerprints, and `research-os context-health` reports current/stale/missing/untracked state.
- Research OS now adapts Karpathy's LLM wiki pattern: raw sources remain authoritative, registries are the machine-readable control plane, and Obsidian contains an LLM-maintained wiki core with `index.md`, `log.md`, `wiki/inbox.md`, and synthesis/entity/claim/method/dataset/result pages.

## Important Conceptual Model

Research OS should distinguish:

- **Tags**: topical/context labels, such as `abr` or `auditory-brainstem-response`.
- **Roles**: what an entity is doing in a project, such as `reference_paper`, `dataset`, `analysis_output`, or `manuscript`.
- **Relations**: explicit links between entities, such as `reference_for -> project:abr`.

Example future source shape:

```yaml
id: paper:shanSubcorticalResponsesMusic2024
type: Paper
title: Subcortical responses to music and speech are alike while cortical responses diverge
tags:
  - abr
  - auditory-brainstem-response
roles:
  - reference_paper
relations:
  - type: reference_for
    target: project:abr
provider:
  name: zotero
  key: GBEMXBSK
```

When the user mentions "ABR project", Codex should resolve context through the registries and graph, not folder names alone.

Relevant context should include:

- the matching project note
- attached folders
- sources tagged with ABR-related tags
- sources explicitly related to the project
- source roles such as `reference_paper`
- concepts, notes, and generated graph neighbors

## Implemented So Far

The repo is a Python package named `research-os` with a console script:

```text
research-os = research_os.cli:main
```

Implemented CLI commands:

```text
init
status
validate
new-project
attach-folder
resolve-project
build-graph
build-index
build-visual
context
context-health
scan
confirm-proposal
integrate-source
zotero-status
doctor
ingest-zotero-collection
```

Implemented modules:

- `src/research_os/cli.py`: command wiring.
- `src/research_os/config.py`: hub and registry loading.
- `src/research_os/projects.py`: project creation, folder attachment, marker resolution.
- `src/research_os/graph.py`: `graph/graph.json` generation.
- `src/research_os/index.py`: Obsidian `Home.md` generation.
- `src/research_os/ingest.py`: Zotero collection ingest into notes and source registry, including metadata-only concept classification.
- `src/research_os/integrate.py`: first CLI-assisted Stage 2 wiki integration slice; consumes one queued `wiki/inbox.md` source item, marks it complete, and logs metadata-only integration.
- `src/research_os/context.py`: agent context packet generation for projects, sources, tags, files, wiki excerpts, and graph-neighbor summaries.
- `src/research_os/scan.py`: local project-folder scanner that writes pending inbox proposals only with `--apply`.
- `src/research_os/staleness.py`: fingerprints and context-health checks for generated context surfaces.
- `src/research_os/wiki.py`: wiki index/log/inbox helpers and wiki page lookup for context packets.
- `src/research_os/paths.py`: shared hub path helpers.
- `src/research_os/validation.py`: hub validation.
- `src/research_os/zotero.py`: Zotero Desktop local API client.

## Demo Hub

The demo hub is:

```text
examples/demo-research-workspace
```

The demo Obsidian vault is:

```text
examples/demo-research-workspace/obsidian/starter-vault
```

Important generated/demo files:

- `examples/demo-research-workspace/obsidian/starter-vault/Home.md`
- `examples/demo-research-workspace/graph/graph.json`
- `examples/demo-research-workspace/registries/projects.yaml`
- `examples/demo-research-workspace/registries/sources.yaml`
- `examples/demo-research-workspace/registries/files.yaml`
- `examples/demo-research-workspace/registries/relations.yaml`
- `examples/demo-research-workspace/registries/inbox.yaml`

The demo has one active project:

```text
auditory-demo
```

It links to the user's Zotero `ABR` collection and several ABR papers.

## Zotero Facts Discovered

Zotero Desktop local API was reachable during prior work when allowed through the sandbox.

Observed Zotero details:

- Zotero version: `9.0.3`
- API version: `3`
- schema version: `42`
- ABR collection key: `G6CDLFHD`
- ABR parent collection: `Audioty System`, key `7HP8BAST`
- ABR had 6 top-level items, each with a PDF attachment.

Observed ABR papers ingested into the demo:

- `shanSubcorticalResponsesMusic2024`
- `shanComparingMethodsDeriving2025`
- `stollAuditoryBrainstemResponse2025`
- `bidelmanMyogenicArtifactsMasquerade2024`
- `kulasinghamPredictorsEstimatingSubcortical2024`
- `maddoxAuditoryBrainstemResponses2018`

## Codex Startup Setup

Root dev repo instructions:

```text
AGENTS.md
```

Generated hub instructions:

```text
src/research_os/template/AGENTS.md
```

Demo hub instructions:

```text
examples/demo-research-workspace/AGENTS.md
```

These instruct Codex to treat Research OS as an indexed research system and load:

1. `research-os.yaml`
2. `registries/projects.yaml`
3. `registries/sources.yaml`
4. `obsidian/research-os/Home.md` or configured vault path
5. `graph/graph.json` when graph context is useful

## Pushed Commit History

Important commits pushed to `origin/main`:

- `2e8aaca` - Initial Research OS implementation
- `b254eed` - Link demo vault to Zotero ABR collection
- `4dd7e4f` - Add Zotero collection ingest command
- `518c8bf` - Add Obsidian home index
- `d599ede` - Teach Codex to load Research OS index context
- `99486a4` - Refresh Research OS README

## Current Known Local State

There is a local untracked Obsidian scratch file that should not be staged or deleted unless the user explicitly asks:

```text
examples/demo-research-workspace/obsidian/starter-vault/Untitled.base
```

Ignored local artifacts may include `.DS_Store`, `.pytest_cache/`, `__pycache__/`, and Obsidian `.obsidian/` settings.

## Verification Commands

Use these before claiming implementation is complete:

```bash
python -m pytest -v
python -m compileall -q src
PYTHONPATH=src python -m research_os.cli --help
```

Optional package smoke test:

```bash
python -m pip wheel . --no-deps --no-build-isolation -w /private/tmp/research-os-wheel
```

## Likely Next Steps

Strong next product slice:

1. Expand `integrate-source` beyond metadata-only completion into source-note and existing synthesis/concept page section updates.
2. Grow metadata classification from the initial deterministic keyword map into a user-editable project vocabulary with correction memory.
3. Make the visual explorer show pending inbox/wiki integration items as reviewable islands.

Suggested design direction:

```text
registries/entities.yaml
registries/relations.yaml
```

or keep the current split:

```text
registries/projects.yaml
registries/sources.yaml
registries/files.yaml
registries/concepts.yaml
registries/relations.yaml
```

The current split is easier to evolve incrementally.
