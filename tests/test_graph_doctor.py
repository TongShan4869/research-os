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
            "concepts": ["auditory-system"],
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

    assert nodes_by_id["project:auditory-demo"]["metadata"]["status"] == "active"
    assert nodes_by_id["project:auditory-demo"]["metadata"]["tags"] == ["auditory-neuroscience"]
    assert nodes_by_id["project:auditory-demo"]["metadata"]["obsidian_note"] == "Projects/auditory-demo.md"
    assert nodes_by_id["project:auditory-demo"]["metadata"]["zotero_collections"] == ["ABR"]
    assert nodes_by_id["project:auditory-demo"]["metadata"]["zotero_collection_keys"] == ["G6CDLFHD"]
    assert nodes_by_id["project:auditory-demo"]["description"] == (
        "Active research project; tagged auditory-neuroscience; linked to ABR."
    )
    assert nodes_by_id["paper:smith-2024"]["metadata"]["citation_key"] == "smith2024demo"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["projects"] == ["auditory-demo"]
    assert nodes_by_id["paper:smith-2024"]["metadata"]["concepts"] == ["auditory-brainstem-response"]
    assert nodes_by_id["paper:smith-2024"]["metadata"]["doi"] == "10.1000/demo"
    assert nodes_by_id["paper:smith-2024"]["metadata"]["roles"] == ["reference_paper"]
    assert nodes_by_id["paper:smith-2024"]["metadata"]["tags"] == ["abr"]
    assert nodes_by_id["paper:smith-2024"]["metadata"]["zotero_collections"] == ["ABR"]
    assert nodes_by_id["paper:smith-2024"]["description"] == (
        "Paper linked to auditory-demo about auditory brainstem response."
    )
    assert nodes_by_id["concept:auditory-system"]["title"] == "auditory system"
    assert nodes_by_id["concept:auditory-system"]["description"].startswith(
        "Auditory system is an indexed Research OS concept"
    )
    assert (hub / "obsidian" / "research-os" / "Concepts" / "auditory-system.md").is_file()
    assert nodes_by_id["concept:auditory-brainstem-response"]["title"] == "auditory brainstem response"
    assert nodes_by_id["collection:G6CDLFHD"]["title"] == "ABR"
    assert nodes_by_id["collection:G6CDLFHD"]["metadata"]["zotero_collection_key"] == "G6CDLFHD"
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["kind"] == "analysis"
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["path"] == "projects/auditory-demo/analysis"
    assert nodes_by_id["folder:auditory-demo:analysis"]["description"] == "Analysis folder attached to auditory-demo."

    assert {"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"} in graph["edges"]
    assert {"source": "project:auditory-demo", "target": "concept:auditory-system", "type": "has_concept"} in graph["edges"]
    assert {
        "source": "project:auditory-demo",
        "target": "concept:auditory-brainstem-response",
        "type": "has_concept",
    } in graph["edges"]
    assert {
        "source": "paper:smith-2024",
        "target": "concept:auditory-brainstem-response",
        "type": "has_concept",
    } in graph["edges"]
    assert {"source": "project:auditory-demo", "target": "collection:G6CDLFHD", "type": "in_collection"} in graph[
        "edges"
    ]
    assert {"source": "paper:smith-2024", "target": "collection:G6CDLFHD", "type": "in_collection"} in graph[
        "edges"
    ]
    assert {
        "source": "project:auditory-demo",
        "target": "folder:auditory-demo:analysis",
        "type": "attached_folder",
    } in graph["edges"]


def test_build_graph_includes_provider_neutral_files_and_relations(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    projects = [{"id": "auditory-demo", "title": "Auditory Demo"}]
    files = [
        {
            "id": "file:auditory-demo:data-raw-csv",
            "type": "Dataset",
            "title": "raw.csv",
            "path": "projects/auditory-demo/data/raw.csv",
            "projects": ["auditory-demo"],
            "roles": ["dataset"],
            "provider": {"name": "local_folder"},
            "review": {"status": "confirmed"},
        }
    ]
    relations = [
        {
            "source": "file:auditory-demo:data-raw-csv",
            "target": "project:auditory-demo",
            "type": "belongs_to_project",
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "files.yaml").write_text(yaml.safe_dump(files, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "relations.yaml").write_text(yaml.safe_dump(relations, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["file:auditory-demo:data-raw-csv"]["type"] == "Dataset"
    assert nodes_by_id["file:auditory-demo:data-raw-csv"]["metadata"]["roles"] == ["dataset"]
    assert nodes_by_id["file:auditory-demo:data-raw-csv"]["metadata"]["provider"]["name"] == "local_folder"
    assert nodes_by_id["file:auditory-demo:data-raw-csv"]["metadata"]["review"]["status"] == "confirmed"
    assert nodes_by_id["file:auditory-demo:data-raw-csv"]["description"] == (
        "Dataset serving as dataset for auditory-demo."
    )
    assert {
        "source": "file:auditory-demo:data-raw-csv",
        "target": "project:auditory-demo",
        "type": "belongs_to_project",
    } in graph["edges"]


def test_build_graph_uses_concept_note_definition(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    projects = [{"id": "auditory-demo", "title": "Auditory Demo", "concepts": ["auditory-brainstem-response"]}]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    concept_note = hub / "obsidian" / "research-os" / "Concepts" / "auditory-brainstem-response.md"
    concept_note.parent.mkdir(parents=True, exist_ok=True)
    concept_note.write_text(
        "---\ntype: concept\n---\n\n# Auditory Brainstem Response\n\n"
        "## Definition\n\n"
        "Auditory brainstem response is an early evoked neural response generated by auditory brainstem pathways after sound onset.\n",
        encoding="utf-8",
    )

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["concept:auditory-brainstem-response"]["description"] == (
        "Auditory brainstem response is an early evoked neural response generated by auditory brainstem pathways after sound onset."
    )
    assert nodes_by_id["concept:auditory-brainstem-response"]["metadata"]["description_source"] == {
        "kind": "obsidian_note",
        "path": "Concepts/auditory-brainstem-response.md",
        "section": "Definition",
    }


def test_build_graph_creates_missing_concept_notes_from_registries(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    sources = [
        {
            "id": "paper:smith-2024",
            "type": "Paper",
            "title": "Speech EEG",
            "projects": ["auditory-demo"],
            "concepts": ["continuous-speech"],
        }
    ]
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    concept_note = hub / "obsidian" / "research-os" / "Concepts" / "continuous-speech.md"
    assert concept_note.is_file()
    assert "## Definition" in concept_note.read_text(encoding="utf-8")

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["concept:continuous-speech"]["description"] != (
        "Concept definition missing for continuous speech. Add it to the matching Concepts note."
    )
    assert nodes_by_id["concept:continuous-speech"]["metadata"]["description_source"] == {
        "kind": "obsidian_note",
        "path": "Concepts/continuous-speech.md",
        "section": "Definition",
    }


def test_build_graph_ignores_blank_explicit_fields_and_deduplicates_edges(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": " auditory-demo ",
            "title": "Auditory Demo",
            "folders": {
                " analysis ": " projects/auditory-demo/analysis ",
                "   ": "projects/auditory-demo/blank-kind",
                "figures": "   ",
            },
            "concepts": [" auditory-brainstem-response ", "auditory-brainstem-response", "   "],
            "zotero_collections": [" ABR ", "ABR", ""],
            "zotero_collection_keys": [" G6CDLFHD "],
        }
    ]
    sources = [
        {
            "id": " paper:smith-2024 ",
            "type": "Paper",
            "title": "Auditory Brainstem Responses",
            "projects": [" auditory-demo ", "auditory-demo", "   "],
            "concepts": [" auditory-brainstem-response ", "auditory-brainstem-response", ""],
            "zotero_collections": [" ABR ", "ABR", "   "],
            "tags": [" abr ", ""],
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in graph["nodes"]}
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert "concept:unknown" not in node_ids
    assert "collection:unknown" not in node_ids
    assert "folder:auditory-demo:unknown" not in node_ids
    assert "folder:auditory-demo:figures" not in node_ids
    assert nodes_by_id["project:auditory-demo"]["metadata"]["zotero_collections"] == ["ABR", "ABR"]
    assert nodes_by_id["project:auditory-demo"]["metadata"]["zotero_collection_keys"] == ["G6CDLFHD"]
    assert nodes_by_id["collection:G6CDLFHD"]["title"] == "ABR"
    assert "collection:ABR" not in node_ids
    assert nodes_by_id["paper:smith-2024"]["metadata"]["tags"] == ["abr"]
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["kind"] == "analysis"
    assert nodes_by_id["folder:auditory-demo:analysis"]["metadata"]["path"] == "projects/auditory-demo/analysis"
    assert graph["edges"].count(
        {"source": "project:auditory-demo", "target": "concept:auditory-brainstem-response", "type": "has_concept"}
    ) == 1
    assert graph["edges"].count(
        {"source": "paper:smith-2024", "target": "concept:auditory-brainstem-response", "type": "has_concept"}
    ) == 1
    assert graph["edges"].count(
        {"source": "project:auditory-demo", "target": "collection:G6CDLFHD", "type": "in_collection"}
    ) == 1
    assert graph["edges"].count({"source": "project:auditory-demo", "target": "paper:smith-2024", "type": "uses"}) == 1


def test_build_graph_preserves_collection_key_alignment_with_blank_keys(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "zotero_collections": ["ABR", "Other"],
            "zotero_collection_keys": ["", "KEY2"],
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert nodes_by_id["project:auditory-demo"]["metadata"]["zotero_collection_keys"] == ["", "KEY2"]
    assert "zotero_collection_key" not in nodes_by_id["collection:ABR"].get("metadata", {})
    assert nodes_by_id["collection:KEY2"]["title"] == "Other"
    assert nodes_by_id["collection:KEY2"]["metadata"]["zotero_collection_key"] == "KEY2"


def test_build_graph_keeps_explicit_blank_collection_keys_name_based(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "zotero_collections": ["ABR", "ABR"],
            "zotero_collection_keys": ["G6CDLFHD", ""],
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert nodes_by_id["collection:G6CDLFHD"]["title"] == "ABR"
    assert nodes_by_id["collection:G6CDLFHD"]["metadata"]["zotero_collection_key"] == "G6CDLFHD"
    assert nodes_by_id["collection:ABR"]["title"] == "ABR"
    assert "zotero_collection_key" not in nodes_by_id["collection:ABR"].get("metadata", {})
    assert {"source": "project:auditory-demo", "target": "collection:G6CDLFHD", "type": "in_collection"} in graph[
        "edges"
    ]
    assert {"source": "project:auditory-demo", "target": "collection:ABR", "type": "in_collection"} in graph[
        "edges"
    ]


def test_build_graph_uses_collection_keys_to_distinguish_duplicate_collection_titles(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0

    projects = [
        {
            "id": "auditory-demo",
            "title": "Auditory Demo",
            "zotero_collections": ["ABR"],
            "zotero_collection_keys": ["G6CDLFHD"],
        },
        {
            "id": "clinical-demo",
            "title": "Clinical Demo",
            "zotero_collections": ["ABR"],
            "zotero_collection_keys": ["CLINICAL1"],
        },
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")

    assert main(["build-graph", "--hub", str(hub)]) == 0

    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}

    assert nodes_by_id["collection:G6CDLFHD"]["title"] == "ABR"
    assert nodes_by_id["collection:G6CDLFHD"]["metadata"]["zotero_collection_key"] == "G6CDLFHD"
    assert nodes_by_id["collection:CLINICAL1"]["title"] == "ABR"
    assert nodes_by_id["collection:CLINICAL1"]["metadata"]["zotero_collection_key"] == "CLINICAL1"
    assert {"source": "project:auditory-demo", "target": "collection:G6CDLFHD", "type": "in_collection"} in graph[
        "edges"
    ]
    assert {"source": "project:clinical-demo", "target": "collection:CLINICAL1", "type": "in_collection"} in graph[
        "edges"
    ]


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
