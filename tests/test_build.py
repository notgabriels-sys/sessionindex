from __future__ import annotations

import csv
import json

import pytest

from sessionindex.build import BuildError, build_snapshot

from .helpers import VALID_CONTRACT, write_contract, write_valid_project


def test_build_creates_relative_metadata_snapshot_without_changing_sources(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    before = (root / "assets" / "clip.wav").read_bytes()
    output = tmp_path / "snapshot"

    result = build_snapshot(contract, root, output)

    assert result.output_dir == output
    assert (output / "PROJECT_INDEX.md").is_file()
    assert (output / "file_inventory.csv").is_file()
    assert (output / "manifest.json").is_file()
    assert (root / "assets" / "clip.wav").read_bytes() == before

    index = (output / "PROJECT_INDEX.md").read_text(encoding="utf-8")
    assert "DECLARED PROJECT INVENTORY" in index
    assert "does not prove source availability, cloud state, backup, or export readiness" in index
    assert str(root) not in index

    with (output / "file_inventory.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["path"] == ".git"
    assert rows[0]["kind"] == "excluded-directory"
    assert all("/private/" not in row["path"] for row in rows)

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "sessionindex-manifest/v1"
    assert manifest["project_root"]["directory_name"] == "project"
    assert manifest["summary"]["file_count"] == 4
    assert all("source_path" not in entry for entry in manifest["entries"])


def test_build_does_not_write_when_check_fails(tmp_path):
    contract = write_contract(tmp_path, VALID_CONTRACT.replace('"session.example"', '"missing.example"'))
    root = write_valid_project(tmp_path / "project")
    output = tmp_path / "snapshot"

    with pytest.raises(BuildError, match="required file is missing"):
        build_snapshot(contract, root, output)

    assert not output.exists()


def test_build_refuses_to_overwrite_existing_output(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    output = tmp_path / "snapshot"
    output.mkdir()
    (output / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(BuildError, match="already exists"):
        build_snapshot(contract, root, output)

    assert (output / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_build_refuses_to_write_snapshot_inside_selected_project_root(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    output = root / "snapshot"

    with pytest.raises(BuildError, match="outside the selected project root"):
        build_snapshot(contract, root, output)

    assert not output.exists()
