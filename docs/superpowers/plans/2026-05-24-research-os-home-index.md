# Research OS Home Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generated Obsidian `Home.md` that acts as the project-management cockpit for Research OS.

**Architecture:** Add `src/research_os/index.py` to render a markdown index from `registries/projects.yaml` and `registries/sources.yaml`. Add a shared `obsidian_vault_path()` helper, wire `research-os build-index` into the CLI, and update the demo/README.

**Tech Stack:** Python stdlib, PyYAML, pytest.

---

### Task 1: Home Index Command

**Files:**
- Create: `src/research_os/index.py`
- Create: `src/research_os/paths.py`
- Modify: `src/research_os/cli.py`
- Modify: `src/research_os/ingest.py`
- Test: `tests/test_index.py`

- [x] **Step 1: Write failing tests**

Write a test that creates a hub, registers a project, writes sources, runs `research-os build-index`, and asserts `Home.md` contains project links, Zotero collection links, source counts, and needs-attention sections.

- [x] **Step 2: Run red test**

Run: `python -m pytest tests/test_index.py -v`
Expected: FAIL because `build-index` is not implemented.

- [x] **Step 3: Implement index rendering**

Render `Home.md` at the Obsidian vault root. Use Obsidian wikilinks and registry-derived tables.

- [x] **Step 4: Run green test**

Run: `python -m pytest tests/test_index.py -v`
Expected: PASS.

### Task 2: Demo And Verification

**Files:**
- Modify: `README.md`
- Create or update: `examples/demo-research-workspace/obsidian/starter-vault/Home.md`

- [x] **Step 1: Generate demo index**

Run `PYTHONPATH=src python -m research_os.cli build-index --hub examples/demo-research-workspace`.

- [x] **Step 2: Verify**

Run: `python -m pytest -v`
Expected: PASS.
