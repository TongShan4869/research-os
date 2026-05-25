# Zotero Collection Ingest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `research-os ingest-zotero-collection` so a Zotero collection can be turned into Obsidian collection/paper notes, source registry entries, and graph edges.

**Architecture:** Add a small Zotero local API client in `src/research_os/zotero.py` and a separate ingest writer in `src/research_os/ingest.py`. The CLI command resolves a collection by name or key, fetches top-level items and attachment keys, writes markdown notes into the configured vault or starter vault, updates `registries/sources.yaml`, and rebuilds `graph/graph.json`.

**Tech Stack:** Python stdlib `urllib.request`, `json`, `pathlib`; PyYAML; pytest with monkeypatched fake Zotero client.

---

### Task 1: Ingest Writer

**Files:**
- Create: `src/research_os/ingest.py`
- Modify: `src/research_os/cli.py`
- Test: `tests/test_ingest_zotero.py`

- [ ] **Step 1: Write failing test**

Test `ingest-zotero-collection ABR --project auditory-demo --hub <hub>` with a fake Zotero client that returns one collection and one item with a PDF attachment. Assert the command writes `Sources/Collections/ABR.md`, writes a paper note with `zotero://select` and `zotero://open-pdf` links, updates `registries/sources.yaml`, and rebuilds `graph/graph.json`.

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_ingest_zotero.py -v`
Expected: FAIL because the command/module does not exist.

- [ ] **Step 3: Implement minimal ingest flow**

Add the command, fake-client friendly boundaries, note rendering, source registry merge by `zotero_item_key`, and graph rebuild.

- [ ] **Step 4: Run green test**

Run: `python -m pytest tests/test_ingest_zotero.py -v`
Expected: PASS.

### Task 2: Live Zotero Smoke And Docs

**Files:**
- Modify: `README.md`
- Modify: `src/research_os/zotero.py`

- [ ] **Step 1: Add docs**

Document `research-os ingest-zotero-collection ABR --project auditory-demo --hub ~/ResearchOS`.

- [ ] **Step 2: Verify**

Run: `python -m pytest -v`
Expected: PASS.

Run a live read-only smoke against the demo hub only when Zotero local API is available.
