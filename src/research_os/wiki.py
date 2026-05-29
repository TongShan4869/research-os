from __future__ import annotations

from datetime import date
import re
from pathlib import Path

from research_os.config import Hub
from research_os.paths import obsidian_vault_path


WIKI_DIRS = ["Synthesis", "Entities", "Concepts", "Claims", "Methods", "Datasets", "Results"]
INDEXED_SOURCES_START = "<!-- research-os:indexed-sources:start -->"
INDEXED_SOURCES_END = "<!-- research-os:indexed-sources:end -->"
FOLDER_GUIDE = [
    {
        "folder": "Projects/",
        "use": "Project goals, status, linked sources, and open questions.",
        "home_use": "One page per research project: goals, scope, linked sources, open questions.",
        "maintainer": "Human plus LLM",
    },
    {
        "folder": "Sources/",
        "use": "Notes for papers, collections, articles, files, and provider metadata.",
        "home_use": "Source notes for papers, Zotero collections, articles, files, and raw-provider links.",
        "maintainer": "LLM after user-approved ingest",
    },
    {
        "folder": "Synthesis/",
        "use": "Evolving summaries that combine multiple sources.",
        "home_use": "Evolving project or topic summaries that combine many sources. Start reading here.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Concepts/",
        "use": "Concept explainers and definitions.",
        "home_use": "Stable concept explainer pages, linked from projects, sources, and syntheses.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Entities/",
        "use": "Named people, labs, tools, institutions, places, or organisms.",
        "home_use": "People, labs, tools, organisms, places, institutions, or other named things.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Claims/",
        "use": "Evidence-backed statements, contradictions, and disputed findings.",
        "home_use": "Atomic evidence-backed claims, especially contested or important ones.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Methods/",
        "use": "Protocols, models, measures, analyses, and workflows.",
        "home_use": "Protocols, analysis methods, measures, models, and workflows.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Datasets/",
        "use": "Dataset provenance, schema, paths, and usage notes.",
        "home_use": "Dataset pages with provenance, variables, access paths, and related outputs.",
        "maintainer": "LLM-maintained",
    },
    {
        "folder": "Results/",
        "use": "Findings, figures, tables, outputs, and interpretations.",
        "home_use": "Findings, figures, tables, analysis outputs, and interpretation notes.",
        "maintainer": "LLM-maintained",
    },
]


def wiki_index_path(hub: Hub) -> Path:
    return obsidian_vault_path(hub) / "index.md"


def wiki_log_path(hub: Hub) -> Path:
    return obsidian_vault_path(hub) / "log.md"


def wiki_inbox_path(hub: Hub) -> Path:
    return obsidian_vault_path(hub) / "wiki" / "inbox.md"


def ensure_concept_notes(hub: Hub, concepts: list[str]) -> list[Path]:
    concepts_dir = obsidian_vault_path(hub) / "Concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for concept in sorted(set(clean_concepts(concepts))):
        path = concepts_dir / f"{safe_concept_filename(concept)}.md"
        if path.exists():
            continue
        path.write_text(render_concept_stub(concept), encoding="utf-8")
        created.append(path)
    return created


def evolve_concept_notes_from_sources(hub: Hub, sources: list[dict[str, object]]) -> list[Path]:
    concepts = sorted(
        {
            concept
            for source in sources
            for concept in clean_concepts(source.get("concepts") if isinstance(source, dict) else [])
        }
    )
    if not concepts:
        return []
    ensure_concept_notes(hub, concepts)
    ensure_wiki_index_entries(
        hub,
        [
            {
                "target": f"Concepts/{safe_concept_filename(concept)}",
                "title": concept_title(concept),
                "summary": "Concept discovered from indexed sources.",
            }
            for concept in concepts
        ],
    )

    concepts_dir = obsidian_vault_path(hub) / "Concepts"
    updated: list[Path] = []
    for concept in concepts:
        concept_sources = [source for source in sources if concept in clean_concepts(source.get("concepts", []))]
        if not concept_sources:
            continue
        path = concepts_dir / f"{safe_concept_filename(concept)}.md"
        text = path.read_text(encoding="utf-8")
        next_text = upsert_indexed_sources_section(text, render_indexed_sources_block(concept, concept_sources))
        if next_text != text:
            path.write_text(next_text, encoding="utf-8")
            updated.append(path)
    return updated


def ensure_wiki_index_entries(hub: Hub, entries: list[dict[str, str]]) -> None:
    path = wiki_index_path(hub)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else "# Research OS Index\n\n"
    existing_targets = {parsed["path"].removesuffix(".md") for line in existing.splitlines() if (parsed := parse_index_line(line))}
    lines = []
    for entry in entries:
        target = entry["target"]
        if target in existing_targets:
            continue
        lines.append(f"- [[{target}|{entry['title']}]] - {entry['summary']}")
    if not lines:
        return
    if not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")


def upsert_indexed_sources_section(text: str, block: str) -> str:
    marked_block_pattern = re.compile(
        rf"\n*## Indexed Sources\n\n{re.escape(INDEXED_SOURCES_START)}.*?{re.escape(INDEXED_SOURCES_END)}\n*",
        re.DOTALL,
    )
    section = f"\n\n## Indexed Sources\n\n{INDEXED_SOURCES_START}\n{block}{INDEXED_SOURCES_END}\n"
    if marked_block_pattern.search(text):
        return marked_block_pattern.sub(section, text).rstrip() + "\n"
    return text.rstrip() + section


def render_indexed_sources_block(concept: str, sources: list[dict[str, object]]) -> str:
    lines = [render_indexed_source_line(concept, source) for source in sorted(sources, key=source_sort_key)]
    return "\n".join(line for line in lines if line) + "\n"


def source_sort_key(source: dict[str, object]) -> tuple[str, str]:
    date_value = source.get("date")
    title_value = source.get("title")
    return (str(date_value) if isinstance(date_value, str) else "", str(title_value) if isinstance(title_value, str) else "")


def render_indexed_source_line(concept: str, source: dict[str, object]) -> str:
    title = string_value(source.get("title")) or string_value(source.get("id")) or "Untitled source"
    note_key = string_value(source.get("citation_key")) or safe_note_filename(string_value(source.get("id")) or title)
    parts = []
    project_text = ", ".join(clean_concepts(source.get("projects", [])))
    if project_text:
        parts.append(f"project: {project_text}")
    evidence_text = evidence_fields_for_concept(source, concept)
    if evidence_text:
        parts.append(f"evidence: {evidence_text}")
    detail = f" - {'; '.join(parts)}" if parts else ""
    return f"- [[Sources/Papers/{note_key}|{title}]]{detail}"


def evidence_fields_for_concept(source: dict[str, object], concept: str) -> str:
    classification = source.get("classification")
    if not isinstance(classification, dict):
        return ""
    evidence = classification.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for item in evidence:
        if not isinstance(item, dict) or item.get("concept") != concept:
            continue
        fields = clean_concepts(item.get("fields", []))
        return ", ".join(fields)
    return ""


def safe_note_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    return safe or "untitled"


def string_value(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def clean_concepts(concepts: object) -> list[str]:
    if not isinstance(concepts, list):
        return []
    return [concept.strip() for concept in concepts if isinstance(concept, str) and concept.strip()]


def safe_concept_filename(concept: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", concept.strip()).strip("-")
    return safe or "unknown"


def concept_title(concept: str) -> str:
    return concept.strip().replace("-", " ")


def render_concept_stub(concept: str) -> str:
    title = concept_title(concept)
    return "\n".join(
        [
            "---",
            "type: concept",
            "status: stub",
            "tags:",
            f"  - {safe_concept_filename(concept)}",
            "---",
            "",
            f"# {title}",
            "",
            "## Definition",
            "",
            f"{title.capitalize()} is an indexed Research OS concept discovered from project, source, or file metadata. Refine this definition as the wiki accumulates stronger evidence.",
            "",
            "## Related",
            "",
            "- Review linked graph neighbors and source notes before treating this stub as settled knowledge.",
            "",
        ]
    )


def folder_guide_markdown_table(include_maintainer: bool) -> str:
    if include_maintainer:
        lines = ["| Folder | What goes here | Who maintains it |", "| --- | --- | --- |"]
        lines.extend(
            f"| `{item['folder']}` | {item['home_use']} | {item['maintainer']} |" for item in FOLDER_GUIDE
        )
        lines.append("| `wiki/inbox.md` | Sources waiting for explicit Stage 2 integration into the wiki. | Human confirms; LLM processes |")
        return "\n".join(lines)
    lines = ["| Folder | Use it for |", "| --- | --- |"]
    lines.extend(f"| `{item['folder']}` | {item['use']} |" for item in FOLDER_GUIDE)
    return "\n".join(lines)


def count_pending_wiki_integrations(hub: Hub) -> int:
    path = wiki_inbox_path(hub)
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- [ ] "))


def wiki_page_count(hub: Hub) -> int:
    vault = obsidian_vault_path(hub)
    return sum(1 for directory in WIKI_DIRS for _path in (vault / directory).glob("*.md") if (vault / directory).is_dir())


def wiki_pages_for_query(hub: Hub, query: str) -> list[dict[str, str]]:
    path = wiki_index_path(hub)
    if not path.is_file():
        return []
    pages: list[dict[str, str]] = []
    query_lower = query.casefold()
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_index_line(line)
        if parsed is None:
            continue
        haystack = " ".join([parsed["path"], parsed["title"], parsed["summary"]]).casefold()
        if query_lower in haystack:
            pages.append(parsed)
    return pages


def parse_index_line(line: str) -> dict[str, str] | None:
    match = re.match(r"- \[\[([^|\]]+)(?:\|([^\]]+))?\]\]\s*-\s*(.+)", line)
    if match is None:
        return None
    target = match.group(1)
    title = match.group(2) or target.rsplit("/", 1)[-1]
    summary = match.group(3).strip()
    path = target if target.endswith(".md") else f"{target}.md"
    return {"path": path, "title": title, "summary": summary}


def queue_wiki_integration(hub: Hub, source_id: str, adapter: str, note: str) -> None:
    path = wiki_inbox_path(hub)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else "# Wiki Integration Inbox\n\n"
    if has_queued_wiki_integration(existing, source_id, adapter):
        return
    line = f"- [ ] {source_id} -> {adapter} ({note})"
    if not existing.endswith("\n"):
        existing += "\n"
    existing += line + "\n"
    path.write_text(existing, encoding="utf-8")


def has_queued_wiki_integration(text: str, source_id: str, adapter: str) -> bool:
    pattern = re.compile(rf"^- \[[ xX]\] {re.escape(source_id)} -> {re.escape(adapter)}(?:\s|\(|$)")
    return any(pattern.match(line) for line in text.splitlines())


def append_wiki_log(hub: Hub, action: str, title: str, detail: str) -> None:
    path = wiki_log_path(hub)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else "# Wiki Log\n\n"
    entry = f"## [{date.today().isoformat()}] {action} | {title}\n\n{detail}\n\n"
    path.write_text(existing.rstrip() + "\n\n" + entry, encoding="utf-8")
