"""The built examples on a real dagu: `dagu validate`, then runs through the client."""

from __future__ import annotations

import json

import pytest

from daguflow.client import Status
from daguflow.validate import with_binary

pytestmark = pytest.mark.dagu

DONE = (Status.SUCCEEDED, Status.PARTIALLY_SUCCEEDED)


def test_dagu_validate_accepts_every_built_file(dagu_bin, built_examples):
    files = sorted(built_examples.glob("*.yaml"))
    assert files
    for path in files:
        assert with_binary(path, dagu_bin) == [], path.name


def _run(client, name, **params):
    run_id = client.start(name, params=params or None)
    run = client.wait(name, run_id, timeout=120)
    return run_id, run


def _log(client, name, run_id, step, stream="stdout"):
    return client.step_log(name, run_id, step, stream=stream)


def test_hello_output(dagu_server):
    run_id, run = _run(dagu_server, "hello", who="tests")
    assert run.status == Status.SUCCEEDED, run.raw
    assert dagu_server.outputs("hello", run_id)["greeting"] == "hello tests"


def test_pipeline_python_tasks_subdag_and_loop(dagu_server):
    run_id, run = _run(dagu_server, "pipeline")
    assert run.status in DONE, json.dumps(run.raw)[:3000]
    outputs = dagu_server.outputs("pipeline", run_id, decode=True)
    assert outputs["makeItems"] == [{"n": 0, "label": "item-0"}, {"n": 1, "label": "item-1"},
                                    {"n": 2, "label": "item-2"}]
    assert outputs["total"] == {"sum": 3, "sqrt": 1}
    assert "sum=3" in _log(dagu_server, "pipeline", run_id, "describe")
    assert "this goes to stderr" in _log(dagu_server, "pipeline", run_id, "total", "stderr")
    subs = dagu_server.sub_runs("pipeline", run_id)
    square_runs = [s for s in subs if s.get("dagName", s.get("name")) == "square"] or subs
    assert len(square_runs) >= 3, subs
    assert {n["step"]["name"]: n["statusLabel"] for n in run.nodes}["colors"] == "succeeded"
    assert run.raw.get("onExit", {}).get("statusLabel") == "succeeded"


def test_classic_with_dag_style(dagu_server):
    run_id, run = _run(dagu_server, "classic")
    assert run.status == Status.SUCCEEDED, run.raw
    assert "hi dagu" in _log(dagu_server, "classic", run_id, "first")


def test_call_another_dag_and_read_its_outputs(dagu_server):
    run_id, run = _run(dagu_server, "calls_hello")
    assert run.status == Status.SUCCEEDED, json.dumps(run.raw)[:3000]
    assert "child said hello from-parent" in _log(dagu_server, "calls_hello", run_id, "echo-child")


def test_nested_subdags(dagu_server):
    run_id, run = _run(dagu_server, "nested")
    assert run.status == Status.SUCCEEDED, json.dumps(run.raw)[:3000]
    assert dagu_server.sub_runs("nested", run_id)
