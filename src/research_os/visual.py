from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from research_os.config import Hub
from research_os.staleness import visual_fingerprint, visual_metadata_comment


GRAPH_DATA_PLACEHOLDER = "__RESEARCH_OS_GRAPH_DATA__"


def write_visual(hub: Hub, graph: dict[str, list[dict[str, Any]]]) -> Path:
    visual_path = hub.path / "visual" / "index.html"
    visual_path.parent.mkdir(parents=True, exist_ok=True)
    visual_path.write_text(render_visual_html(graph), encoding="utf-8")
    return visual_path


def script_json(value: Any) -> str:
    return (
        json.dumps(value, sort_keys=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render_visual_html(graph: dict[str, list[dict[str, Any]]]) -> str:
    template = visual_template()
    html = template.replace(GRAPH_DATA_PLACEHOLDER, script_json(graph))
    return f"{visual_metadata_comment(visual_fingerprint(graph))}\n{html}"


def visual_template() -> str:
    template = files("research_os").joinpath("visual_template.html").read_text(encoding="utf-8")
    if GRAPH_DATA_PLACEHOLDER not in template:
        raise RuntimeError("visual template is missing the graph data placeholder")
    return template
