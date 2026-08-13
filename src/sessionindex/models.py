from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


INVENTORY_STATUS = (
    "DECLARED PROJECT INVENTORY - SOURCE AVAILABILITY, CLOUD STATE, BACKUP, AND EXPORT READINESS UNVERIFIED"
)


@dataclass(frozen=True)
class Project:
    title: str
    kind: str
    requirements_basis: str


@dataclass(frozen=True)
class Expectations:
    required_files: tuple[str, ...]
    required_directories: tuple[str, ...]


@dataclass(frozen=True)
class ScanConfig:
    exclude_directories: tuple[str, ...]
    max_entries: int


@dataclass(frozen=True)
class ProjectContract:
    source: Path
    project: Project
    expectations: Expectations
    scan: ScanConfig


@dataclass(frozen=True)
class InventoryEntry:
    path: str
    kind: str
    byte_size: int
    modified_utc: str


@dataclass(frozen=True)
class InventorySummary:
    entry_count: int
    file_count: int
    directory_count: int
    excluded_directory_count: int
    symlink_count: int
    other_count: int
    logical_file_bytes: int
