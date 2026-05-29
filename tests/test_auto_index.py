from pathlib import Path

import yaml

from research_os.cli import main


def test_scan_proposes_file_assignments_without_mutating_registries(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    data_dir = project_root / "data"
    figures_dir = project_root / "figures"
    data_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    (data_dir / "raw.csv").write_text("time,value\n0,1\n", encoding="utf-8")
    (figures_dir / "waveform.png").write_bytes(b"fake image")
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    projects[0]["folders"] = {"root": "projects/auditory-demo"}
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["scan", "--hub", str(hub)]) == 0

    output = capsys.readouterr().out
    assert "proposals: 2" in output
    assert yaml.safe_load((hub / "registries" / "inbox.yaml").read_text(encoding="utf-8")) == []
    assert yaml.safe_load((hub / "registries" / "files.yaml").read_text(encoding="utf-8")) == []


def test_scan_apply_writes_pending_inbox_not_confirmed_files(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "raw.csv").write_text("time,value\n0,1\n", encoding="utf-8")
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    projects[0]["folders"] = {"root": "projects/auditory-demo"}
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["scan", "--hub", str(hub), "--apply"]) == 0

    inbox = yaml.safe_load((hub / "registries" / "inbox.yaml").read_text(encoding="utf-8"))
    assert inbox[0]["path"] == "projects/auditory-demo/data/raw.csv"
    assert inbox[0]["proposed_type"] == "Dataset"
    assert inbox[0]["proposed_project"] == "auditory-demo"
    assert inbox[0]["status"] == "pending"
    assert yaml.safe_load((hub / "registries" / "files.yaml").read_text(encoding="utf-8")) == []


def test_confirm_proposal_promotes_pending_item_to_files_registry(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "raw.csv").write_text("time,value\n0,1\n", encoding="utf-8")
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    projects[0]["folders"] = {"root": "projects/auditory-demo"}
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    assert main(["scan", "--hub", str(hub), "--apply"]) == 0
    capsys.readouterr()

    assert main(["confirm-proposal", "proposal:projects-auditory-demo-data-raw.csv", "--hub", str(hub)]) == 0

    output = capsys.readouterr().out
    assert "confirmed proposal: proposal:projects-auditory-demo-data-raw.csv" in output
    files = yaml.safe_load((hub / "registries" / "files.yaml").read_text(encoding="utf-8"))
    assert files == [
        {
            "id": "file:projects-auditory-demo-data-raw.csv",
            "type": "Dataset",
            "title": "raw.csv",
            "path": "projects/auditory-demo/data/raw.csv",
            "projects": ["auditory-demo"],
            "roles": ["dataset"],
            "provider": {"name": "local_folder"},
            "review": {"status": "confirmed", "proposal_id": "proposal:projects-auditory-demo-data-raw.csv"},
        }
    ]
    inbox = yaml.safe_load((hub / "registries" / "inbox.yaml").read_text(encoding="utf-8"))
    assert inbox[0]["status"] == "confirmed"
    assert inbox[0]["confirmed_file"] == "file:projects-auditory-demo-data-raw.csv"

    assert main(["context", "projects/auditory-demo/data/raw.csv", "--hub", str(hub), "--json"]) == 0
    packet = yaml.safe_load(capsys.readouterr().out)
    assert packet["files"][0]["id"] == "file:projects-auditory-demo-data-raw.csv"


def test_confirm_proposal_rejects_missing_and_duplicate_paths(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    proposal = {
        "id": "proposal:data-csv",
        "path": "projects/auditory-demo/data/raw.csv",
        "proposed_type": "Dataset",
        "proposed_role": "dataset",
        "proposed_project": "auditory-demo",
        "provider": {"name": "local_folder"},
        "status": "pending",
    }
    (hub / "registries" / "inbox.yaml").write_text(yaml.safe_dump([proposal], sort_keys=False), encoding="utf-8")
    (hub / "registries" / "files.yaml").write_text(
        yaml.safe_dump(
            [
                {
                    "id": "file:existing",
                    "type": "Dataset",
                    "title": "raw.csv",
                    "path": "projects/auditory-demo/data/raw.csv",
                    "projects": ["auditory-demo"],
                }
            ],
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["confirm-proposal", "proposal:missing", "--hub", str(hub)]) == 1
    assert "proposal not found or not pending: proposal:missing" in capsys.readouterr().out

    assert main(["confirm-proposal", "proposal:data-csv", "--hub", str(hub)]) == 1
    assert "file already indexed for path: projects/auditory-demo/data/raw.csv" in capsys.readouterr().out


def test_scan_respects_max_files_and_ignore_names(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    data_dir = project_root / "data"
    cache_dir = project_root / "cache"
    data_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)
    (data_dir / "one.csv").write_text("x\n1\n", encoding="utf-8")
    (data_dir / "two.csv").write_text("x\n2\n", encoding="utf-8")
    (cache_dir / "ignored.csv").write_text("x\n3\n", encoding="utf-8")
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    projects[0]["folders"] = {"root": "projects/auditory-demo"}
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    capsys.readouterr()

    assert main(["scan", "--hub", str(hub), "--ignore", "cache", "--max-files", "1"]) == 0

    output = capsys.readouterr().out
    assert "proposals: 1" in output
    assert "scan stopped early after reaching max files: 1" in output


def test_index_folders_creates_summarized_context_surfaces(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    data_dir = project_root / "data" / "raw"
    scripts_dir = project_root / "analysis"
    data_dir.mkdir(parents=True)
    scripts_dir.mkdir(parents=True)
    (data_dir / "participants.csv").write_text("id,score\n1,2\n", encoding="utf-8")
    (scripts_dir / "fit_trf.py").write_text("print('fit')\n", encoding="utf-8")
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    projects[0]["folders"] = {"workspace": "projects/auditory-demo"}
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["index-folders", "--hub", str(hub), "--max-depth", "2"]) == 0
    assert main(["index-folders", "--hub", str(hub), "--max-depth", "2"]) == 0

    output = capsys.readouterr().out
    assert "folder surfaces: 3" in output
    files = yaml.safe_load((hub / "registries" / "files.yaml").read_text(encoding="utf-8"))
    surface_ids = [entry["id"] for entry in files]
    assert surface_ids == [
        "folder-surface:auditory-demo:workspace:analysis",
        "folder-surface:auditory-demo:workspace:data",
        "folder-surface:auditory-demo:workspace:data-raw",
    ]
    data_entry = files[1]
    assert data_entry["type"] == "Folder"
    assert data_entry["title"] == "data"
    assert data_entry["path"] == "projects/auditory-demo/data"
    assert data_entry["projects"] == ["auditory-demo"]
    assert data_entry["roles"] == ["workspace_section"]
    assert data_entry["provider"] == {"name": "local_folder", "root_kind": "workspace"}
    assert "1 subfolder" in data_entry["summary"]
    assert "notable children: raw" in data_entry["summary"]
    assert files[2]["summary"] == "Folder with 1 file; includes tabular data; notable children: participants.csv."
