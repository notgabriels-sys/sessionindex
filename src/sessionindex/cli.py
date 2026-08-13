from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .build import BuildError, build_snapshot
from .check import check_project


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "check":
        report = check_project(arguments.contract, arguments.project_directory)
        if arguments.json:
            print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
        elif report.ok:
            contract = report.contract
            summary = report.summary
            assert contract is not None and summary is not None
            print(
                f"OK: declared project inventory for {contract.project.title!s} contains "
                f"{summary.entry_count} metadata entry(s)."
            )
            print(f"Status: {report.status}.")
        else:
            for error in report.errors:
                print(f"ERROR: {error}")
        return 0 if report.ok else 1

    if arguments.command == "build":
        try:
            result = build_snapshot(arguments.contract, arguments.project_directory, arguments.output)
        except BuildError as error:
            print(f"ERROR: {error}")
            return 1
        print(f"Built Sessionindex snapshot: {result.output_dir}")
        print(
            "Status: DECLARED PROJECT INVENTORY - SOURCE AVAILABILITY, CLOUD STATE, BACKUP, "
            "AND EXPORT READINESS UNVERIFIED."
        )
        return 0

    parser.error(f"unsupported command: {arguments.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sessionindex",
        description="Create a metadata-only project inventory without reading file contents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="validate and scan a selected project root")
    check_parser.add_argument("contract", type=Path, help="path to a Sessionindex TOML file")
    check_parser.add_argument("project_directory", type=Path, help="project root to inventory read-only")
    check_parser.add_argument("--json", action="store_true", help="print a machine-readable report")

    build_parser = subparsers.add_parser("build", help="write a new complete metadata snapshot")
    build_parser.add_argument("contract", type=Path, help="path to a Sessionindex TOML file")
    build_parser.add_argument("project_directory", type=Path, help="project root to inventory read-only")
    build_parser.add_argument("--output", required=True, type=Path, help="new output directory")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
