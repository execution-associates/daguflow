"""task.expand / partial / expand_kwargs: Airflow's dynamic task mapping, as a parallel local sub-DAG."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

import pytest
import yaml

from daguflow import DAG, dag, shell, task


@task
def fetch(api: str, story_id: int, verbose: bool = False) -> dict:
    return {"api": api, "id": story_id, "verbose": verbose}


@task
def ids(n: int) -> list:
    return list(range(n))


@task
def summarize(stories: list) -> int:
    return len(stories)


def _docs(d):
    return list(yaml.safe_load_all(d.to_yaml()))


def _script(step: dict) -> str:
    return base64.b64decode(re.search(r"echo ([A-Za-z0-9+/=]+) \|", step["run"]).group(1)).decode()


def test_expand_over_a_step_output_with_fixed_arguments():
    @dag
    def digest(api: str = "https://x"):
        found = ids(3)
        stories = fetch.partial(api=api, verbose=True).expand(story_id=found, max_concurrent=4)
        summarize(stories)

    entry, child = _docs(digest)
    call, gather = entry["steps"][1], entry["steps"][2]
    assert call["name"] == "fetch" and call["depends"] == "ids" and call["action"] == "dag.run"
    assert call["with"] == {"dag": "fetch", "params": {"story_id": "${ITEM}", "api": "${api}"}}
    assert call["parallel"] == {"items": "${IDS}", "max_concurrent": 4}
    assert gather["depends"] == "fetch" and gather["env"] == [{"DAGUFLOW_ARG_stories": "${FETCH}"}]
    assert child["name"] == "fetch" and [s["name"] for s in child["steps"]] == ["fetch"]
    inner = child["steps"][0]
    assert inner["env"] == [{"DAGUFLOW_ARG_api": "${api}"}, {"DAGUFLOW_ARG_story_id": "${story_id}"}]
    assert '"verbose": true' in _script(inner), "a constant is baked into the child, not passed"


def test_a_child_run_calls_the_function_with_its_item():
    @dag
    def d():
        fetch.partial(api="https://x").expand(story_id=[7, 8])

    _, child = _docs(d)
    proc = subprocess.run([sys.executable, "-"], input=_script(child["steps"][0]), text=True, capture_output=True,
                          env={**os.environ, "DAGUFLOW_ARG_story_id": "7"})
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"api": "https://x", "id": 7, "verbose": False}


def test_several_mapped_lists_run_every_combination():
    @task
    def cell(row: str, col: int) -> str:
        return f"{row}{col}"

    @dag
    def grid():
        cell.expand(row=["a", "b"], col=[1, 2])

    entry, child = _docs(grid)
    call = entry["steps"][0]
    assert json.loads(call["parallel"]) == [{"row": "a", "col": 1}, {"row": "a", "col": 2},
                                            {"row": "b", "col": 1}, {"row": "b", "col": 2}]
    assert call["with"]["params"] == {"mapped_kwargs": "${ITEM}"}
    proc = subprocess.run([sys.executable, "-"], input=_script(child["steps"][0]), text=True, capture_output=True,
                          env={**os.environ, "DAGUFLOW_ARG_mapped_kwargs": '{"row": "b", "col": 2}'})
    assert json.loads(proc.stdout) == "b2", proc.stderr


def test_expand_kwargs_from_a_list_and_from_a_step():
    @task
    def pairs() -> list:
        return [{"story_id": 1}, {"story_id": 2}]

    @dag
    def d():
        fetch.expand_kwargs([{"api": "a", "story_id": 1}, {"api": "b", "story_id": 2}])
        fetch.partial(api="c").expand_kwargs(pairs())

    entry, _, made_child = _docs(d)
    literal, _, made = entry["steps"]
    assert literal["with"]["params"] == {"mapped_kwargs": "${ITEM}"}
    assert made["name"] == "fetch__1" and made["parallel"] == "${PAIRS}"
    assert made["with"]["params"] == {"mapped_kwargs": "${ITEM}"}
    proc = subprocess.run([sys.executable, "-"], input=_script(made_child["steps"][0]), text=True, capture_output=True,
                          env={**os.environ, "DAGUFLOW_ARG_mapped_kwargs": '{"story_id": 2, "verbose": true}'})
    assert json.loads(proc.stdout) == {"api": "c", "id": 2, "verbose": True}, "a defaulted key in the dict is used"
    proc = subprocess.run([sys.executable, "-"], input=_script(made_child["steps"][0]), text=True, capture_output=True,
                          env={**os.environ, "DAGUFLOW_ARG_mapped_kwargs": '{"story_id": 3}'})
    assert json.loads(proc.stdout) == {"api": "c", "id": 3, "verbose": False}, "a missing one takes the default"


def test_expanding_twice_gives_distinct_names_and_documents():
    @dag
    def d():
        fetch.partial(api="a").expand(story_id=[1])
        fetch.partial(api="b").expand(story_id=[2])

    docs = _docs(d)
    assert [s["name"] for s in docs[0]["steps"]] == ["fetch", "fetch__1"]
    assert [doc["name"] for doc in docs[1:]] == ["fetch", "fetch__1"]


def test_mistakes_are_named_at_build_time():
    with DAG("d"):
        with pytest.raises(TypeError, match="no argument"):
            fetch.expand(nope=[1])
        with pytest.raises(TypeError, match="both fixed and mapped"):
            fetch.partial(story_id=1, api="a").expand(story_id=[1])
        with pytest.raises(TypeError, match="api"):
            fetch.expand(story_id=[1])  # api is required and neither fixed nor mapped
        with pytest.raises(TypeError, match="literal lists"):
            fetch.partial(api="a").expand(story_id=ids(2), verbose=[True, False])
        with pytest.raises(TypeError, match="list or a step"):
            fetch.partial(api="a").expand(story_id=5)
        mapped = fetch.partial(api="a").expand(story_id=[1])
        with pytest.raises(TypeError, match="not a list dagu can fan out over"):
            fetch.partial(api="a").expand(story_id=mapped)
        with pytest.raises(TypeError, match="item 1"):
            fetch.expand_kwargs([{"api": "a", "story_id": 1}, {"story_id": 2}])
        with pytest.raises(TypeError, match="no argument"):
            fetch.expand_kwargs([{"api": "a", "story_id": 1, "colour": "red"}])
    with pytest.raises(RuntimeError, match="outside a DAG"):
        fetch.partial(api="a").expand(story_id=[1])


def test_a_mapped_shell_step_input_is_its_raw_output():
    with DAG("d") as d:
        mapped = fetch.partial(api="a").expand(story_id=[1])
        shell(f"echo {mapped.output}", name="raw")
    assert d.to_dict()["steps"][1]["run"] == "echo ${FETCH}"


def test_literal_lists_of_dicts_reach_dagu_as_json_so_types_survive():
    @task
    def take(row: dict) -> int:
        return row["n"]

    @dag
    def d():
        take.expand(row=[{"n": 1}, {"n": 2}])
        take.expand(row=[1, 2])

    steps = _docs(d)[0]["steps"]
    assert json.loads(steps[0]["parallel"]) == [{"n": 1}, {"n": 2}]
    assert steps[1]["parallel"] == [1, 2], "scalars stay readable YAML"
