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


def test_demo_obsidian_vault_has_linked_notes_for_graph_view():
    repo = Path(__file__).resolve().parents[1]
    vault = repo / "examples" / "demo-research-workspace" / "obsidian" / "starter-vault"

    markdown_notes = list(vault.rglob("*.md"))
    combined_text = "\n".join(note.read_text(encoding="utf-8") for note in markdown_notes)

    assert vault.joinpath("Projects", "auditory-demo.md").is_file()
    assert vault.joinpath("Sources", "Papers", "smith-2024.md").is_file()
    assert vault.joinpath("Concepts", "auditory-brainstem-response.md").is_file()
    assert "[[Sources/Papers/smith-2024|Auditory Brainstem Responses In Demo Conditions]]" in combined_text
    assert "[[Concepts/auditory-brainstem-response|Auditory brainstem response]]" in combined_text


def test_demo_obsidian_notes_have_auto_assigned_tags():
    repo = Path(__file__).resolve().parents[1]
    vault = repo / "examples" / "demo-research-workspace" / "obsidian" / "starter-vault"

    project_note = vault / "Projects" / "auditory-demo.md"
    paper_note = vault / "Sources" / "Papers" / "smith-2024.md"
    concept_note = vault / "Concepts" / "auditory-brainstem-response.md"

    assert "  - research-os/project" in project_note.read_text(encoding="utf-8")
    assert "  - project/auditory-demo" in project_note.read_text(encoding="utf-8")
    assert "  - topic/auditory-neuroscience" in project_note.read_text(encoding="utf-8")
    assert "  - research-os/paper" in paper_note.read_text(encoding="utf-8")
    assert "  - research-os/concept" in concept_note.read_text(encoding="utf-8")


def test_demo_links_real_zotero_abr_collection():
    repo = Path(__file__).resolve().parents[1]
    vault = repo / "examples" / "demo-research-workspace" / "obsidian" / "starter-vault"

    collection_note = vault / "Sources" / "Collections" / "ABR.md"
    paper_note = vault / "Sources" / "Papers" / "shanSubcorticalResponsesMusic2024.md"

    assert "zotero_collection_key: G6CDLFHD" in collection_note.read_text(encoding="utf-8")
    assert "zotero://select/library/collections/G6CDLFHD" in collection_note.read_text(encoding="utf-8")
    assert "zotero_item_key: GBEMXBSK" in paper_note.read_text(encoding="utf-8")
    assert "zotero_attachment_key: REBSD7ZN" in paper_note.read_text(encoding="utf-8")
    assert "zotero://select/library/items/GBEMXBSK" in paper_note.read_text(encoding="utf-8")
    assert "zotero://open-pdf/library/items/REBSD7ZN" in paper_note.read_text(encoding="utf-8")


def test_demo_workspace_builds_visual_explorer():
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo-research-workspace"

    assert main(["build-visual", "--hub", str(demo)]) == 0
    assert (demo / "visual" / "index.html").is_file()
    visual_html = (demo / "visual" / "index.html").read_text(encoding="utf-8")
    assert "Research OS Visual Explorer" in visual_html
    assert "Auditory Demo Project" in visual_html
