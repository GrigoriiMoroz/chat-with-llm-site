from importlib.metadata import version
from pathlib import Path


def test_runtime_versions_match_lock():
    for line in Path("requirements.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            package, expected = line.split("==")
            assert version(package) == expected, package


def test_python_version_is_consistent():
    assert Path(".python-version").read_text().strip() == "3.12"
    assert "Python 3.14" not in Path("CLAUDE.md").read_text()
    assert "FROM python:3.12-slim" in Path("dockerfile").read_text()
