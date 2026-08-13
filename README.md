# Sessionindex

Sessionindex is a read-only, metadata-only project inventory for music and
audio work. Use it before a backup, a manual copy, a delivery package, cloud
offload, or an export retry to capture the declared project structure without
touching the project itself.

It checks declared required files/directories, walks the selected root in
stable order, reports entries/types/logical file sizes/modification times,
notes controlled exclusions, and records symlinks without following them.

Every output starts with:

```text
DECLARED PROJECT INVENTORY - SOURCE AVAILABILITY, CLOUD STATE, BACKUP, AND EXPORT READINESS UNVERIFIED
```

That boundary is intentional. A present project marker, audio file, export, or
folder does not prove a DAW session opens, media is collected, cloud content is
local, a backup is complete, there is enough storage, or an export is ready.

## What it does

- Reads directory entries and metadata only: file type, byte size, and modified
  time. It does not hash, parse, open, or copy asset contents.
- Checks that required files and directories exist as ordinary filesystem
  objects below the selected project root, without following symlinks.
- Recursively inventories a selected root with an explicit metadata-entry cap.
- Skips only declared excluded directories and records each skipped directory.
- Treats symlinks as visible inventory records but never traverses them.
- Writes a new local index, CSV inventory, and JSON manifest only when the
  complete declared scan passes.

## What it does not do

- It makes no network, iCloud, File Provider, filesystem-content, checksum,
  media, DAW, archive, copy, move, delete, offload, upload, or browser call.
- It does not assess source availability, cloud download/upload/conflict state,
  backup integrity, free space, dependencies, missing media, project recall,
  session correctness, export settings, audio quality, or delivery completion.
- It does not follow symlink targets or store link-target text, so it does not
  map content outside the selected project root.

For package-level byte checks, use
[Handoffpack](https://github.com/notgabriels-sys/handoffpack) on a deliberately
selected, validated subset. For PCM WAV stem headers/frame counts, use
[Stemguard](https://github.com/notgabriels-sys/stemguard). These remain separate
checks, not proof of source or cloud readiness.

## Install

Requires Python 3.11 or later.

```bash
uv tool install .
```

For a development checkout:

```bash
uv venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

## Use

The example uses only fictional placeholder files.

```bash
sessionindex check examples/sessionindex-example.toml examples/project
sessionindex check examples/sessionindex-example.toml examples/project --json
sessionindex build examples/sessionindex-example.toml examples/project --output ./project-snapshot
```

For a real project, make the contract first and point the second argument at
the specific project root you intend to inspect:

```bash
sessionindex check my-project-index.toml /path/to/one/project
sessionindex build my-project-index.toml /path/to/one/project --output ./inventory-before-copy
```

`check` does not write anywhere. `build` creates a new output directory
atomically, refuses to overwrite an existing directory, and refuses an output
inside the selected project root. Review the output before any separate manual
backup, copy, archive, or cloud action.

## Contract format

```toml
[project]
title = "Project title"
kind = "Digital-audio project"
requirements_basis = "Read-only inventory before a manual backup."

[expectations]
required_files = ["session.example"]
required_directories = ["assets", "exports"]

[scan]
exclude_directories = ["cache", ".git"]
max_entries = 10000
```

All required/excluded paths are safe relative POSIX paths beneath the project
root selected on the command line. They cannot be absolute, traverse `..`, use
backslashes, use control characters, or contain empty path segments.

`exclude_directories` skips recursion only. It does not say the material is
temporary, backed up, cloud-safe, or eligible for deletion/offload.

`max_entries` limits directory metadata traversal, not bytes or duration. Set
it above the known expected entry count for a specific project; it is not a
storage-headroom calculation or an estimate of export viability.

## Output

```text
project-snapshot/
├── PROJECT_INDEX.md
├── file_inventory.csv
└── manifest.json
```

Only relative paths are written. The snapshot contains no absolute source
paths, file contents, hashes, link targets, cloud state, recipient data, or
cleanup instructions.

## Development

```bash
uv run pytest
uv build
```

Tests use a fictional directory tree and never inspect a real music project.

## Licence

[MIT](LICENSE)
