from pathlib import Path

import pytest

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
            }
        ],
        "edges": [{"source": "project:demo", "target": "paper:demo", "type": "uses"}],
    }

    html = render_visual_html(graph)

    assert "<title>Research OS Visual Explorer</title>" in html
    assert "const graphData =" in html
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


def test_write_visual_creates_visual_index(tmp_path: Path):
    hub = Hub(path=tmp_path, config={})
    graph = {"nodes": [], "edges": []}

    visual_path = write_visual(hub, graph)

    assert visual_path == tmp_path / "visual" / "index.html"
    assert visual_path.is_file()
    assert "Research OS Visual Explorer" in visual_path.read_text(encoding="utf-8")


@pytest.mark.xfail(reason="build-visual is wired in Task 3", strict=True)
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
