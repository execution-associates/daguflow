import json

import httpx
import pytest

from daguflow.client import Client, DaguError, Status


def _client(handler):
    return Client("http://dagu:8080", transport=httpx.MockTransport(handler))


def test_base_path_is_added_and_params_are_json():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"dagRunId": "r1"})

    assert _client(handler).start("d", params={"effect": "Rock 'n' Roll", "value": 5}) == "r1"
    assert seen["url"] == "http://dagu:8080/api/v1/dags/d/start"
    assert json.loads(seen["body"]["params"]) == {"effect": "Rock 'n' Roll", "value": 5}


def test_status_reads_either_wrapper_and_wait_polls():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        status = 1 if calls["n"] < 3 else 4
        key = "dagRunDetails" if calls["n"] % 2 else "dagRun"
        return httpx.Response(200, json={key: {"name": "d", "dagRunId": "r", "status": status,
                                               "statusLabel": Status(status).name.lower(), "nodes": []}})

    run = _client(handler).wait("d", "r", interval=0.01)
    assert run.status == Status.SUCCEEDED and run.succeeded and calls["n"] == 3


def test_outputs_decode():
    def handler(request):
        return httpx.Response(200, json={"outputs": {"result": '{"ok": true}', "plain": "x"}})

    assert _client(handler).outputs("d", "r", decode=True) == {"result": {"ok": True}, "plain": "x"}


def test_errors_carry_dagu_codes():
    def handler(request):
        return httpx.Response(404, json={"code": "not_found", "message": "DAG not found"})

    with pytest.raises(DaguError) as e:
        _client(handler).status("d", "r")
    assert e.value.status_code == 404 and e.value.code == "not_found"


def test_validate_and_inline_run():
    def handler(request):
        body = json.loads(request.content)
        if request.url.path.endswith("/dags/validate"):
            return httpx.Response(200, json={"valid": False, "errors": ["bad"]})
        assert "spec" in body
        return httpx.Response(200, json={"dagRunId": "inline"})

    c = _client(handler)
    assert c.validate("steps: []") == {"valid": False, "errors": ["bad"]}
    assert c.run_inline("steps: [{name: a, run: x}]", name="adhoc") == "inline"
