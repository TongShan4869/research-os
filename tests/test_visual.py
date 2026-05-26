from pathlib import Path
import json

from research_os.cli import main
from research_os.config import Hub
from research_os.visual import render_visual_html, write_visual


def test_render_visual_html_embeds_graph_data():
    graph = {
        "nodes": [{"id": "project:demo", "type": "Project", "title": "Demo Project"}],
        "edges": [{"source": "project:demo", "target": "paper:demo", "type": "uses"}],
    }

    html = render_visual_html(graph)

    assert "<title>Research OS Visual Explorer</title>" in html
    assert "const graphData =" in html
    assert json.dumps(graph, sort_keys=True) in html
    assert "Project" in html
    assert "Paper" in html
    assert "Concept" in html
    assert "Collection" in html
    assert "Folder" in html


def test_write_visual_creates_visual_index(tmp_path: Path):
    hub = Hub(path=tmp_path, config={})
    graph = {"nodes": [], "edges": []}

    visual_path = write_visual(hub, graph)

    assert visual_path == tmp_path / "visual" / "index.html"
    assert visual_path.is_file()
    assert "Research OS Visual Explorer" in visual_path.read_text(encoding="utf-8")


def test_build_visual_cli_rebuilds_graph_and_writes_dashboard(tmp_path: Path):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0

    exit_code = main(["build-visual", "--hub", str(hub)])

    assert exit_code == 0
    assert (hub / "graph" / "graph.json").is_file()
    html = (hub / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Auditory Demo" in html
    assert "project:auditory-demo" in html
