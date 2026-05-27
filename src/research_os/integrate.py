from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from research_os.config import Hub, HubError, load_files, load_sources
from research_os.wiki import append_wiki_log, wiki_inbox_path


@dataclass(frozen=True)
class IntegrationResult:
    source_id: str
    title: str
    adapter: str


def integrate_source(hub: Hub, source_id: str) -> IntegrationResult:
    source = resolve_source(hub, source_id)
    inbox_text = read_wiki_inbox(hub)
    line_match = queued_inbox_line(inbox_text, source_id)
    if line_match is None:
        raise HubError(f"source is not queued for wiki integration: {source_id}")

    adapter = line_match.group("adapter")
    title = string_value(source.get("title")) or source_id
    write_wiki_inbox(hub, mark_inbox_line_complete(inbox_text, line_match))
    append_wiki_log(
        hub,
        "Integrated source",
        title,
        f"- Source: `{source_id}`\n- Adapter: `{adapter}`\n- Mode: metadata-only; no PDF or full-text processing.",
    )
    return IntegrationResult(source_id=source_id, title=title, adapter=adapter)


def resolve_source(hub: Hub, source_id: str) -> dict[str, Any]:
    for source in [*load_sources(hub), *load_files(hub)]:
        if source.get("id") == source_id:
            return source
    raise HubError(f"source not found: {source_id}")


def read_wiki_inbox(hub: Hub) -> str:
    path = wiki_inbox_path(hub)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def write_wiki_inbox(hub: Hub, text: str) -> None:
    path = wiki_inbox_path(hub)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def queued_inbox_line(text: str, source_id: str) -> re.Match[str] | None:
    pattern = re.compile(
        rf"^(?P<prefix>- \[ \] {re.escape(source_id)} -> (?P<adapter>[^\s(]+)(?: .*)?)$",
        re.MULTILINE,
    )
    return pattern.search(text)


def mark_inbox_line_complete(text: str, match: re.Match[str]) -> str:
    start = match.start("prefix")
    return f"{text[:start]}- [x]{text[start + len('- [ ]'): match.end('prefix')]}{text[match.end('prefix'):]}"


def string_value(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
