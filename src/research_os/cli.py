from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from research_os.config import HubError, load_hub, load_projects, load_sources
from research_os.graph import build_graph, write_graph
from research_os.ingest import ingest_zotero_collection
from research_os.projects import attach_folder, create_project, load_optional_hub, resolve_project
from research_os.validation import validate_hub
from research_os.zotero import ZoteroLocalClient, check_zotero


TEMPLATE_DIR = Path(__file__).with_name("template")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a Research OS hub.")
    init_parser.add_argument("path", type=Path)
    init_parser.add_argument("--force", action="store_true", help="Initialize into a non-empty directory without overwriting files.")
    init_parser.set_defaults(handler=run_init)

    status_parser = subparsers.add_parser("status", help="Show Research OS hub status.")
    add_hub_argument(status_parser)
    status_parser.set_defaults(handler=run_status)

    validate_parser = subparsers.add_parser("validate", help="Validate a Research OS hub.")
    add_hub_argument(validate_parser)
    validate_parser.set_defaults(handler=run_validate)

    new_project_parser = subparsers.add_parser("new-project", help="Register a new Research OS project.")
    new_project_parser.add_argument("project_id")
    new_project_parser.add_argument("--title", required=True)
    add_hub_argument(new_project_parser)
    new_project_parser.set_defaults(handler=run_new_project)

    attach_parser = subparsers.add_parser("attach-folder", help="Attach a folder to a registered project.")
    attach_parser.add_argument("project_id")
    attach_parser.add_argument("path", type=Path)
    attach_parser.add_argument("--kind", required=True)
    add_hub_argument(attach_parser)
    attach_parser.set_defaults(handler=run_attach_folder)

    resolve_parser = subparsers.add_parser("resolve-project", help="Resolve the Research OS project for a path.")
    resolve_parser.add_argument("path", type=Path)
    resolve_parser.add_argument("--hub", type=Path, default=None, help="Research OS hub path for registry path lookup.")
    resolve_parser.set_defaults(handler=run_resolve_project)

    build_graph_parser = subparsers.add_parser("build-graph", help="Build graph/graph.json from Research OS registries.")
    add_hub_argument(build_graph_parser)
    build_graph_parser.set_defaults(handler=run_build_graph)

    zotero_parser = subparsers.add_parser("zotero-status", help="Check Zotero Desktop local API availability.")
    zotero_parser.set_defaults(handler=run_zotero_status)

    doctor_parser = subparsers.add_parser("doctor", help="Run Research OS hub and integration checks.")
    add_hub_argument(doctor_parser)
    doctor_parser.set_defaults(handler=run_doctor)

    ingest_collection_parser = subparsers.add_parser("ingest-zotero-collection", help="Create Obsidian notes from a Zotero collection.")
    ingest_collection_parser.add_argument("collection", help="Zotero collection name or key.")
    ingest_collection_parser.add_argument("--project", required=True, help="Research OS project id to link papers to.")
    add_hub_argument(ingest_collection_parser)
    ingest_collection_parser.set_defaults(handler=run_ingest_zotero_collection)

    return parser


def add_hub_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hub", type=Path, default=Path("."), help="Research OS hub path.")


def run_init(args: argparse.Namespace) -> int:
    target = args.path.expanduser().resolve()
    if target.exists() and any(target.iterdir()) and not args.force:
        print(f"Refusing to initialize non-empty directory: {target}")
        print("Run again with --force to add missing Research OS files without overwriting existing files.")
        return 2

    copy_template(TEMPLATE_DIR, target)
    print(f"Initialized Research OS hub at {target}")
    print()
    print("Open Codex in this folder and run:")
    print("/research-os:onboard")
    print()
    print('Natural-language fallback: "Initialize my Research OS workspace."')
    return 0


def copy_template(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for source_path in source.rglob("*"):
        relative_path = source_path.relative_to(source)
        target_path = target / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            continue
        shutil.copy2(source_path, target_path)


def run_status(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        projects = load_projects(hub)
        sources = load_sources(hub)
    except HubError as error:
        print(f"status blocked: {error}")
        return 1

    onboarding_complete = bool(hub.config.get("profile", {}).get("onboarding_complete"))
    onboarding_state = "complete" if onboarding_complete else "incomplete"
    print(f"Research OS hub: {hub.path}")
    print(f"onboarding: {onboarding_state}")
    print(f"projects: {len(projects)}")
    print(f"sources: {len(sources)}")
    return 0


def run_validate(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
    except HubError as error:
        print(f"validation blocked: {error}")
        return 1

    result = validate_hub(hub)
    if result.ok:
        print(f"hub is valid: {hub.path}")
        return 0

    for error in result.errors:
        print(error)
    return 1


def run_new_project(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        project = create_project(hub, args.project_id, args.title)
    except HubError as error:
        print(error)
        return 1
    print(f"created project: {project['id']}")
    return 0


def run_attach_folder(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        attach_folder(hub, args.project_id, args.path, args.kind)
    except HubError as error:
        print(error)
        return 1
    print(f"attached {args.kind} folder to project: {args.project_id}")
    return 0


def run_resolve_project(args: argparse.Namespace) -> int:
    try:
        hub = load_optional_hub(args.hub)
        resolution = resolve_project(args.path, hub=hub)
    except HubError as error:
        print(error)
        return 1
    print(f"project_id: {resolution.project_id}")
    print(f"resolution: {resolution.resolution}")
    if resolution.workspace is not None:
        print(f"workspace: {resolution.workspace}")
    if resolution.folder_kind is not None:
        print(f"folder_kind: {resolution.folder_kind}")
    if resolution.matched_path is not None:
        print(f"matched_path: {resolution.matched_path}")
    return 0


def run_build_graph(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        graph = build_graph(hub)
        graph_path = write_graph(hub, graph)
    except HubError as error:
        print(error)
        return 1
    print(f"wrote graph: {graph_path}")
    print(f"nodes: {len(graph['nodes'])}")
    print(f"edges: {len(graph['edges'])}")
    return 0


def run_zotero_status(args: argparse.Namespace) -> int:
    status = check_zotero()
    print(f"Zotero: {status.message}")
    return 0 if status.available else 1


def run_doctor(args: argparse.Namespace) -> int:
    hub_ok = False
    try:
        hub = load_hub(args.hub)
    except HubError as error:
        print(f"Hub: blocked - {error}")
    else:
        result = validate_hub(hub)
        if result.ok:
            hub_ok = True
            print("Hub: valid")
        else:
            print("Hub: invalid")
            for error in result.errors:
                print(f"- {error}")

    zotero_status = check_zotero()
    print(f"Zotero: {zotero_status.message}")
    return 0 if hub_ok and zotero_status.available else 1


def run_ingest_zotero_collection(args: argparse.Namespace) -> int:
    try:
        hub = load_hub(args.hub)
        result = ingest_zotero_collection(hub, args.collection, args.project, ZoteroLocalClient())
    except (HubError, ValueError, OSError) as error:
        print(f"ingest blocked: {error}")
        return 1
    print(f"ingested Zotero collection: {result.collection_name} ({result.collection_key})")
    print(f"papers: {result.item_count}")
    print(f"vault: {result.vault_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
