from pathlib import Path
import json

import yaml

from research_os.cli import main


def test_build_graph_emits_project_nodes(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0

    exit_code = main(["build-graph", "--hub", str(hub)])

    assert exit_code == 0
    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    assert {"id": "project:auditory-demo", "type": "Project", "title": "Auditory Demo"} in graph["nodes"]


def test_build_graph_links_sources_to_projects(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "zotero_item_key": "ABCD1234",
            "projects": ["auditory-demo"],
        }
    ]
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    exit_code = main(["build-graph", "--hub", str(hub)])

    assert exit_code == 0
    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    assert {"id": "paper:smith-2024", "type": "Paper", "title": "Auditory Brainstem Responses"} in graph["nodes"]
    assert {"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"} in graph["edges"]


def test_zotero_status_reports_availability_without_crashing(capsys):
    exit_code = main(["zotero-status"])

    assert exit_code in {0, 1}
    output = capsys.readouterr().out
    assert "Zotero" in output


def test_doctor_reports_hub_and_zotero_sections(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    exit_code = main(["doctor", "--hub", str(hub)])

    assert exit_code in {0, 1}
    output = capsys.readouterr().out
    assert "Hub:" in output
    assert "Zotero:" in output
