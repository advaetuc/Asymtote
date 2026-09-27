"""Deployment configuration constraints validated before Vercel builds the app."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_python_function_exclude_glob_fits_vercel_limit():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    pattern = config["functions"]["api/index.py"]["excludeFiles"]
    assert isinstance(pattern, str)
    assert 0 < len(pattern) <= 256, "Vercel limits excludeFiles to 256 characters."
