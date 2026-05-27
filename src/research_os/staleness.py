from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_os.config import Hub
from research_os.paths import obsidian_vault_path


FINGERPRINT_VERSION = 1
FINGERPRINT_KEY = "research_os_fingerprint"
FINGERPRINT_VERSION_KEY = "research_os_fingerprint_version"
GRAPH_METADATA_KEY = "metadata"
VISUAL_META_PREFIX = "<!-- research-os:"

GRAPH_INPUTS = [
    "registries/projects.yaml",
    "registries/sources.yaml",
    "registries/files.yaml",
    "registries/relations.yaml",
]

HOME_INPUTS = [
    *GRAPH_INPUTS,
    "registries/inbox.yaml",
    "obsidian/starter-vault/wiki/inbox.md",
]


@dataclass(frozen=True)
class SurfaceStatus:
    name: str
    path: Path
    expected_fingerprint: str
    actual_fingerprint: str | None
    status: str


def graph_fingerprint(hub: Hub) -> str:
    return fingerprint_relative_paths(hub, GRAPH_INPUTS)


def home_fingerprint(hub: Hub) -> str:
    return fingerprint_relative_paths(hub, [*HOME_INPUTS, *wiki_page_paths(hub)])


def visual_fingerprint(graph: dict[str, Any]) -> str:
    payload = json.dumps(graph, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b"research-os-visual\0" + payload).hexdigest()[:16]


def fingerprint_relative_paths(hub: Hub, relative_paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(set(relative_paths)):
        path = hub.path / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def wiki_page_paths(hub: Hub) -> list[str]:
    vault = obsidian_vault_path(hub)
    if not vault.is_dir():
        return []
    return [
        path.relative_to(hub.path).as_posix()
        for path in vault.rglob("*.md")
        if ".obsidian" not in path.parts and path.name != "Home.md"
    ]


def graph_with_fingerprint(hub: Hub, graph: dict[str, Any]) -> dict[str, Any]:
    return with_metadata_fingerprint(graph, graph_fingerprint(hub))


def with_metadata_fingerprint(value: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    stamped = dict(value)
    metadata = stamped.get(GRAPH_METADATA_KEY)
    stamped[GRAPH_METADATA_KEY] = metadata if isinstance(metadata, dict) else {}
    stamped[GRAPH_METADATA_KEY][FINGERPRINT_KEY] = fingerprint
    stamped[GRAPH_METADATA_KEY][FINGERPRINT_VERSION_KEY] = FINGERPRINT_VERSION
    return stamped


def visual_metadata_comment(fingerprint: str) -> str:
    metadata = {
        FINGERPRINT_KEY: fingerprint,
        FINGERPRINT_VERSION_KEY: FINGERPRINT_VERSION,
    }
    return f"{VISUAL_META_PREFIX} {json.dumps(metadata, sort_keys=True)} -->"


def stored_home_fingerprint(text: str) -> str | None:
    return stored_yaml_scalar(text, FINGERPRINT_KEY)


def stored_graph_fingerprint(graph: dict[str, Any]) -> str | None:
    metadata = graph.get(GRAPH_METADATA_KEY)
    if not isinstance(metadata, dict):
        return None
    value = metadata.get(FINGERPRINT_KEY)
    return value if isinstance(value, str) and value else None


def stored_visual_fingerprint(text: str) -> str | None:
    pattern = re.compile(r"<!-- research-os:\s*(\{.*?\})\s*-->", re.DOTALL)
    match = pattern.search(text)
    if match is None:
        return None
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    value = metadata.get(FINGERPRINT_KEY) if isinstance(metadata, dict) else None
    return value if isinstance(value, str) and value else None


def stored_yaml_scalar(text: str, key: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith(f"{key}:"):
            value = line.split(":", 1)[1].strip().strip('"')
            return value or None
    return None


def context_health(hub: Hub, graph: dict[str, Any] | None = None) -> list[SurfaceStatus]:
    home_path = obsidian_vault_path(hub) / "Home.md"
    graph_path = hub.path / "graph" / "graph.json"
    visual_path = hub.path / "visual" / "index.html"

    home_text = home_path.read_text(encoding="utf-8") if home_path.is_file() else ""
    visual_text = visual_path.read_text(encoding="utf-8") if visual_path.is_file() else ""
    graph_data = graph or read_json_object(graph_path)
    home_expected = home_fingerprint(hub)
    graph_expected = graph_fingerprint(hub)
    visual_graph = visual_graph_data(graph_data) if graph_data is not None else None
    visual_expected = visual_fingerprint(visual_graph) if visual_graph is not None else ""
    home_actual = stored_home_fingerprint(home_text) if home_text else None
    graph_actual = stored_graph_fingerprint(graph_data) if graph_data is not None else None
    visual_actual = stored_visual_fingerprint(visual_text) if visual_text else None

    return [
        SurfaceStatus(
            name="Home.md",
            path=home_path,
            expected_fingerprint=home_expected,
            actual_fingerprint=home_actual,
            status=status_for(home_path, home_actual, home_expected),
        ),
        SurfaceStatus(
            name="graph.json",
            path=graph_path,
            expected_fingerprint=graph_expected,
            actual_fingerprint=graph_actual,
            status=status_for(graph_path, graph_actual, graph_expected),
        ),
        SurfaceStatus(
            name="visual/index.html",
            path=visual_path,
            expected_fingerprint=visual_expected,
            actual_fingerprint=visual_actual,
            status=status_for(visual_path, visual_actual, visual_expected),
        ),
    ]


def status_for(path: Path, actual: str | None, expected: str) -> str:
    if not path.is_file():
        return "missing"
    if actual is None:
        return "untracked"
    return "current" if actual == expected else "stale"


def read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def visual_graph_data(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    return {
        "nodes": nodes if isinstance(nodes, list) else [],
        "edges": edges if isinstance(edges, list) else [],
    }


def render_context_health(statuses: list[SurfaceStatus]) -> str:
    lines = ["# Context Health", ""]
    for status in statuses:
        lines.append(
            f"- {status.name}: {status.status} "
            f"(expected {status.expected_fingerprint or 'n/a'}, found {status.actual_fingerprint or 'none'})"
        )
    return "\n".join(lines) + "\n"
