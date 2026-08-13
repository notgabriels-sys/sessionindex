from __future__ import annotations

import json

from sessionindex.cli import main

from .helpers import VALID_CONTRACT, write_contract, write_valid_project


def test_check_command_prints_human_and_json_reports(tmp_path, capsys):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")

    assert main(["check", str(contract), str(root)]) == 0
    human = capsys.readouterr().out
    assert "OK: declared project inventory" in human
    assert "READINESS UNVERIFIED" in human

    assert main(["check", str(contract), str(root), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert report["summary"]["file_count"] == 4


def test_check_command_returns_nonzero_for_missing_required_file(tmp_path, capsys):
    contract = write_contract(tmp_path, VALID_CONTRACT.replace('"session.example"', '"missing.example"'))
    root = write_valid_project(tmp_path / "project")

    assert main(["check", str(contract), str(root)]) == 1
    output = capsys.readouterr().out
    assert "ERROR:" in output
    assert "required file is missing" in output


def test_build_command_creates_snapshot(tmp_path, capsys):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    output = tmp_path / "snapshot"

    assert main(["build", str(contract), str(root), "--output", str(output)]) == 0
    message = capsys.readouterr().out
    assert "Built Sessionindex snapshot" in message
    assert (output / "manifest.json").is_file()
