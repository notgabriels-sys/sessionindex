from __future__ import annotations

from sessionindex.contract import load_contract, validate_contract
from sessionindex.models import Expectations, Project, ProjectContract, ScanConfig

from .helpers import write_contract


def test_load_contract_parses_required_structure_and_scan_limit(tmp_path):
    contract = load_contract(write_contract(tmp_path))

    assert contract.project.title == "Fictional audio-project snapshot"
    assert contract.expectations.required_files == ("session.example",)
    assert contract.expectations.required_directories == ("assets", "exports")
    assert contract.scan.exclude_directories == ("cache", ".git")
    assert contract.scan.max_entries == 50


def test_validate_contract_rejects_unsafe_paths_duplicates_and_bad_limit(tmp_path):
    contract = ProjectContract(
        source=tmp_path / "sessionindex.toml",
        project=Project(title="", kind="", requirements_basis=""),
        expectations=Expectations(
            required_files=("../outside", "session.example", "SESSION.EXAMPLE"),
            required_directories=("assets", "assets"),
        ),
        scan=ScanConfig(exclude_directories=("cache/../bad", "cache"), max_entries=0),
    )

    errors = validate_contract(contract).errors

    assert "project.title must not be blank" in errors
    assert "project.kind must not be blank" in errors
    assert "project.requirements_basis must not be blank" in errors
    assert "expectations.required_files[0] must be a safe relative POSIX path" in errors
    assert "expectations.required_files[2] duplicates expectations.required_files[1] after case normalization" in errors
    assert "expectations.required_directories[1] duplicates expectations.required_directories[0] after case normalization" in errors
    assert "scan.exclude_directories[0] must be a safe relative POSIX path" in errors
    assert "scan.max_entries must be a positive integer" in errors


def test_load_contract_explains_malformed_toml(tmp_path):
    source = write_contract(tmp_path, "[project\ntitle = \"Broken\"\n")

    try:
        load_contract(source)
    except ValueError as error:
        assert "could not parse TOML" in str(error)
    else:
        raise AssertionError("malformed TOML should fail")
