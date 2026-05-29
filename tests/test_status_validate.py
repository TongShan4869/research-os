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
    assert "projects: 0" in output


def test_validate_reports_missing_required_file(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)
    (hub / "AGENTS.md").unlink()

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 1
    assert "missing required file: AGENTS.md" in capsys.readouterr().out


def test_validate_reports_missing_wiki_core(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)
    (hub / "obsidian" / "research-os" / "index.md").unlink()

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 1
    assert "missing required file: obsidian/research-os/index.md" in capsys.readouterr().out


def test_validate_reports_invalid_project_registry_shape(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)
    (hub / "registries" / "projects.yaml").write_text("id: not-a-list\n", encoding="utf-8")

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 1
    assert "registries/projects.yaml must contain a list" in capsys.readouterr().out


def test_validate_accepts_fresh_hub(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 0
    assert "hub is valid" in capsys.readouterr().out


def test_validate_accepts_legacy_null_configured_starter_vault(tmp_path: Path, capsys):
    hub = make_hub(tmp_path)
    (hub / "research-os.yaml").write_text(
        (hub / "research-os.yaml").read_text(encoding="utf-8").replace(
            "obsidian_vault: obsidian/research-os",
            "obsidian_vault: null",
        ),
        encoding="utf-8",
    )
    (hub / "obsidian" / "research-os").rename(hub / "obsidian" / "starter-vault")

    exit_code = main(["validate", "--hub", str(hub)])

    assert exit_code == 0
    assert "hub is valid" in capsys.readouterr().out
