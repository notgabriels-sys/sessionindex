# Sessionindex design

**Date:** 2026-08-13
**Status:** Approved implementation plan

## Purpose

Sessionindex creates a read-only, metadata-only snapshot of a declared music
or audio-project directory. It exists before a backup, delivery packaging,
manual copy, cloud offload, or export retry: it makes the stated project
structure, required paths, file counts, logical sizes, exclusions, and
non-followed symlinks reviewable without touching the project data.

It complements Handoffpack. Handoffpack packages a small explicitly declared
subset into a verified local ZIP. Sessionindex inventories a project tree first
without reading file contents or creating an archive.

## Explicit boundaries

- No content reads, checksums, media parsing, hashing, archive creation,
  copying, moving, renaming, deletion, iCloud eviction, cloud download,
  upload, export, DAW integration, browser automation, or network requests.
- It reads directory entries and file metadata only (`lstat`-level type, size,
  and modification time). It does not establish whether local content is
  complete, readable, current, non-placeholder, synced, uploaded, backed up,
  or safe to remove.
- A present `.bwproject`, audio file, export, or folder is not proof that the
  correct project opens, all media is collected, a DAW session is recovered,
  an export is ready, or an iCloud state is healthy.
- Symlinks are recorded but never followed. The tool never resolves an entry
  in the project tree to search beyond the selected root.
- Example data is fictional and has no relationship to an actual project,
  artist, title, storage state, release, or delivery.

## CLI

```text
sessionindex check PROJECT_TOML PROJECT_DIRECTORY [--json]
sessionindex build PROJECT_TOML PROJECT_DIRECTORY --output OUTPUT_DIR
```

`check` is fully read-only. `build` first checks, then writes a new snapshot
directory atomically outside the selected project root. It refuses to overwrite
an existing output path or write the snapshot inside that project tree.

## Contract model

```toml
[project]
title = "..."
kind = "Audio project"
requirements_basis = "Purpose and requirements for this inventory."

[expectations]
required_files = ["project/session-file.ext"]
required_directories = ["assets", "exports"]

[scan]
exclude_directories = ["cache", ".git"]
max_entries = 10000
```

All expected and excluded paths are safe relative POSIX paths. Required files
must resolve to ordinary files inside the selected project root; required
directories must resolve to ordinary directories. Both are checked without
following symlinks. Exclusions skip directory recursion only; they do not mean
the excluded material is absent, safe, synced, or disposable.

`max_entries` is a project-specific read-only scan cap. It limits metadata
traversal, not bytes or media duration. It protects a caller from accidentally
walking a much larger tree than intended; it is not a size/headroom estimate.

## Scan rules

- The root must be an existing ordinary directory, not a symlink.
- Entries are scanned recursively in stable lexical order, using metadata only.
- An excluded directory is noted and skipped, without traversing its children.
- Files, directories, symlinks, and other filesystem entries are recorded.
- Symlinks are never followed; their link text is not read into generated
  output to avoid accidentally exposing targets outside the project root.
- Permission or metadata errors, required-path failures, and a max-entry
  overflow fail the check. The output is never built from a partial scan.

## Output

```text
PROJECT_INDEX.md
file_inventory.csv
manifest.json
```

All human-readable output begins with:

```text
DECLARED PROJECT INVENTORY - SOURCE AVAILABILITY, CLOUD STATE, BACKUP, AND EXPORT READINESS UNVERIFIED
```

The snapshot records relative paths only. It does not contain absolute source
paths, file contents, hashes, iCloud state, recipient data, or cleanup action.

## Test plan

- TOML parsing and path/limit validation;
- required-file/directory state and safe path rules;
- stable metadata-only recursive inventory and excluded-directory handling;
- symlink visibility without following an external target;
- max-entry and missing-root failures;
- deterministic snapshot construction, relative path output, source immutability,
  no build on failures, and no overwrite;
- human/JSON CLI plus installed command and source/wheel package smoke checks.
