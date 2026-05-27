# Research OS

Research OS is a local-first indexing layer for scientific research. It helps Codex understand how projects, papers, notes, folders, data, figures, manuscripts, and external tools relate to each other.

## For Agents: Start Here

If a user sends you this GitHub repo and asks to set up Research OS, do the setup for them. Do not ask them to clone the repo.

1. Install Research OS directly from the GitHub zip:

```bash
python -m pip install "https://github.com/TongShan4869/research-os/archive/refs/heads/main.zip"
```

2. Create the user's hub, using `~/ResearchOS` unless they ask for another location:

```bash
research-os init ~/ResearchOS
```

3. Start onboarding with questions, not instructions:

```text
I created your Research OS hub. Do you want to use the starter Obsidian vault or connect an existing vault?
Should I check Zotero Desktop?
What is the first research project or folder you want indexed?
```

4. Run the setup commands yourself as the user answers:

```bash
research-os status --hub ~/ResearchOS
research-os validate --hub ~/ResearchOS
research-os doctor --hub ~/ResearchOS
research-os build-index --hub ~/ResearchOS
research-os build-graph --hub ~/ResearchOS
research-os build-visual --hub ~/ResearchOS
```

Only developers need to clone this repository. Regular users should be able to hand the GitHub link to an agent and then answer onboarding questions.

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
- Tracks provider-neutral files in `registries/files.yaml` and explicit links in `registries/relations.yaml`.
- Proposes unconfirmed file assignments in `registries/inbox.yaml` before mutating the confirmed index.
- Emits agent-ready context packets for projects, sources, tags, files, wiki excerpts, and graph-neighbor summaries.
- Stamps generated context surfaces with fingerprints so agents can detect stale `Home.md`, `graph.json`, and visual explorer output.
- Maintains a Karpathy-style LLM wiki core in Obsidian: `index.md`, `log.md`, synthesis pages, entity pages, claims, methods, datasets, and results.
- Generates an Obsidian `Home.md` project cockpit.
- Generates `graph/graph.json` for linked project/source context.
- Generates a static `visual/index.html` explorer for browsing the research graph.
- Connects papers to Zotero when Zotero is available, captures Zotero metadata, and assigns explainable concept tags from title, abstract, and Zotero tags.
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

Local files can also be indexed without pretending they are Zotero papers:

```yaml
- id: file:auditory-demo:data-raw-csv
  type: Dataset
  title: raw.csv
  path: projects/auditory-demo/data/raw.csv
  projects:
    - auditory-demo
  roles:
    - dataset
  provider:
    name: local_folder
  review:
    status: confirmed
```

Explicit relations connect entities across providers:

```yaml
- source: file:auditory-demo:data-raw-csv
  target: project:auditory-demo
  type: belongs_to_project
```

## Repository Layout

```text
.
  AGENTS.md                         Codex instructions for this development repo
  PROJECT_MEMORY.md                 durable project context for future sessions
  README.md
  pyproject.toml
  src/research_os/
    cli.py                          CLI entrypoint
    config.py                       hub loading and registry helpers
    graph.py                        graph.json generation
    index.py                        Obsidian Home.md generation
    ingest.py                       Zotero collection ingest
    context.py                      agent context packet generation
    scan.py                         local file proposal scanning
    paths.py                        shared hub path helpers
    projects.py                     project registry and folder attachment
    validation.py                   hub validation
    visual.py                       static visual explorer generation
    visual_template.html            bundled React Flow visual shell
    zotero.py                       Zotero local API client
    template/                       files copied by `research-os init`
  visual-app/                       React Flow source for the visual explorer
  examples/demo-research-workspace/  working demo hub
  tests/                            pytest coverage
```

## Install

For regular users, an agent should install Research OS directly from GitHub:

```bash
python -m pip install "https://github.com/TongShan4869/research-os/archive/refs/heads/main.zip"
research-os --help
```

For local development from a cloned repo:

```bash
python -m pip install -e .
research-os --help
```

Without installing, run commands from the repo with:

```bash
PYTHONPATH=src python -m research_os.cli --help
```

## Codex Skill

This repo also includes an installable Codex skill that turns Codex into a Research OS onboarding guide:

```text
src/research_os/skills/research-os
```

Use it when you want an agent to install Research OS, create or inspect a hub, connect Obsidian/Zotero/project folders, and walk a user through the safe indexing workflow. The skill is helpful, but it should not be a prerequisite for ordinary users: an agent can follow the "For Agents: Start Here" section from the GitHub link alone.

After installing the skill in Codex, ask:

```text
Use $research-os to install Research OS and guide me through onboarding my research workspace.
```

The skill teaches the agent to:

- install the CLI directly from the GitHub zip for users, or with `python -m pip install -e .` for local development
- create or open a hub with `research-os init`
- check `research-os.yaml`, validate the hub, and run doctor checks
- ask before using Zotero, reading PDFs, attaching folders, or confirming scan proposals
- register projects, attach confirmed folders, ingest Zotero collections, and scan local files
- build the generated user surfaces: `Home.md`, `graph/graph.json`, and `visual/index.html`
- explain the Research OS loop from registries to Obsidian, visual graph, and agent context

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
research-os build-visual --hub ~/ResearchOS
research-os context-health --hub ~/ResearchOS
```

Open `~/ResearchOS/visual/index.html` in a browser to inspect the generated visual map.

Ask Research OS what context an agent should load:

```bash
research-os context auditory-demo --hub ~/ResearchOS
research-os context auditory-demo --hub ~/ResearchOS --json
```

Scan configured project folders for unindexed files:

```bash
research-os scan --hub ~/ResearchOS
research-os scan --hub ~/ResearchOS --apply
research-os confirm-proposal proposal:projects-auditory-demo-data-raw.csv --hub ~/ResearchOS
```

`scan` is safe by default. Without `--apply`, it prints proposal counts only. With `--apply`, it writes pending proposals to `registries/inbox.yaml`; it does not confirm files or attach folders to projects. Use `confirm-proposal` to promote exactly one pending proposal into `registries/files.yaml`.

Consume one queued wiki integration item:

```bash
research-os integrate-source paper:smith-2024 --hub ~/ResearchOS
```

The first slice is metadata-only: it requires an existing unchecked item in `wiki/inbox.md`, marks that item complete, and appends to `log.md`. It does not read PDFs or full text.

## LLM Wiki Core

The Obsidian vault has three layers:

- raw source notes under `Sources/`
- machine-readable registries under `registries/`
- an LLM-maintained wiki core under `index.md`, `log.md`, `Synthesis/`, `Entities/`, `Concepts/`, `Claims/`, `Methods/`, `Datasets/`, and `Results/`

`index.md` is the wiki catalog. `log.md` is an append-only maintenance ledger. `wiki/inbox.md` queues sources for explicit integration. Ingest commands register sources safely and queue integration work; they do not deep-process papers or read PDFs unless the user confirms a Stage 2 workflow.

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
- wiki index/log/inbox links
- pending wiki integration count
- linked Zotero collections
- source counts per project
- recent source notes
- context readiness, including pending inbox proposals and indexed files
- items that need attention, such as sources with no linked project or concepts

Open the vault folder in Obsidian to inspect notes and Graph View.

## Visual Explorer

`research-os build-visual` creates:

```text
visual/index.html
```

The visual explorer is a static React Flow page generated from the current `graph/graph.json`. Run `research-os build-graph` when the hub knowledge graph needs to change; `research-os build-visual` only packages that graph for browsing. It is designed as a research board:

- `Zotero Library` is the canonical home for paper collections and paper pills.
- `Global Wiki` is the canonical home for concepts.
- `Workspace Context` keeps folders, datasets, figures, manuscripts, notes, and code surfaces visible instead of hiding non-paper graph nodes.
- Project cards connect to the papers and concepts they use through edges, without duplicating those nodes.
- Search keeps direct neighbors visible for matching nodes, so filtered views still preserve local context.
- Clicking a project opens its surrounding context by expanding the linked library and wiki regions.
- The right inspector shows selected-node metadata, direct neighbors, and compact graph counts.

The generated page is self-contained. Ordinary Research OS users do not need Node.js or a dev server to run it.

For frontend development, the source lives in `visual-app/`:

```bash
cd visual-app
npm install
npm run build
```

That build updates `src/research_os/visual_template.html`, which is packaged with the Python project. The Python CLI injects the current hub graph data into that template when `build-visual` runs.

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

Ingest reads Zotero item metadata only: title, abstract note, publication title, date, creators, DOI, and Zotero tags. It stores that metadata in Research OS, assigns concept tags with evidence, and leaves Zotero itself unchanged.

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
research-os build-visual --hub <path>
research-os context <query> --hub <path> [--json]
research-os scan --hub <path> [--apply] [--ignore <name>] [--max-files <n>]
research-os confirm-proposal <proposal-id> --hub <path>
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
PYTHONPATH=src python -m research_os.cli build-visual --hub examples/demo-research-workspace
```

Then open `examples/demo-research-workspace/obsidian/starter-vault` in Obsidian and start from `Home.md`, or open `examples/demo-research-workspace/visual/index.html` in a browser.

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

When changing the visual explorer source, rebuild the bundled template:

```bash
cd visual-app
npm run build
```

## Safety Principles

- Do not mutate Zotero records unless the user explicitly asks.
- Do not deep-process papers automatically.
- Do not attach folders to projects on heuristic matches without confirmation.
- Preserve existing notes; prefer append/update sections over wholesale rewrites.
- Keep the index explicit: registries and graph should explain why context is connected.
