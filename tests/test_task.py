import base64
import json
import os
import re
import subprocess
import sys
from typing import Annotated, Literal

import pytest

from daguflow import DAG, Pattern, Range, SSHTarget, Step, actions, container, dag, env, shell, task
from daguflow.task import function_source

pi = SSHTarget(user=env.U, host="10.0.0.1", port=22, key="/k", strict_host_key=True,
                   known_host_file="/kh")


@task(runs_on=pi, output="RESULT")
def power(action):
    return f"/usr/bin/python3 lights.py power --action {action}"


@task
def http_get(url):
    return actions.http.request(method="GET", url=url)


@task
def makes_its_own_step():
    return shell("echo own", name="ignored", output="OWN")


def test_build_time_task_forms():
    @dag
    def d(action="toggle"):
        power(action)
        power.override(name="power-off")("off")
        http_get("https://x")
        makes_its_own_step()
        power("on")

    steps = d.to_dict()["steps"]
    assert [s["name"] for s in steps] == ["power", "power-off", "http_get", "makes_its_own_step", "power__1"]
    assert steps[0]["action"] == "ssh.run"
    assert steps[0]["with"]["command"] == "/usr/bin/python3 lights.py power --action ${action}"
    assert steps[0]["with"]["user"] == "${env.U}" and steps[0]["output"] == "RESULT"
    assert steps[2] == {"name": "http_get", "action": "http.request",
                        "with": {"method": "GET", "url": "https://x"}}
    assert steps[3]["run"] == "echo own" and steps[3]["output"] == "OWN"


def test_task_outside_a_dag():
    with pytest.raises(RuntimeError):
        power("x")


def test_task_returning_garbage():
    @task
    def bad():
        return 42

    with DAG("d"):
        with pytest.raises(TypeError, match="command string"):
            bad()


def test_passing_a_step_links_it():
    @task
    def consume(thing):
        return f"echo {thing}"

    with DAG("d") as d:
        made = shell("echo hi", name="made")
        consume(made)
    use = d.to_dict()["steps"][1]
    assert use == {"name": "consume", "depends": "made", "run": "echo ${MADE}"}


def test_container_target():
    @task(runs_on=container("alpine:3.20"))
    def in_box():
        return "uname -a"

    with DAG("d") as d:
        in_box()
    assert d.to_dict()["steps"][0]["container"] == {"image": "alpine:3.20"}


# -- @task.python -----------------------------------------------------------------

GLOBAL_THING = 3


def test_python_tasks_must_be_self_contained():
    def uses_global():
        return GLOBAL_THING

    with pytest.raises(TypeError, match="GLOBAL_THING"):
        task.python(uses_global)

    value = 1

    def closure():
        return value

    with pytest.raises(TypeError, match="closes over"):
        task.python(closure)

    def fine(x: int) -> int:
        import math

        total = 0
        for i in range(x):
            total += math.floor(i)
        return total

    assert "def fine" in function_source(fine)


def _decoded(command: str) -> str:
    payload = re.search(r"echo ([A-Za-z0-9+/=]+) \|", command).group(1)
    return base64.b64decode(payload).decode()


@task.python
def add(a: int, b: int, label: str = "sum") -> dict:
    print("noise")
    return {label: a + b}


def test_local_python_task_runs_for_real():
    with DAG("d") as d:
        first = shell("echo 40", name="first")
        add(first, 2, label="total")
    step = d.to_dict()["steps"][1]
    assert step["depends"] == "first" and step["output"] == "ADD"
    assert step["env"] == [{"DAGUFLOW_ARG_a": "${FIRST}"}]
    proc = subprocess.run([sys.executable, "-"], input=_decoded(step["run"]), text=True,
                          capture_output=True, env={**os.environ, "DAGUFLOW_ARG_a": "40"})
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"total": 42}
    assert "noise" in proc.stderr


def _sh_render(command: str, values: dict[str, str]) -> str:
    # What dagu does to an SSH command: unquoted ${X} becomes the raw value.
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_.]*)\}", lambda m: values[m.group(1)], command)


def test_ssh_python_task_passes_hostile_values_byte_for_byte():
    @task.python(runs_on=pi, python=sys.executable, unsafe_args=True)
    def echo_back(payload: dict, label: str) -> dict:
        return {"payload": payload, "label": label}

    @dag
    def d(label: Annotated[str, Pattern(r"^[A-Za-z ']*$")] = "x"):
        src = shell("emit", name="src")
        echo_back(src, label)

    step = d.to_dict()["steps"][1]
    command = step["with"]["command"]
    assert "DAGUFLOW_EOF" in command and step["depends"] == "src"
    nasty = {"q": "it's \"quoted\"", "dollar": "$HOME ${PATH} $(id)", "back": "`id`", "nl": "a\nb"}
    rendered = _sh_render(command, {"SRC": json.dumps(nasty), "label": "Rock 'n' Roll"})
    proc = subprocess.run(["sh", "-c", rendered], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"payload": nasty, "label": "Rock 'n' Roll"}


def test_ssh_python_task_refuses_unconstrained_params():
    @task.python(runs_on=pi)
    def takes(text: str) -> str:
        return text

    with pytest.raises(TypeError, match="unconstrained"):
        @dag
        def d(text=""):
            takes(text)

    @dag
    def ok(level: Annotated[int, Range(0, 3)] = 1, mode: Literal["a", "b"] = "a"):
        takes(level)
        takes(mode)

    assert len(ok.to_dict()["steps"]) == 2


def test_ssh_python_task_refuses_step_outputs_and_newline_patterns():
    @task.python(runs_on=pi)
    def takes(value: str) -> str:
        return value

    with pytest.raises(TypeError, match="unconstrained value"):
        @dag
        def from_step():
            takes(shell("emit", name="src"))

    for loose in (r"[a-z]+", r"^[\w\s]*$", r"^[^;]*$", r"(?s)^.*$"):
        with pytest.raises(TypeError, match="unconstrained value"):
            @dag
            def from_pattern(text: Annotated[str, Pattern(loose)] = "x"):
                takes(text)

    @dag
    def tight(text: Annotated[str, Pattern(r"^[A-Za-z ']*$")] = "x"):
        takes(text)

    assert len(tight.to_dict()["steps"]) == 1

    @task.python(runs_on=pi, unsafe_args=True)
    def trusted(value: str) -> str:
        return value

    @dag
    def opted_in():
        trusted(shell("emit", name="src"))

    assert len(opted_in.to_dict()["steps"]) == 2


def test_python_task_with_deps_uses_uv():
    @task.python(deps=["httpx"], python="python3")
    def fetch() -> int:
        import httpx  # noqa: F401

        return 1

    with DAG("d") as d:
        fetch()
    assert "uv run --quiet --no-project --with httpx -- python3 -" in d.to_dict()["steps"][0]["run"]


def test_python_constants_must_be_json():
    @task.python
    def f(x: object) -> None:
        return None

    with DAG("d"):
        with pytest.raises(TypeError, match="JSON"):
            f(object())
        assert isinstance(f({"a": [1, 2]}), Step)
