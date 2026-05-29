from pathlib import Path

import yaml

from research_os.cli import main


def test_integrate_source_marks_wiki_inbox_item_complete_and_logs(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    source = {
        "id": "paper:smith-2024",
        "type": "Paper",
        "title": "Auditory Brainstem Responses",
        "citation_key": "smith2024demo",
        "projects": ["auditory-demo"],
        "concepts": ["auditory-brainstem-response"],
    }
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump([source], sort_keys=False), encoding="utf-8")
    inbox_path = hub / "obsidian" / "research-os" / "wiki" / "inbox.md"
    inbox_path.write_text(
        "# Wiki Integration Inbox\n\n- [ ] paper:smith-2024 -> academic-paper (queued after Zotero ingest)\n",
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["integrate-source", "paper:smith-2024", "--hub", str(hub)]) == 0

    output = capsys.readouterr().out
    assert "integrated source: paper:smith-2024" in output
    assert "- [x] paper:smith-2024 -> academic-paper (queued after Zotero ingest)" in inbox_path.read_text(
        encoding="utf-8"
    )
    log_text = (hub / "obsidian" / "research-os" / "log.md").read_text(encoding="utf-8")
    assert "Integrated source | Auditory Brainstem Responses" in log_text
    assert "paper:smith-2024" in log_text


def test_integrate_source_refuses_source_not_in_wiki_inbox(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    source = {"id": "paper:smith-2024", "type": "Paper", "title": "Auditory Brainstem Responses"}
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump([source], sort_keys=False), encoding="utf-8")
    capsys.readouterr()

    assert main(["integrate-source", "paper:smith-2024", "--hub", str(hub)]) == 1

    assert "source is not queued for wiki integration: paper:smith-2024" in capsys.readouterr().out
