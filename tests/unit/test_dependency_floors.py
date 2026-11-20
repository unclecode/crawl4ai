"""Dependency floors must exclude builds with known decoder bugs.

CVE-2026-111497 is an out-of-bounds write in Google's Brotli decoder. It is in
the Python brotli package before 1.2.1, and in the Node.js runtime that
playwright and patchright bundle as their driver before 1.64.1 and 1.64.2.
A crawled server chooses the response body, so a floor that still allows an
affected build lets pip install one.
"""

import pathlib

import pytest
from packaging.requirements import Requirement

tomllib = pytest.importorskip("tomllib")

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Newest affected release of each package.
AFFECTED = {
    "brotli": "1.2.0",
    "playwright": "1.64.0",
    "patchright": "1.64.1",
}


def _pyproject_reqs():
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    return [Requirement(d) for d in deps]


def _requirements_txt_reqs():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    return [Requirement(l) for l in lines if l.strip() and not l.lstrip().startswith("#")]


@pytest.mark.parametrize("source", [_pyproject_reqs, _requirements_txt_reqs], ids=["pyproject", "requirements"])
@pytest.mark.parametrize("name,affected", AFFECTED.items())
def test_floor_excludes_affected_version(source, name, affected):
    req = next(r for r in source() if r.name.lower() == name)
    assert not req.specifier.contains(affected), f"{req} still allows {name} {affected}"
