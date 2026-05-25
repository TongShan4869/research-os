from pathlib import Path

import yaml

from research_os.cli import main


def test_new_project_adds_registry_entry_and_project_note(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    exit_code = main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"])

    assert exit_code == 0
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    assert projects[0]["id"] == "auditory-demo"
    assert projects[0]["title"] == "Auditory Demo"
    assert projects[0]["status"] == "active"
    assert projects[0]["obsidian_note"] == "Projects/auditory-demo.md"
    project_note = hub / "obsidian" / "starter-vault" / "Projects" / "auditory-demo.md"
    assert project_note.is_file()
    note_text = project_note.read_text(encoding="utf-8")
    assert "tags:" in note_text
    assert "  - research-os/project" in note_text
    assert "  - project/auditory-demo" in note_text
    assert "  - status/active" in note_text


def test_new_project_refuses_duplicate_id(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0

    exit_code = main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"])

    assert exit_code == 1
    assert "project already exists: auditory-demo" in capsys.readouterr().out


def test_attach_folder_updates_registry_and_marker(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    folder = tmp_path / "analysis"
    folder.mkdir()
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0

    exit_code = main(["attach-folder", "auditory-demo", str(folder), "--kind", "analysis", "--hub", str(hub)])

    assert exit_code == 0
    marker = yaml.safe_load((folder / ".research-os-project.yaml").read_text(encoding="utf-8"))
    assert marker["workspace"] == str(hub.resolve())
    assert marker["project_id"] == "auditory-demo"
    assert marker["folder_kind"] == "analysis"
    projects = yaml.safe_load((hub / "registries" / "projects.yaml").read_text(encoding="utf-8"))
    assert projects[0]["folders"]["analysis"] == str(folder.resolve())


def test_resolve_project_by_marker(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    folder = tmp_path / "analysis"
    child = folder / "notebooks"
    child.mkdir(parents=True)
    assert main(["init", str(hub)]) == 0
    (folder / ".research-os-project.yaml").write_text(
        f"workspace: {hub.resolve()}\nproject_id: auditory-demo\nfolder_kind: analysis\n",
        encoding="utf-8",
    )

    exit_code = main(["resolve-project", str(child)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "project_id: auditory-demo" in output
    assert "resolution: marker" in output


def test_resolve_project_by_registry_path(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    folder = tmp_path / "analysis"
    child = folder / "notebooks"
    child.mkdir(parents=True)
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0
    assert main(["attach-folder", "auditory-demo", str(folder), "--kind", "analysis", "--hub", str(hub)]) == 0
    (folder / ".research-os-project.yaml").unlink()

    exit_code = main(["resolve-project", str(child), "--hub", str(hub)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "project_id: auditory-demo" in output
    assert "resolution: registry-path" in output
