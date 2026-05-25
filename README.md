# Research OS

Research OS is a local-first indexing layer for scientific research. It helps Codex understand how projects, papers, notes, folders, data, figures, manuscripts, and external tools relate to each other.

The core idea is simple: files and apps remain where they are, but their context is indexed in one place.

```text
project folders + Obsidian + Zotero + PDFs + outputs
        -> Research OS registries
        -> Home.md + graph.json
        -> Codex can resolve project context
```

Research OS is not trying to replace Zotero, Obsidian, or normal project folders. It coordinates them.

## What It Does

- Creates a bootable Research OS hub with registries, workflows, schemas, and an Obsidian starter vault.
- Tracks project identity in `registries/projects.yaml`.
- Tracks papers and other sources in `registries/sources.yaml`.
- Generates an Obsidian `Home.md` project cockpit.
- Generates `graph/graph.json` for linked project/source context.
- Connects papers to Zotero when Zotero is available.
- Gives Codex startup instructions through `AGENTS.md`, similar in spirit to Claude Code's `CLAUDE.md`.

## Mental Model

Research OS treats everything important as an indexed entity.

A project can start as a folder:

```yaml
- id: auditory-demo
  title: Auditory Demo Project
  status: active
  obsidian_note: Projects/auditory-demo.md
  folders:
    analysis: projects/auditory-demo/analysis
  zotero_collections:
    - ABR
  tags:
    - auditory-neuroscience
```

A paper can be linked by project, concept, tag, and provider metadata:

```yaml
- id: paper:shanSubcorticalResponsesMusic2024
  type: Paper
  title: Subcortical responses to music and speech are alike while cortical responses diverge
  citation_key: shanSubcorticalResponsesMusic2024
  zotero_item_key: GBEMXBSK
  projects:
    - auditory-demo
  concepts:
    - auditory-brainstem-response
```

That lets an agent understand that a paper tagged or linked to `ABR` is relevant when the user asks about the ABR project, even if the PDF lives in Zotero, a folder, or somewhere else.

## Repository Layout

```text
.
  AGENTS.md                         Codex instructions for this development repo
  README.md
  pyproject.toml
  src/research_os/
    cli.py                          CLI entrypoint
    config.py                       hub loading and registry helpers
    graph.py                        graph.json generation
    index.py                        Obsidian Home.md generation
    ingest.py                       Zotero collection ingest
    paths.py                        shared hub path helpers
    projects.py                     project registry and folder attachment
    validation.py                   hub validation
    zotero.py                       Zotero local API client
    template/                       files copied by `research-os init`
  examples/demo-research-workspace/  working demo hub
  tests/                            pytest coverage
```

## Install From This Repo

For local development:

```bash
python -m pip install -e .
research-os --help
```

Without installing, run commands from the repo with:

```bash
PYTHONPATH=src python -m research_os.cli --help
```

## Quickstart

Create a hub:

```bash
research-os init ~/ResearchOS
```

Open `~/ResearchOS` in Codex. Codex will read the hub's `AGENTS.md`, then use the registries, `Home.md`, and graph as the indexed research context.

Check the hub:

```bash
research-os status --hub ~/ResearchOS
research-os validate --hub ~/ResearchOS
research-os doctor --hub ~/ResearchOS
```

Create a project:

```bash
research-os new-project auditory-demo --title "Auditory Demo" --hub ~/ResearchOS
```

Attach an existing folder to that project:

```bash
research-os attach-folder auditory-demo ./analysis --kind analysis --hub ~/ResearchOS
```

Resolve which project a folder belongs to:

```bash
research-os resolve-project ./analysis --hub ~/ResearchOS
```

Build generated context:

```bash
research-os build-index --hub ~/ResearchOS
research-os build-graph --hub ~/ResearchOS
```

## Obsidian

Each hub can point to an existing Obsidian vault or use the starter vault:

```yaml
paths:
  obsidian_vault: obsidian/starter-vault
```

`research-os build-index` creates or refreshes:

```text
obsidian/starter-vault/Home.md
```

`Home.md` summarizes:

- active projects
- linked Zotero collections
- source counts per project
- recent source notes
- items that need attention, such as sources with no linked project or concepts

Open the vault folder in Obsidian to inspect notes and Graph View.

## Zotero

Zotero is optional. Research OS uses it as a metadata provider when available, not as the only place papers can live.

Check whether Zotero Desktop's local API is reachable:

```bash
research-os zotero-status
```

Ingest a Zotero collection into a project:

```bash
research-os ingest-zotero-collection ABR --project auditory-demo --hub ~/ResearchOS
```

This creates or updates:

- `Sources/Collections/<collection>.md`
- `Sources/Papers/<citation-key>.md`
- `registries/sources.yaml`
- `graph/graph.json`

Paper notes include Zotero deep links when available:

- `zotero://select/library/items/<item-key>`
- `zotero://open-pdf/library/items/<attachment-key>`

Future source providers can index local PDF folders or other metadata sources without requiring Zotero.

## Codex Startup Context

Codex uses `AGENTS.md` as the project-local instruction file. In Research OS hubs, that file tells Codex to treat the hub as an indexed research system.

At session start, Codex should load:

1. `research-os.yaml`
2. `registries/projects.yaml`
3. `registries/sources.yaml`
4. `obsidian/starter-vault/Home.md`, or the configured vault path
5. `graph/graph.json` when graph context is useful

When the user mentions a project, tag, paper, folder, concept, or role, Codex should resolve it through the registries before relying on folder names alone.

## CLI Commands

```bash
research-os init <path>
research-os status --hub <path>
research-os validate --hub <path>
research-os doctor --hub <path>
research-os new-project <project-id> --title "<title>" --hub <path>
research-os attach-folder <project-id> <folder> --kind <kind> --hub <path>
research-os resolve-project <folder> --hub <path>
research-os build-index --hub <path>
research-os build-graph --hub <path>
research-os zotero-status
research-os ingest-zotero-collection <collection-name-or-key> --project <project-id> --hub <path>
```

From source without installing, prefix commands with:

```bash
PYTHONPATH=src python -m research_os.cli
```

## Demo

The demo hub is at:

```text
examples/demo-research-workspace
```

The demo Obsidian vault is at:

```text
examples/demo-research-workspace/obsidian/starter-vault
```

Try:

```bash
PYTHONPATH=src python -m research_os.cli validate --hub examples/demo-research-workspace
PYTHONPATH=src python -m research_os.cli build-index --hub examples/demo-research-workspace
PYTHONPATH=src python -m research_os.cli build-graph --hub examples/demo-research-workspace
```

Then open `examples/demo-research-workspace/obsidian/starter-vault` in Obsidian and start from `Home.md`.

## Development

Run tests:

```bash
python -m pytest -v
```

Check Python files compile:

```bash
python -m compileall -q src
```

Build a wheel:

```bash
python -m pip wheel . --no-deps --no-build-isolation -w /private/tmp/research-os-wheel
```

Current package metadata lives in `pyproject.toml`.

## Safety Principles

- Do not mutate Zotero records unless the user explicitly asks.
- Do not deep-process papers automatically.
- Do not attach folders to projects on heuristic matches without confirmation.
- Preserve existing notes; prefer append/update sections over wholesale rewrites.
- Keep the index explicit: registries and graph should explain why context is connected.
