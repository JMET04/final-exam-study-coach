# Public Book Spirit format 1.0

UTF-8 JSON/JSONL metadata and knowledge, authored HTML/SVG animation, independent narration. No proprietary database or API is required. `catalog.json` identifies book/edition, relative archive path, SHA-256, size and independent coverage states. Each archive contains `manifest.json` with `format=book-spirit-public-book`, `format_version=1.0`, identity, revision, rights, entrypoints and per-file integrity records.

Knowledge: frame contains scope and terminology; index routes topic keys/titles/aliases; topics JSONL stores reviewed topic bodies (facets, required facets, conditions, branches, relations, bounds and optional declarative calculations); nodes and relations represent reviewed concept connections. Do not execute declarative data as code. Original source pages are referenced, not included.

Animations: index entries identify point JSON, independent knowledge context and player paths, with active-manifest hashes. Point JSON has prerequisites, conditions, bounds and segments. Each segment has narration, symbols, keyframes and representation limits. Current progress is a display state, never an inferred physical measurement. Context tools select one segment and include the user's question; API transport is supplied by the caller. No vendor-specific schema is necessary.

Integrity uses SHA-256 of raw file bytes in public manifests. Existing point/knowledge semantic hashes use canonical JSON (UTF-8, sorted keys, compact separators, no ASCII escaping); player hashes use raw bytes. Public validation certifies consistency only. Book expert completion and animation coverage require separate recorded acceptance, not inferred from checksums.
