"""The README leads with examples/hn_digest.py, word for word, and it is Python all the way down."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from daguflow.cli import main

REPO = Path(__file__).resolve().parents[1]


def test_the_lead_example_is_examples_hn_digest():
    code = re.search(r"```python\n(.*?)```", (REPO / "README.md").read_text(), re.S).group(1)
    assert code == (REPO / "examples" / "hn_digest.py").read_text()


def test_every_step_of_it_is_python(tmp_path):
    assert main(["build", str(REPO / "examples" / "hn_digest.py"), "-o", str(tmp_path), "--root", str(REPO)]) == 0
    steps = [s for d in yaml.safe_load_all((tmp_path / "hn_digest.yaml").read_text()) for s in d["steps"]]
    assert [s["action"] for s in steps if "action" in s] == ["dag.run"]
    assert all(s["run"].endswith("| base64 -d | python3 -") for s in steps if "run" in s)


def test_the_sub_dag_section_shows_examples_hn_threads_word_for_word():
    blocks = re.findall(r"```python\n(.*?)```", (REPO / "README.md").read_text(), re.S)
    assert (REPO / "examples" / "hn_threads.py").read_text() in blocks
