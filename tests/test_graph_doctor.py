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
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["project:auditory-demo"]["type"] == "Project"
    assert nodes_by_id["project:auditory-demo"]["title"] == "Auditory Demo"


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
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["paper:smith-2024"]["type"] == "Paper"
    assert nodes_by_id["paper:smith-2024"]["title"] == "Auditory Brainstem Responses"
    assert {"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"} in graph["edges"]


def test_build_graph_emits_research_context_nodes_and_edges(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "status": "active",
            "obsidian_note": "Projects/auditory-demo.md",
            "folders": {"analysis": "projects/auditory-demo/analysis"},
            "zotero_collections": ["ABR"],
            "zotero_collection_keys": ["G6CDLFHD"],
            "tags": ["auditory-neuroscience"],
        }
    ]
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "citation_key": "smith2024demo",
            "zotero_item_key": "ABCD1234",
            "zotero_attachment_key": "PDF1234",
            "doi": "10.1000/demo",
            "projects": ["auditory-demo"],
            "concepts": ["auditory-brainstem-response"],
            "zotero_collections": ["ABR"],
            "roles": ["reference_paper"],
            "tags": ["abr"],
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert nodes_by_id["project:auditory-demo"]["metadata"]["tags"] == ["auditory-neuroscience"]
    assert nodes_by_id["project:auditory-demo"]["metadata"]["obsidian_note"] == "Projects/auditory-demo.md"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["citation_key"] == "smith2024demo"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["roles"] == ["reference_paper"]
    assert nodes_by_id["concept:auditory-brainstem-response"]["title"] == "auditory brainstem response"
    assert nodes_by_id["collection:ABR"]["metadata"]["zotero_collection_key"] == "G6CDLFHD"
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["path"] == "projects/auditory-demo/analysis"

    assert {"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"} in graph["edges"]
    assert {
        "source": "paper:smith-2024",
        "target": "concept:auditory-brainstem-response",
        "type": "has_concept",
    } in graph["edges"]
    assert {"source": "project:auditory-demo", "target": "collection:ABR", "type": "in_collection"} in graph["edges"]
    assert {"source": "paper:smith-2024", "target": "collection:ABR", "type": "in_collection"} in graph["edges"]
    assert {
        "source": "project:auditory-demo",
        "target": "folder:auditory-demo:analysis",
        "type": "attached_folder",
    } in graph["edges"]


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
