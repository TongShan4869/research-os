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

## Demo

```bash
python -m research_os.cli validate --hub examples/demo-research-workspace
python -m research_os.cli build-graph --hub examples/demo-research-workspace
```
