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
    assert (hub / "registries" / "sources.yaml").is_file()
    assert (hub / "obsidian" / "starter-vault" / "index.md").is_file()
    assert (hub / "obsidian" / "starter-vault" / "log.md").is_file()
    assert (hub / "obsidian" / "starter-vault" / "wiki" / "inbox.md").is_file()
    index_text = (hub / "obsidian" / "starter-vault" / "index.md").read_text(encoding="utf-8")
    assert "Read this before opening random folders" in index_text
    assert "## Page Types" in index_text
    assert "`Synthesis/`: best first stop" in index_text
    for directory in ["Synthesis", "Entities", "Claims", "Methods", "Datasets", "Results"]:
        assert (hub / "obsidian" / "starter-vault" / directory).is_dir()
    for workflow in ["integrate-source.md", "query-wiki.md", "lint-wiki.md"]:
        assert (hub / "workflows" / workflow).is_file()
    assert (hub / "schemas" / "project.schema.yaml").is_file()
    assert (hub / "graph" / "graph.json").is_file()
    agents_text = (hub / "AGENTS.md").read_text(encoding="utf-8")
    assert "indexed research system" in agents_text
    assert "obsidian/starter-vault/Home.md" in agents_text
    assert "graph/graph.json" in agents_text
    assert "resolve it through the registries" in agents_text
    assert "LLM-maintained synthesis layer" in agents_text
    assert "Open Codex" in capsys.readouterr().out


def test_init_refuses_non_empty_directory_without_force(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    hub.mkdir()
    (hub / "note.txt").write_text("keep me", encoding="utf-8")

    exit_code = main(["init", str(hub)])

    assert exit_code == 2
    assert (hub / "note.txt").read_text(encoding="utf-8") == "keep me"


def test_init_force_preserves_existing_files(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    hub.mkdir()
    (hub / "note.txt").write_text("keep me", encoding="utf-8")

    exit_code = main(["init", str(hub), "--force"])

    assert exit_code == 0
    assert (hub / "note.txt").read_text(encoding="utf-8") == "keep me"
    assert (hub / "research-os.yaml").is_file()
