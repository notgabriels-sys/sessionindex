"""Portable renderers for metadata-only project snapshots."""

from __future__ import annotations

import csv
from io import StringIO
import json

from .check import ProjectCheck, entry_to_dict, summary_to_dict
from .models import INVENTORY_STATUS


def render_index(report: ProjectCheck) -> str:
    contract = report.contract
    summary = report.summary
    assert contract is not None and summary is not None and report.project_root is not None
    lines = [
        f"# Project inventory: {_markdown_text(contract.project.title)}",
        "",
        f"**{INVENTORY_STATUS}**",
        "",
        "This is a metadata-only snapshot. It does not prove source availability, cloud state, backup, "
        "or export readiness. It did not read file contents, hash files, follow symlinks, copy, archive, "
        "move, delete, download, upload, or query any cloud provider.",
        "",
        "## Declared project",
        "",
        f"- **Project kind:** {_markdown_text(contract.project.kind)}",
        f"- **Requirements basis:** {_markdown_text(contract.project.requirements_basis)}",
        f"- **Selected root directory name:** `{_markdown_text(report.project_root.name)}`",
        "",
        "## Metadata scan summary",
        "",
        f"- **Entries:** {summary.entry_count}",
        f"- **Ordinary files:** {summary.file_count}",
        f"- **Directories traversed:** {summary.directory_count}",
        f"- **Excluded directories noted:** {summary.excluded_directory_count}",
        f"- **Symlinks noted but not followed:** {summary.symlink_count}",
        f"- **Other entries:** {summary.other_count}",
        f"- **Logical bytes of ordinary files only:** {summary.logical_file_bytes}",
        "",
        "## Required structure checked",
        "",
        "### Required files",
        "",
    ]
    lines.extend(f"- `{_markdown_text(path)}`" for path in contract.expectations.required_files)
    lines.extend(["", "### Required directories", ""])
    lines.extend(f"- `{_markdown_text(path)}`" for path in contract.expectations.required_directories)
    lines.extend(["", "### Excluded directories (not traversed)", ""])
    if contract.scan.exclude_directories:
        lines.extend(f"- `{_markdown_text(path)}`" for path in contract.scan.exclude_directories)
    else:
        lines.append("- None declared")

    lines.extend(
        [
            "",
            "## Before a separate copy, offload, or export decision",
            "",
            "- Recheck that the active project, revision, and intended destination are correct.",
            "- Verify file content, missing media, cloud availability/sync state, storage headroom, and destination writability separately.",
            "- Treat exclusions as scan boundaries only, not cleanup authorisation or backup evidence.",
            "- Use a dedicated archive/copy workflow and verify its output before any destructive or cloud action.",
            "",
        ]
    )
    return "\n".join(lines)


def render_inventory_csv(report: ProjectCheck) -> str:
    output = StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=["path", "kind", "byte_size", "modified_utc"],
        lineterminator="\n",
    )
    writer.writeheader()
    for entry in report.entries:
        writer.writerow(entry_to_dict(entry))
    return output.getvalue()


def render_manifest(report: ProjectCheck) -> str:
    contract = report.contract
    summary = report.summary
    assert contract is not None and summary is not None and report.project_root is not None
    manifest = {
        "format": "sessionindex-manifest/v1",
        "status": INVENTORY_STATUS,
        "contract_source": {"filename": contract.source.name},
        "project": {
            "title": contract.project.title,
            "kind": contract.project.kind,
            "requirements_basis": contract.project.requirements_basis,
        },
        "project_root": {"directory_name": report.project_root.name},
        "expectations": {
            "required_files": list(contract.expectations.required_files),
            "required_directories": list(contract.expectations.required_directories),
        },
        "scan": {
            "exclude_directories": list(contract.scan.exclude_directories),
            "max_entries": contract.scan.max_entries,
        },
        "summary": summary_to_dict(summary),
        "entries": [entry_to_dict(entry) for entry in report.entries],
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _markdown_text(value: object) -> str:
    return str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
