from pathlib import Path

import yaml

from research_os.cli import main
from research_os.config import load_hub
from research_os.graph import build_graph, graph_from_registries


def test_build_index_creates_home_note_from_registries(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    projects_path = hub / "registries" / "projects.yaml"
    projects = yaml.safe_load(projects_path.read_text(encoding="utf-8"))
    projects[0]["zotero_collections"] = ["ABR"]
    projects[0]["tags"] = ["auditory-neuroscience"]
    projects_path.write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    sources = [
        {
            "id": "paper:shanSubcorticalResponsesMusic2024",
            "type": "Paper",
            "title": "Subcortical responses to music and speech are alike while cortical responses diverge",
            "citation_key": "shanSubcorticalResponsesMusic2024",
            "zotero_item_key": "GBEMXBSK",
            "projects": ["auditory-demo"],
            "concepts": [],
        },
        {
            "id": "paper:unlinked",
            "type": "Paper",
            "title": "Unlinked Source",
            "citation_key": "unlinkedSource",
            "zotero_item_key": "UNLINKED1",
            "projects": [],
            "concepts": [],
        },
    ]
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    exit_code = main(["build-index", "--hub", str(hub)])

    assert exit_code == 0
    home = hub / "obsidian" / "starter-vault" / "Home.md"
    text = home.read_text(encoding="utf-8")
    assert "type: research_os_home" in text
    assert "# Research OS" in text
    assert "## Visual Explorer" in text
    assert "[Open visual explorer](../../visual/index.html)" in text
    assert "- Graph: 4 nodes, 2 edges" in text
    assert text.index("# Research OS") < text.index("## Visual Explorer") < text.index("## Projects")
    project_row = (
        "| [[Projects/auditory-demo\\|Auditory Demo]] | active | "
        "[[Sources/Collections/ABR\\|ABR]] | 1 | auditory-neuroscience |"
    )
    assert project_row in text
    assert len(project_row.split(" | ")) == 5
    assert "- [[Sources/Collections/ABR|ABR]]: 1 linked project" in text
    assert "- [[Sources/Papers/shanSubcorticalResponsesMusic2024|Subcortical responses to music and speech are alike while cortical responses diverge]]" in text
    assert "- Sources with no linked project: 1" in text
    assert "- Sources with no concepts: 2" in text


def test_build_index_uses_canonical_graph_counts_with_drift_prone_registries(tmp_path: Path):
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
        }
    ]
    (hub / "registries" / "projects.yaml").write_text(yaml.safe_dump(projects, sort_keys=False), encoding="utf-8")
    (hub / "registries" / "sources.yaml").write_text(yaml.safe_dump(sources, sort_keys=False), encoding="utf-8")

    assert main(["build-index", "--hub", str(hub)]) == 0

    graph = graph_from_registries(projects, sources)
    assert build_graph(load_hub(hub)) == graph
    graph_line = f"- Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges"
    text = (hub / "obsidian" / "starter-vault" / "Home.md").read_text(encoding="utf-8")
    assert graph_line == "- Graph: 5 nodes, 6 edges"
    assert graph_line in text
