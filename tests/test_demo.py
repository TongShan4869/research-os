from pathlib import Path

from research_os.cli import main


def test_demo_workspace_validates():
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo-research-workspace"

    assert main(["validate", "--hub", str(demo)]) == 0


def test_demo_workspace_builds_graph():
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo-research-workspace"

    assert main(["build-graph", "--hub", str(demo)]) == 0
    assert (demo / "graph" / "graph.json").is_file()
