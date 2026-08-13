"""Metadata-only project tree validation with no symlink traversal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from pathlib import Path
import stat
from typing import Any

from .contract import ContractFormatError, load_contract, validate_contract
from .models import (
    INVENTORY_STATUS,
    InventoryEntry,
    InventorySummary,
    ProjectContract,
)


@dataclass(frozen=True)
class ProjectCheck:
    ok: bool
    errors: tuple[str, ...]
    contract: ProjectContract | None
    project_root: Path | None
    entries: tuple[InventoryEntry, ...]
    summary: InventorySummary | None
    status: str = INVENTORY_STATUS

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "status": self.status,
            "project": None
            if self.contract is None
            else {
                "title": self.contract.project.title,
                "kind": self.contract.project.kind,
                "requirements_basis": self.contract.project.requirements_basis,
            },
            "project_root": None
            if self.project_root is None
            else {"directory_name": self.project_root.name},
            "summary": None if self.summary is None else summary_to_dict(self.summary),
            "entries": [entry_to_dict(entry) for entry in self.entries],
        }


def check_project(contract_source: str | Path, project_directory: str | Path) -> ProjectCheck:
    """Read entry metadata only; do not read project-file content or follow links."""

    try:
        contract = load_contract(contract_source)
    except ContractFormatError as error:
        return ProjectCheck(False, (str(error),), None, None, (), None)

    validation = validate_contract(contract)
    if not validation.is_valid:
        return ProjectCheck(False, validation.errors, contract, None, (), None)

    root = Path(project_directory)
    root_error = _validate_root(root)
    if root_error is not None:
        return ProjectCheck(False, (root_error,), contract, None, (), None)

    errors = _validate_required_paths(contract, root)
    entries, scan_errors = _scan_metadata(root, contract.scan.exclude_directories, contract.scan.max_entries)
    errors.extend(scan_errors)
    summary = summarize_entries(entries)
    return ProjectCheck(
        ok=not errors,
        errors=tuple(errors),
        contract=contract,
        project_root=root,
        entries=tuple(entries),
        summary=summary,
    )


def summarize_entries(entries: list[InventoryEntry] | tuple[InventoryEntry, ...]) -> InventorySummary:
    return InventorySummary(
        entry_count=len(entries),
        file_count=sum(item.kind == "file" for item in entries),
        directory_count=sum(item.kind == "directory" for item in entries),
        excluded_directory_count=sum(item.kind == "excluded-directory" for item in entries),
        symlink_count=sum(item.kind == "symlink" for item in entries),
        other_count=sum(item.kind == "other" for item in entries),
        logical_file_bytes=sum(item.byte_size for item in entries if item.kind == "file"),
    )


def entry_to_dict(entry: InventoryEntry) -> dict[str, object]:
    return {
        "path": entry.path,
        "kind": entry.kind,
        "byte_size": entry.byte_size,
        "modified_utc": entry.modified_utc,
    }


def summary_to_dict(summary: InventorySummary) -> dict[str, int]:
    return {
        "entry_count": summary.entry_count,
        "file_count": summary.file_count,
        "directory_count": summary.directory_count,
        "excluded_directory_count": summary.excluded_directory_count,
        "symlink_count": summary.symlink_count,
        "other_count": summary.other_count,
        "logical_file_bytes": summary.logical_file_bytes,
    }


def _validate_root(root: Path) -> str | None:
    try:
        metadata = os.lstat(root)
    except FileNotFoundError:
        return f"project directory does not exist: {root}"
    except OSError as error:
        return f"project directory metadata could not be read: {error}"
    if stat.S_ISLNK(metadata.st_mode):
        return "project directory must not be a symlink"
    if not stat.S_ISDIR(metadata.st_mode):
        return f"project directory is not a directory: {root}"
    return None


def _validate_required_paths(contract: ProjectContract, root: Path) -> list[str]:
    errors: list[str] = []
    for relative in contract.expectations.required_files:
        kind = _required_path_kind(root, relative)
        if kind == "missing":
            errors.append(f"required file is missing: {relative}")
        elif kind == "symlink":
            errors.append(f"required file is a symlink or travels through one: {relative}")
        elif kind == "traversal-error":
            errors.append(f"required file cannot be traversed safely: {relative}")
        elif kind != "file":
            errors.append(f"required file is not a file: {relative}")
    for relative in contract.expectations.required_directories:
        kind = _required_path_kind(root, relative)
        if kind == "missing":
            errors.append(f"required directory is missing: {relative}")
        elif kind == "symlink":
            errors.append(f"required directory is a symlink or travels through one: {relative}")
        elif kind == "traversal-error":
            errors.append(f"required directory cannot be traversed safely: {relative}")
        elif kind != "directory":
            errors.append(f"required directory is not a directory: {relative}")
    return errors


def _required_path_kind(root: Path, relative: str) -> str:
    current = root
    for component in relative.split("/"):
        current = current / component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            return "missing"
        except OSError:
            return "traversal-error"
        if stat.S_ISLNK(metadata.st_mode):
            return "symlink"
    if stat.S_ISREG(metadata.st_mode):
        return "file"
    if stat.S_ISDIR(metadata.st_mode):
        return "directory"
    return "other"


def _scan_metadata(
    root: Path, excluded_directories: tuple[str, ...], max_entries: int
) -> tuple[list[InventoryEntry], list[str]]:
    excluded = set(excluded_directories)
    entries: list[InventoryEntry] = []
    errors: list[str] = []

    def add(relative: str, kind: str, metadata: os.stat_result) -> bool:
        entries.append(
            InventoryEntry(
                path=relative,
                kind=kind,
                byte_size=metadata.st_size,
                modified_utc=_utc_timestamp(metadata.st_mtime),
            )
        )
        if len(entries) > max_entries:
            errors.append(f"scan exceeded declared max_entries ({max_entries})")
            return False
        return True

    def walk(directory: Path, prefix: Path) -> bool:
        try:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda item: item.name)
        except OSError as error:
            display = prefix.as_posix() if prefix.parts else "."
            errors.append(f"could not read directory metadata at {display}: {error}")
            return False

        for entry in children:
            relative_path = prefix / entry.name
            relative = relative_path.as_posix()
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as error:
                errors.append(f"could not read entry metadata at {relative}: {error}")
                return False
            if stat.S_ISLNK(metadata.st_mode):
                if not add(relative, "symlink", metadata):
                    return False
                continue
            if stat.S_ISDIR(metadata.st_mode):
                if relative in excluded:
                    if not add(relative, "excluded-directory", metadata):
                        return False
                    continue
                if not add(relative, "directory", metadata):
                    return False
                if not walk(Path(entry.path), relative_path):
                    return False
                continue
            kind = "file" if stat.S_ISREG(metadata.st_mode) else "other"
            if not add(relative, kind, metadata):
                return False
        return True

    walk(root, Path())
    return entries, errors


def _utc_timestamp(value: float) -> str:
    return datetime.fromtimestamp(value, tz=UTC).isoformat().replace("+00:00", "Z")
