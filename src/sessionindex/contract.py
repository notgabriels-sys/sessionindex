from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
from typing import Any
import tomllib

from .models import Expectations, Project, ProjectContract, ScanConfig


class ContractFormatError(ValueError):
    """A TOML file cannot be structurally interpreted as a Sessionindex contract."""


@dataclass(frozen=True)
class ContractValidationReport:
    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


def load_contract(source: str | Path) -> ProjectContract:
    """Read only the configuration TOML; never inspect a project tree here."""

    path = Path(source)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ContractFormatError(f"contract file does not exist: {path}") from error
    except UnicodeDecodeError as error:
        raise ContractFormatError(f"contract file is not UTF-8: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ContractFormatError(f"could not parse TOML in {path}: {error}") from error

    project = _required_table(data, "project")
    expectations = _required_table(data, "expectations")
    scan = _required_table(data, "scan")
    return ProjectContract(
        source=path,
        project=Project(
            title=_required_string(project, "title", "project"),
            kind=_required_string(project, "kind", "project"),
            requirements_basis=_required_string(
                project, "requirements_basis", "project"
            ),
        ),
        expectations=Expectations(
            required_files=_string_list(
                expectations.get("required_files"), "expectations.required_files"
            ),
            required_directories=_string_list(
                expectations.get("required_directories"),
                "expectations.required_directories",
            ),
        ),
        scan=ScanConfig(
            exclude_directories=_string_list(
                scan.get("exclude_directories", []), "scan.exclude_directories"
            ),
            max_entries=_required_integer(scan, "max_entries", "scan"),
        ),
    )


def validate_contract(contract: ProjectContract) -> ContractValidationReport:
    """Validate structure and path safety without traversing the selected root."""

    errors: list[str] = []
    for field in ("title", "kind", "requirements_basis"):
        if not _is_nonblank_string(getattr(contract.project, field)):
            errors.append(f"project.{field} must not be blank")

    total_required = len(contract.expectations.required_files) + len(
        contract.expectations.required_directories
    )
    if total_required == 0:
        errors.append("at least one required file or directory must be declared")

    _validate_path_list(
        contract.expectations.required_files, "expectations.required_files", errors
    )
    _validate_path_list(
        contract.expectations.required_directories,
        "expectations.required_directories",
        errors,
    )
    _validate_path_list(contract.scan.exclude_directories, "scan.exclude_directories", errors)

    required_files = {item.casefold() for item in contract.expectations.required_files if isinstance(item, str)}
    for directory in contract.expectations.required_directories:
        if isinstance(directory, str) and directory.casefold() in required_files:
            errors.append(
                "a path cannot be declared as both required file and required directory: "
                f"{directory}"
            )
    if not _is_positive_integer(contract.scan.max_entries):
        errors.append("scan.max_entries must be a positive integer")
    return ContractValidationReport(tuple(errors))


def _required_table(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ContractFormatError(f"contract must contain a [{name}] table")
    return value


def _required_string(table: dict[str, Any], name: str, context: str) -> str:
    value = table.get(name)
    if not isinstance(value, str):
        raise ContractFormatError(f"{context}.{name} must be a string")
    return value


def _required_integer(table: dict[str, Any], name: str, context: str) -> int:
    value = table.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractFormatError(f"{context}.{name} must be an integer")
    return value


def _string_list(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractFormatError(f"{context} must be an array of strings")
    return tuple(value)


def _validate_path_list(values: tuple[str, ...], context: str, errors: list[str]) -> None:
    seen: dict[str, int] = {}
    for index, value in enumerate(values):
        prefix = f"{context}[{index}]"
        if not _is_safe_relative_posix_path(value):
            errors.append(f"{prefix} must be a safe relative POSIX path")
            continue
        normalised = value.casefold()
        previous = seen.get(normalised)
        if previous is not None:
            errors.append(f"{prefix} duplicates {context}[{previous}] after case normalization")
        else:
            seen[normalised] = index


def _is_safe_relative_posix_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        return False
    if value.startswith("/") or any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    parts = value.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return False
    return PurePosixPath(value).as_posix() == value


def _is_nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0
