"""The README's lead example builds, validates, and is Python all the way down."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from daguflow.cli import main

REPO = Path(__file__).resolve().parents[1]


def test_the_lead_example_builds(tmp_path):
    code = re.search(r"```python\n(.*?)```", (REPO / "README.md").read_text(), re.S).group(1)
    (tmp_path / "readme_example.py").write_text(code)
    out = tmp_path / "dags"
    assert main(["build", str(tmp_path / "readme_example.py"), "-o", str(out), "--root", str(tmp_path)]) == 0
    docs = list(yaml.safe_load_all((out / "dim_each.yaml").read_text()))
    steps = [s for d in docs for s in d["steps"]]
    assert [s.get("action") for s in steps if s.get("action")] == ["dag.run"]
    python_steps = [s for s in steps if "run" in s]
    assert python_steps and all(s["run"].endswith("| base64 -d | python3 -") for s in python_steps)
