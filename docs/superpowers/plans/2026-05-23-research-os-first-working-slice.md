# Research OS First Working Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first installable Research OS CLI and bundled workspace template.

**Architecture:** A small Python package exposes a `research-os` console script. The CLI copies package data from `research_os/template`, validates hub structure and YAML registries, resolves projects from markers or registry paths, and builds a minimal JSON graph from registered projects and source records.

**Tech Stack:** Python 3.11+, `argparse`, `importlib.resources`, `pathlib`, `json`, `yaml` through PyYAML, `pytest`.

---

### Task 1: Package Skeleton And Init Command

**Files:**
- Create: `pyproject.toml`
- Create: `src/research_os/__init__.py`
- Create: `src/research_os/cli.py`
- Create: `src/research_os/paths.py`
- Create: `src/research_os/template/*`
- Test: `tests/test_init.py`

- [ ] **Step 1: Write failing tests for `research-os init`**

```python
from pathlib import Path

from research_os.cli import main


def test_init_creates_bootable_hub(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"

    exit_code = main(["init", str(hub)])

    assert exit_code == 0
    assert (hub / "research-os.yaml").is_file()
    assert (hub / "AGENTS.md").is_file()
    assert (hub / "workflows" / "onboard.md").is_file()
    assert (hub / "registries" / "projects.yaml").is_file()
    assert (hub / "graph" / "graph.json").is_file()
    assert "Open Codex" in capsys.readouterr().out


def test_init_refuses_non_empty_directory_without_force(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    hub.mkdir()
    (hub / "note.txt").write_text("keep me", encoding="utf-8")

    exit_code = main(["init", str(hub)])

    assert exit_code == 2
    assert (hub / "note.txt").read_text(encoding="utf-8") == "keep me"
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_init.py -v`
Expected: FAIL because `research_os` does not exist.

- [ ] **Step 3: Implement package skeleton and template copy**

Create a `pyproject.toml` with a console script named `research-os`. Implement `main(argv=None)` in `src/research_os/cli.py`, copy bundled files from `src/research_os/template`, and return integer exit codes.

- [ ] **Step 4: Run green test**

Run: `python -m pytest tests/test_init.py -v`
Expected: PASS.

### Task 2: Status And Validate Commands

**Files:**
- Create: `src/research_os/config.py`
- Create: `src/research_os/validation.py`
- Modify: `src/research_os/cli.py`
- Test: `tests/test_status_validate.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

from research_os.cli import main


def make_hub(tmp_path: Path) -> Path:
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    return hub


def test_status_reports_incomplete_onboarding(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)

    exit_code = main(["status", "--hub", str(hub)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Research OS hub" in output
    assert "onboarding: incomplete" in output


def test_validate_reports_missing_required_file(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)
    (hub / "AGENTS.md").unlink()

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 1
    assert "missing required file: AGENTS.md" in capsys.readouterr().out


def test_validate_accepts_fresh_hub(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 0
    assert "hub is valid" in capsys.readouterr().out
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_status_validate.py -v`
Expected: FAIL because commands are not implemented.

- [ ] **Step 3: Implement hub loading and validation**

Parse `research-os.yaml`, validate required files/directories, validate registry YAML shapes, and print actionable blockers.

- [ ] **Step 4: Run green test**

Run: `python -m pytest tests/test_status_validate.py -v`
Expected: PASS.

### Task 3: Project Commands And Resolution

**Files:**
- Create: `src/research_os/projects.py`
- Modify: `src/research_os/cli.py`
- Test: `tests/test_projects.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

import yaml

from research_os.cli import main


def test_new_project_adds_registry_entry(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    exit_code = main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) 

    assert exit_code == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    assert projects[0]["id"] == "auditory-demo"
    assert projects[0]["title"] == "Auditory Demo"


def test_resolve_project_by_marker(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    folder = tmp_path / "analysis"
    folder.mkdir()
    assert main(["init", str(hub)]) == 0
    (folder / ".research-os-project.yaml").write_text(
        f"workspace: {hub}\nproject_id: auditory-demo\nfolder_kind: analysis\n",
        encoding="utf-8",
    )

    exit_code = main(["resolve-project", str(folder)])

    assert exit_code == 0
    assert "auditory-demo" in capsys.readouterr().out


def test_attach_folder_updates_registry_and_marker(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    folder = tmp_path / "analysis"
    folder.mkdir()
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0

    exit_code = main(["attach-folder", "auditory-demo", str(folder), "--kind", "analysis", "--hub", str(hub)])

    assert exit_code == 0
    marker = yaml.safe_load((folder / ".research-os-project.yaml").read_text(encoding="utf-8"))
    assert marker["project_id"] == "auditory-demo"
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    assert projects[0]["folders"]["analysis"] == str(folder)
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_projects.py -v`
Expected: FAIL because project commands are missing.

- [ ] **Step 3: Implement project registry helpers**

Load and save `registries/projects.yaml`, create project notes, write marker files, and resolve marker or registry path matches.

- [ ] **Step 4: Run green test**

Run: `python -m pytest tests/test_projects.py -v`
Expected: PASS.

### Task 4: Graph Build And Zotero-Unavailable Doctor

**Files:**
- Create: `src/research_os/graph.py`
- Create: `src/research_os/zotero.py`
- Modify: `src/research_os/cli.py`
- Test: `tests/test_graph_doctor.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
import json

from research_os.cli import main


def test_build_graph_emits_project_nodes(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0

    exit_code = main(["build-graph", "--hub", str(hub)])

    assert exit_code == 0
    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    assert {"id": "project:auditory-demo", "type": "Project", "title": "Auditory Demo"} in graph["nodes"]


def test_zotero_status_reports_unavailable_without_crashing(capsys):
    exit_code = main(["zotero-status"])

    assert exit_code in {0, 1}
    output = capsys.readouterr().out
    assert "Zotero" in output
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_graph_doctor.py -v`
Expected: FAIL because graph and Zotero commands are missing.

- [ ] **Step 3: Implement graph and Zotero status**

Build `graph/graph.json` from projects and source registry entries. Check Zotero local API with a short timeout and report unavailable as a blocker instead of raising.

- [ ] **Step 4: Run green test**

Run: `python -m pytest tests/test_graph_doctor.py -v`
Expected: PASS.

### Task 5: Demo Workspace And Full Verification

**Files:**
- Create: `examples/demo-research-workspace/README.md`
- Create: `examples/demo-research-workspace/research-os.yaml`
- Create: `examples/demo-research-workspace/registries/projects.yaml`
- Create: `examples/demo-research-workspace/registries/sources.yaml`
- Modify: `README.md`

- [ ] **Step 1: Add smoke test for demo validation**

```python
from pathlib import Path

from research_os.cli import main


def test_demo_workspace_validates():
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo-research-workspace"

    assert main(["validate", "--hub", str(demo)]) == 0
```

- [ ] **Step 2: Run red test**

Run: `python -m pytest tests/test_demo.py -v`
Expected: FAIL until demo files are present.

- [ ] **Step 3: Add demo workspace and README**

Create a minimal demo with one project, one fake paper source, and generated graph file.

- [ ] **Step 4: Run full verification**

Run: `python -m pytest -v`
Expected: PASS.

Run: `python -m research_os.cli init /tmp/research-os-smoke`
Expected: PASS and prints Codex onboarding instructions.
