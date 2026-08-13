from __future__ import annotations

from sessionindex.check import check_project

from .helpers import VALID_CONTRACT, write_contract, write_valid_project


def test_check_inventory_is_metadata_only_stable_and_honours_exclusions(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")

    report = check_project(contract, root)

    assert report.ok
    assert report.contract is not None
    assert [(entry.path, entry.kind) for entry in report.entries] == [
        (".git", "excluded-directory"),
        ("assets", "directory"),
        ("assets/clip.wav", "file"),
        ("cache", "excluded-directory"),
        ("exports", "directory"),
        ("exports/bounce.wav", "file"),
        ("notes", "directory"),
        ("notes/readme.txt", "file"),
        ("session.example", "file"),
    ]
    assert "cache/temporary.bin" not in [entry.path for entry in report.entries]
    assert report.summary.file_count == 4
    assert report.summary.excluded_directory_count == 2
    assert report.status == (
        "DECLARED PROJECT INVENTORY - SOURCE AVAILABILITY, CLOUD STATE, BACKUP, AND EXPORT READINESS UNVERIFIED"
    )


def test_check_reports_missing_required_paths_and_wrong_types(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    (root / "session.example").unlink()
    (root / "assets" / "clip.wav").unlink()
    (root / "assets").rmdir()
    (root / "assets").write_text("wrong kind", encoding="utf-8")

    errors = "\n".join(check_project(contract, root).errors)

    assert "required file is missing: session.example" in errors
    assert "required directory is not a directory: assets" in errors


def test_check_records_but_never_follows_external_symlink(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("outside only", encoding="utf-8")
    (root / "assets" / "external-link").symlink_to(outside, target_is_directory=True)

    report = check_project(contract, root)

    assert report.ok
    assert ("assets/external-link", "symlink") in [(entry.path, entry.kind) for entry in report.entries]
    assert "assets/external-link/secret.txt" not in [entry.path for entry in report.entries]


def test_check_stops_at_declared_max_entry_cap(tmp_path):
    contract = write_contract(tmp_path, VALID_CONTRACT.replace("max_entries = 50", "max_entries = 2"))
    root = write_valid_project(tmp_path / "project")

    errors = "\n".join(check_project(contract, root).errors)

    assert "scan exceeded declared max_entries (2)" in errors


def test_check_rejects_a_project_root_symlink(tmp_path):
    contract = write_contract(tmp_path)
    root = write_valid_project(tmp_path / "project")
    link = tmp_path / "project-link"
    link.symlink_to(root, target_is_directory=True)

    report = check_project(contract, link)

    assert not report.ok
    assert report.errors == ("project directory must not be a symlink",)
