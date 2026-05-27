from __future__ import annotations

from datetime import date
import re
from pathlib import Path

from research_os.config import Hub
from research_os.paths import obsidian_vault_path


WIKI_DIRS = ["Synthesis", "Entities", "Concepts", "Claims", "Methods", "Datasets", "Results"]
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
