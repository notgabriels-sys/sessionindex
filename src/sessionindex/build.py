"""Atomic writing of Sessionindex metadata snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import tempfile

from .check import check_project
from .render import render_index, render_inventory_csv, render_manifest


class BuildError(ValueError):
    """A complete metadata snapshot could not be built safely."""


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    files: tuple[Path, ...]


def build_snapshot(
    contract_source: str | Path, project_directory: str | Path, output_dir: str | Path
) -> BuildResult:
    """Write a new snapshot only after a full successful metadata scan."""

    report = check_project(contract_source, project_directory)
    if not report.ok:
        raise BuildError("cannot build failed project inventory:\n" + "\n".join(report.errors))

    output = Path(output_dir)
    if output.exists() or output.is_symlink():
        raise BuildError(f"output path already exists: {output}")
    assert report.project_root is not None
    if _is_within_project_root(output, report.project_root):
        raise BuildError("output directory must be outside the selected project root")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        _write_text(temporary / "PROJECT_INDEX.md", render_index(report))
        _write_text(temporary / "file_inventory.csv", render_inventory_csv(report))
        _write_text(temporary / "manifest.json", render_manifest(report))
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    files = (
        output / "PROJECT_INDEX.md",
        output / "file_inventory.csv",
        output / "manifest.json",
    )
    return BuildResult(output_dir=output, files=files)


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _is_within_project_root(output: Path, project_root: Path) -> bool:
    try:
        output.resolve(strict=False).relative_to(project_root.resolve(strict=True))
    except ValueError:
        return False
    return True
