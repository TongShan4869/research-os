from pathlib import Path
import json

import yaml

from research_os.cli import main


class FakeZoteroClient:
    def collections(self):
        return [
            {
                "key": "G6CDLFHD",
                "name": "ABR",
                "parentCollection": "7HP8BAST",
            }
        ]

    def collection_top_items(self, collection_key: str):
        assert collection_key == "G6CDLFHD"
        return [
            {
                "key": "GBEMXBSK",
                "links": {
                    "attachment": {
                        "href": "http://localhost:23119/api/users/15426440/items/REBSD7ZN",
                        "attachmentType": "application/pdf",
                    }
                },
                "meta": {"parsedDate": "2024-01-08"},
                "data": {
                    "key": "GBEMXBSK",
                    "title": "Subcortical responses to music and speech are alike while cortical responses diverge",
                    "date": "2024-01-08",
                    "publicationTitle": "Scientific Reports",
                    "DOI": "10.1038/s41598-023-50438-0",
                    "citationKey": "shanSubcorticalResponsesMusic2024",
                    "creators": [
                        {"firstName": "Tong", "lastName": "Shan", "creatorType": "author"},
                        {"firstName": "Ross K.", "lastName": "Maddox", "creatorType": "author"},
                    ],
                },
            }
        ]


def test_ingest_zotero_collection_creates_collection_and_paper_notes(tmp_path: Path, monkeypatch):
    hub = tmp_path / "ResearchOS"
    assert main(["init", str(hub)]) == 0
    assert main(["new-project", "auditory-demo", "--hub", str(hub), "--title", "Auditory Demo"]) == 0
    monkeypatch.setattr("research_os.cli.ZoteroLocalClient", FakeZoteroClient)

    exit_code = main(["ingest-zotero-collection", "ABR", "--project", "auditory-demo", "--hub", str(hub)])

    assert exit_code == 0
    vault = hub / "obsidian" / "starter-vault"
    collection_note = vault / "Sources" / "Collections" / "ABR.md"
    paper_note = vault / "Sources" / "Papers" / "shanSubcorticalResponsesMusic2024.md"
    collection_text = collection_note.read_text(encoding="utf-8")
    paper_text = paper_note.read_text(encoding="utf-8")
    assert "zotero_collection_key: G6CDLFHD" in collection_text
    assert "zotero://select/library/collections/G6CDLFHD" in collection_text
    assert "[[Sources/Papers/shanSubcorticalResponsesMusic2024|" in collection_text
    assert "zotero_item_key: GBEMXBSK" in paper_text
    assert "zotero_attachment_key: REBSD7ZN" in paper_text
    assert "zotero://select/library/items/GBEMXBSK" in paper_text
    assert "zotero://open-pdf/library/items/REBSD7ZN" in paper_text

    sources = yaml.safe_load((hub / "registries" / "sources.yaml").read_text(encoding="utf-8"))
    assert sources == [
        {
            "id": "paper:shanSubcorticalResponsesMusic2024",
            "type": "Paper",
            "title": "Subcortical responses to music and speech are alike while cortical responses diverge",
            "zotero_item_key": "GBEMXBSK",
            "zotero_attachment_key": "REBSD7ZN",
            "citation_key": "shanSubcorticalResponsesMusic2024",
            "doi": "10.1038/s41598-023-50438-0",
            "projects": ["auditory-demo"],
            "concepts": [],
        }
    ]
    graph = json.loads((hub / "graph" / "graph.json").read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    source_node = nodes_by_id["paper:shanSubcorticalResponsesMusic2024"]
    assert source_node["title"] == "Subcortical responses to music and speech are alike while cortical responses diverge"
    assert source_node["type"] == "Paper"
    assert source_node["metadata"]["zotero_item_key"] == "GBEMXBSK"
    assert source_node["metadata"]["zotero_attachment_key"] == "REBSD7ZN"
    assert source_node["metadata"]["citation_key"] == "shanSubcorticalResponsesMusic2024"
    assert source_node["metadata"]["doi"] == "10.1038/s41598-023-50438-0"
    assert source_node["metadata"]["projects"] == ["auditory-demo"]
    assert {"source": "project:auditory-demo", "target": "paper:shanSubcorticalResponsesMusic2024", "type": "uses"} in graph["edges"]
