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


@pytest.fixture
def fake_hn():
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    stories = {1: ("Show HN: daguflow", 250), 2: ("Ask HN: dagu?", 40), 3: ("A post-mortem", 120), 4: ("Off", 999)}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/topstories.json":
                body = [1, 2, 3, 4]
            else:
                sid = int(self.path.rsplit("/", 1)[1].removesuffix(".json"))
                title, score = stories[sid]
                body = {"id": sid, "title": title, "score": score, "descendants": sid * 10}
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_hn_digest_fans_out_and_gathers_on_real_dagu(dagu_server, fake_hn):
    run_id, run = _run(dagu_server, "hn_digest", api=fake_hn, limit=3, min_score=100)
    assert run.status == Status.SUCCEEDED, json.dumps(run.raw)[:3000]
    digest = json.loads(dagu_server.outputs("hn_digest", run_id)["digest"])
    assert digest == "  250  Show HN: daguflow\n  120  A post-mortem"
    assert len(dagu_server.sub_runs("hn_digest", run_id)) >= 3
