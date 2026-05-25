from pathlib import Path

import yaml

from research_os.cli import main


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
    assert "| [[Projects/auditory-demo|Auditory Demo]] | active | [[Sources/Collections/ABR|ABR]] | 1 | auditory-neuroscience |" in text
    assert "- [[Sources/Collections/ABR|ABR]]: 1 linked project" in text
    assert "- [[Sources/Papers/shanSubcorticalResponsesMusic2024|Subcortical responses to music and speech are alike while cortical responses diverge]]" in text
    assert "- Sources with no linked project: 1" in text
    assert "- Sources with no concepts: 2" in text
