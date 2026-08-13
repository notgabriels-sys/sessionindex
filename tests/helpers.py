from __future__ import annotations

from pathlib import Path


VALID_CONTRACT = '''
[project]
title = "Fictional audio-project snapshot"
kind = "Example digital-audio project"
requirements_basis = "Read-only pre-copy inventory for a fictional example project."

[expectations]
required_files = ["session.example"]
required_directories = ["assets", "exports"]

[scan]
exclude_directories = ["cache", ".git"]
max_entries = 50
'''.lstrip()


def write_contract(tmp_path: Path, content: str = VALID_CONTRACT) -> Path:
    path = tmp_path / "sessionindex.toml"
    path.write_text(content, encoding="utf-8")
    return path


def write_valid_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "session.example").write_text("fictional project marker\n", encoding="utf-8")
    (root / "assets").mkdir()
    (root / "assets" / "clip.wav").write_bytes(b"fictional-audio-data")
    (root / "exports").mkdir()
    (root / "exports" / "bounce.wav").write_bytes(b"fictional-export-data")
    (root / "notes").mkdir()
    (root / "notes" / "readme.txt").write_text("fictional notes\n", encoding="utf-8")
    (root / "cache").mkdir()
    (root / "cache" / "temporary.bin").write_bytes(b"not-scanned")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("not-scanned\n", encoding="utf-8")
    return root
