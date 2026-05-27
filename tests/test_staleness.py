from pathlib import Path
import json

import yaml

from research_os.cli import main


def test_generated_surfaces_store_fingerprints(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    assert main(["build-index", "--hub", str(hub)]) == 0
    assert main(["build-graph", "--hub", str(hub)]) == 0
    assert main(["build-visual", "--hub", str(hub)]) == 0
    capsys.readouterr()

    home = (hub / "obsidian" / "starter-vault" / "Home.md").read_text(encoding="utf-8")
    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    visual = (hub / "visual" / "index.html").read_text(encoding="utf-8")

    assert "research_os_fingerprint:" in home
    assert "- Home context fingerprint: `" in home
    assert graph["metadata"]["research_os_fingerprint"]
    assert visual.startswith("<!-- research-os:")


def test_context_health_reports_current_and_stale_surfaces(tmp_path: Path, capsys):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--title", "Auditory Demo", "--hub", str(hub)]) == 0
    assert main(["build-index", "--hub", str(hub)]) == 0
    assert main(["build-graph", "--hub", str(hub)]) == 0
    assert main(["build-visual", "--hub", str(hub)]) == 0
    capsys.readouterr()

    assert main(["context-health", "--hub", str(hub)]) == 0
    output = capsys.readouterr().out
    assert "- Home.md: current" in output
    assert "- graph.json: current" in output
    assert "- visual/index.html: current" in output

    sources_path = hub / "registries" / "sources.yaml"
    sources_path.write_text(
        yaml.safe_dump([{"id": "paper:smith", "title": "Smith Paper", "projects": ["auditory-demo"]}], sort_keys=False),
        encoding="utf-8",
    )

    assert main(["context-health", "--hub", str(hub)]) == 1
    output = capsys.readouterr().out
    assert "- Home.md: stale" in output
    assert "- graph.json: stale" in output
    assert "- visual/index.html: current" in output
