# Research OS Session Handoff

Date: 2026-05-22

## Current State

We brainstormed the v1 design for an open-source scientific research operating-system setup built around Codex, Obsidian, Zotero, and project folders.

The formal design spec is in:

```text
docs/superpowers/specs/2026-05-22-research-os-workspace-template-design.md
```

## Locked Decisions

- The shippable artifact is a reusable workspace template, not a single research skill.
- The system is local-first for a single researcher in v1.
- Architecture is a hub/control-plane folder that references existing Obsidian vaults, Zotero, and project folders.
- Project identity lives in `registries/projects.yaml`.
- Codex is the primary interface.
- CLI is deterministic helper machinery, not the main interface.
- Install story is `uv tool install research-os` or `uvx research-os init ~/ResearchOS`.
- Cold start is minimal CLI bootstrap, then Codex-native onboarding through `/research-os:onboard`.
- Natural-language onboarding fallback: "Initialize my Research OS workspace."
- Knowledge graph is hybrid: Obsidian-readable markdown plus machine-readable `graph/graph.json`.
- Research graph core is required; full ontology is a big-picture overlay.
- Paper intake is lightweight by default; `deep-process-paper` is opt-in.
- Daily notes and per-project logs both exist.
- Project resolution uses marker files, registry path matching, or confirmed heuristic attach.
- Zotero is read-only by default; writes and PDF/full-text reads require explicit user intent.

## Next Step

Turn the design spec into an implementation plan for the first working repo.

Recommended first implementation slice:

1. Python package skeleton installable with `uv`.
2. `research-os init <path>` that creates a bootable hub.
3. Template files: `AGENTS.md`, `research-os.yaml`, `workflows/onboard.md`, registries, schemas, Obsidian templates.
4. `research-os validate` and `research-os status`.
5. Minimal `/research-os:onboard` workflow instructions.
6. Demo workspace and tests.

## Notes

The previous scratch folder was not a git repo. The target project folder is:

```text
/Users/tongshan/Documents/research-os-dev
```
