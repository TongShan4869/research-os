from pathlib import Path
import json

import yaml

from research_os.cli import main


def test_context_outputs_agent_packet_for_project(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "status": "active",
            "obsidian_note": "Projects/auditory-demo.md",
            "folders": {"analysis": "projects/auditory-demo/analysis"},
            "tags": ["auditory-neuroscience"],
        }
    ]
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "projects": ["auditory-demo"],
            "concepts": ["auditory-brainstem-response"],
            "roles": ["reference_paper"],
            "provider": {"name": "zotero", "key": "ABCD1234"},
        }
    ]
    files = [
        {
            "id": "file:auditory-demo:figures-waveform-png",
            "type": "Figure",
            "title": "Waveform figure",
            "path": "projects/auditory-demo/figures/waveform.png",
            "projects": ["auditory-demo"],
            "roles": ["figure"],
            "provider": {"name": "local_folder"},
            "review": {"status": "confirmed"},
        }
    ]
    relations = [
        {
            "source": "file:auditory-demo:figures-waveform-png",
            "target": "project:auditory-demo",
            "type": "belongs_to_project",
        }
    ]
    proposals = [
        {
            "id": "proposal:data-csv",
            "path": "projects/auditory-demo/data/raw.csv",
            "proposed_type": "Dataset",
            "proposed_project": "auditory-demo",
            "status": "pending",
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "files.yaml").write_text(yaml.safe_dump(files, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "relations.yaml").write_text(yaml.safe_dump(relations, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "inbox.yaml").write_text(yaml.safe_dump(proposals, sort_keys=False), encoding="utf-8")
    capsys.readouterr()

    assert main(["context", "auditory-demo", "--hub", str(hub), "--json"]) == 0

    packet = json.loads(capsys.readouterr().out)
    assert packet["query"] == "auditory-demo"
    assert packet["match"]["id"] == "project:auditory-demo"
    assert packet["projects"][0]["id"] == "auditory-demo"
    assert packet["sources"][0]["id"] == "paper:smith-2024"
    assert packet["files"][0]["id"] == "file:auditory-demo:figures-waveform-png"
    assert packet["relations"][0]["type"] == "belongs_to_project"
    assert packet["concepts"] == ["auditory-brainstem-response"]
    assert packet["inbox"][0]["id"] == "proposal:data-csv"


def test_context_outputs_markdown_summary(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    capsys.readouterr()

    assert main(["context", "auditory-demo", "--hub", str(hub)]) == 0

    output = capsys.readouterr().out
    assert "# Context Packet: Auditory Demo" in output
    assert "## Projects" in output
    assert "- auditory-demo: Auditory Demo" in output


def test_context_json_serializes_yaml_dates(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    (hub / "registries" / "projects.yaml").write_text(
        "- id: auditory-demo\n  title: Auditory Demo\n  created: 2026-05-27\n",
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["context", "auditory-demo", "--hub", str(hub), "--json"]) == 0

    packet = json.loads(capsys.readouterr().out)
    assert packet["projects"][0]["created"] == "2026-05-27"


def test_context_packet_includes_relevant_wiki_pages(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    vault = hub / "obsidian" / "starter-vault"
    (vault / "index.md").write_text(
        "# Wiki Index\n\n- [[Synthesis/auditory-demo|Auditory Demo synthesis]] - project synthesis for auditory-demo\n",
        encoding="utf-8",
    )
    (vault / "Synthesis").mkdir(exist_ok=True)
    (vault / "Synthesis" / "auditory-demo.md").write_text("# Auditory Demo synthesis\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["context", "auditory-demo", "--hub", str(hub), "--json"]) == 0

    packet = json.loads(capsys.readouterr().out)
    assert packet["wiki_pages"] == [
        {
            "path": "Synthesis/auditory-demo.md",
            "title": "Auditory Demo synthesis",
            "summary": "project synthesis for auditory-demo",
        }
    ]


def test_context_resolves_project_source_file_folder_collection_and_wiki_terms(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    project_root = hub / "projects" / "auditory-demo"
    (project_root / "analysis").mkdir(parents=True)
    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "status": "active",
            "obsidian_note": "Projects/auditory-demo.md",
            "folders": {"analysis": "projects/auditory-demo/analysis"},
            "tags": ["demo-tag"],
            "concepts": ["auditory-brainstem-response"],
            "zotero_collections": ["ABR"],
        }
    ]
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "citation_key": "smith2024demo",
            "projects": ["auditory-demo"],
            "tags": ["paper-tag"],
            "concepts": ["auditory-brainstem-response"],
            "zotero_collections": ["ABR"],
        }
    ]
    files = [
        {
            "id": "file:auditory-demo:raw-csv",
            "type": "Dataset",
            "title": "Raw ABR data",
            "path": "projects/auditory-demo/data/raw.csv",
            "projects": ["auditory-demo"],
            "tags": ["file-tag"],
            "concepts": ["auditory-brainstem-response"],
        }
    ]
    vault = hub / "obsidian" / "starter-vault"
    (vault / "index.md").write_text(
        "# Wiki Index\n\n- [[Synthesis/auditory-demo|ABR synthesis]] - project synthesis for auditory-demo\n",
        encoding="utf-8",
    )
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "files.yaml").write_text(yaml.safe_dump(files, sort_keys=False), encoding="utf-8")
    capsys.readouterr()

    queries = [
        "Auditory Demo",
        "demo-tag",
        "auditory-brainstem-response",
        "projects/auditory-demo/analysis",
        "ABR",
        "smith2024demo",
        "projects/auditory-demo/data/raw.csv",
        "ABR synthesis",
    ]
    for query in queries:
        assert main(["context", query, "--hub", str(hub), "--json"]) == 0
        packet = json.loads(capsys.readouterr().out)
        assert packet["projects"][0]["id"] == "auditory-demo", query


def test_context_unresolved_query_returns_clear_error(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    capsys.readouterr()

    assert main(["context", "not-a-real-project", "--hub", str(hub)]) == 1

    assert "context unresolved: not-a-real-project" in capsys.readouterr().out
