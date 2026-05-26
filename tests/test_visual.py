from pathlib import Path

import json

from research_os.cli import main
from research_os.config import Hub
from research_os.visual import render_visual_html, write_visual


def test_render_visual_html_embeds_graph_data():
    dangerous_value = "</script><script>alert(1)</script> & <tag>"
    graph = {
        "nodes": [
            {
                "id": "project:demo",
                "type": "Project",
                "title": dangerous_value,
                "metadata": {"note": dangerous_value},
            },
            {"id": "paper:demo", "type": "Paper", "title": "Paper Demo"},
            {"id": "concept:demo", "type": "Concept", "title": "Concept Demo"},
            {"id": "collection:demo", "type": "Collection", "title": "Collection Demo"},
            {"id": "folder:demo", "type": "Folder", "title": "Folder Demo"},
            {"id": "dataset:demo", "type": "Dataset", "title": "Dataset Demo"},
        ],
        "edges": [{"source": "project:demo", "target": "paper:demo", "type": "uses"}],
    }

    html = render_visual_html(graph)

    assert "<title>Research OS Visual Explorer</title>" in html
    assert '<script id="research-os-graph-data" type="application/json">' in html
    assert dangerous_value not in html
    assert (
        "\\u003c/script\\u003e\\u003cscript\\u003ealert(1)"
        "\\u003c/script\\u003e \\u0026 \\u003ctag\\u003e"
    ) in html
    assert "Project" in html
    assert "Paper" in html
    assert "Concept" in html
    assert "Collection" in html
    assert "Folder" in html
    assert "Dataset" in html
    assert "Universe" in html
    assert "Zotero Library" in html
    assert "Global Wiki" in html
    assert "Research Projects" not in html
    assert "Project Map" not in html
    assert "Category Map" not in html
    assert "Group View" not in html
    assert "Theme:" in html
    assert "--font-serif" in html
    assert "16px 16px" in html
    assert "circle at 50% 50%" not in html
    assert "react-flow" in html
    assert "research-os-graph-data" in html
    assert "__RESEARCH_OS_GRAPH_DATA__" not in html
    assert "html[data-theme=dark]" in html
    assert "html[data-theme=light]" in html


def test_write_visual_creates_visual_index(tmp_path: Path):
    hub = Hub(path=tmp_path, config={})
    graph = {"nodes": [], "edges": []}

    visual_path = write_visual(hub, graph)

    assert visual_path == tmp_path / "visual" / "index.html"
    assert visual_path.is_file()
    assert "Research OS Visual Explorer" in visual_path.read_text(encoding="utf-8")


def test_build_visual_cli_reads_graph_and_writes_dashboard(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    assert main(["build-graph", "--hub", str(hub)]) == 0

    exit_code = main(["build-visual", "--hub", str(hub)])

    assert exit_code == 0
    assert (hub / "graph" / "graph.json").is_file()
    html = (hub / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Auditory Demo" in html
    assert "project:auditory-demo" in html


def test_build_visual_cli_reads_existing_graph_without_rebuilding(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    graph_path = hub / "graph" / "graph.json"
    graph = {
        "nodes": [{"id": "project:visual-only", "type": "Project", "title": "Visual Only"}],
        "edges": [],
    }
    graph_path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    assert main(["build-visual", "--hub", str(hub)]) == 0

    assert json.loads(graph_path.read_text(encoding="utf-8")) == graph
    html = (hub / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Visual Only" in html
    assert "Auditory Demo" not in html
