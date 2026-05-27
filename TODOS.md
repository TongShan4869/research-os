# Research OS TODOs

## CLI-Assisted Stage 2 Wiki Integration

- **What:** Add a CLI-assisted `integrate-source` flow that consumes one `wiki/inbox.md` item and updates source, concept, claim, entity, and synthesis pages by section.
- **Why:** Stage 1 ingest now safely registers sources and queues integration, but Stage 2 is still document-driven. A CLI flow would make the compounding wiki loop repeatable without deep-processing papers automatically.
- **Pros:** Reduces manual wiki maintenance, creates a testable integration path, and gives agents a safer workflow for one-source-at-a-time synthesis.
- **Cons:** Requires source-type adapters, page update policy, conflict handling, and careful tests to avoid wholesale rewrites.
- **Context:** Start from `src/research_os/wiki.py`, `workflows/integrate-source.md`, and `wiki/inbox.md`. Academic papers must keep Zotero read-only and require explicit PDF/full-text confirmation.
- **Depends on / blocked by:** Control-plane context packets and keyed wiki inbox entries should be stable first.

## Visual Explorer Wiki Health Overlays

- **What:** Extend the visual explorer to show pending wiki integration items, orphan wiki pages, missing index entries, and later contradiction/claim nodes.
- **Why:** The graph is intended to become a review surface, not just a static map. Wiki health overlays would make unindexed islands visible.
- **Pros:** Helps users inspect context readiness visually and spot maintenance work that plain YAML/Markdown lists hide.
- **Cons:** Adds frontend state and graph annotation work that is not required for the current CLI/template slice.
- **Context:** Start from `src/research_os/visual.py`, `graph/graph.json`, and the wiki helpers in `src/research_os/wiki.py`.
- **Depends on / blocked by:** Wiki lint semantics should exist before richer contradiction or orphan overlays are added.
