# Research OS

Research OS is a local-first workspace template for scientific research built around Codex, Obsidian, Zotero, and existing project folders.

The first working slice provides a small Python CLI that can create a bootable Research OS hub:

```bash
python -m research_os.cli init ~/ResearchOS
```

## Commands

```bash
python -m research_os.cli init ~/ResearchOS
python -m research_os.cli status --hub ~/ResearchOS
python -m research_os.cli validate --hub ~/ResearchOS
python -m research_os.cli new-project auditory-demo --title "Auditory Demo" --hub ~/ResearchOS
python -m research_os.cli attach-folder auditory-demo ./analysis --kind analysis --hub ~/ResearchOS
python -m research_os.cli resolve-project ./analysis --hub ~/ResearchOS
python -m research_os.cli build-graph --hub ~/ResearchOS
python -m research_os.cli zotero-status
python -m research_os.cli doctor --hub ~/ResearchOS
```

## Zotero Collection Ingest

With Zotero Desktop running and the local API enabled:

```bash
python -m research_os.cli ingest-zotero-collection ABR --project auditory-demo --hub ~/ResearchOS
```

This creates or updates:

- `Sources/Collections/<collection>.md`
- `Sources/Papers/<citation-key>.md`
- `registries/sources.yaml`
- `graph/graph.json`

Paper notes include `zotero_item_key`, `citation_key`, `Open in Zotero`, and `Open PDF in Zotero` links when a PDF attachment is available.

## Demo

```bash
python -m research_os.cli validate --hub examples/demo-research-workspace
python -m research_os.cli build-graph --hub examples/demo-research-workspace
```
