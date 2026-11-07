import keyword
import subprocess
import sys
from pathlib import Path

import pytest

from daguflow import DAG, SSHTarget, actions, schema

REPO = Path(__file__).resolve().parents[1]


def test_generated_builders_match_the_schema():
    fresh = subprocess.run([sys.executable, str(REPO / "tools" / "gen_actions.py")], capture_output=True,
                           text=True, check=True).stdout
    committed = (REPO / "src/daguflow/actions/_generated.py").read_text()
    assert fresh == committed, "run: python tools/gen_actions.py > src/daguflow/actions/_generated.py"


def _py(name: str) -> str:
    return name + "_" if keyword.iskeyword(name) else name


def test_every_builtin_action_has_a_builder():
    for name in schema.builtin_actions():
        head, _, rest = name.partition(".")
        if not rest:
            fn = getattr(actions, head + "_", None) or getattr(actions, head)
        else:
            fn = getattr(getattr(actions, head), _py(rest.replace(".", "_")))
        assert callable(fn), name


def test_required_and_closed_keys():
    a = actions.http.request(method="POST", url="https://x", json=True, headers={"A": "b"})
    assert a.name == "http.request" and a.with_["method"] == "POST"
    with pytest.raises(TypeError):
        actions.http.request(url="https://x")  # method missing
    with pytest.raises(TypeError):
        actions.dag.run(dag="x", bogus=1)  # dagRunActionConfig is closed
    assert actions.data.convert(from_="json", to="yaml", data="{}").with_["from"] == "json"


def test_ssh_builder_and_target_agree():
    target = SSHTarget(user="u", host="h", port=22)
    assert actions.ssh.Target is SSHTarget
    built = actions.ssh.run(user="u", host="h", port=22, command="ls")
    assert target.action("ls").with_ == built.with_
    assert list(built.with_) == ["user", "host", "port", "command"]
    with pytest.raises(TypeError):
        SSHTarget(user="u", host="h", hots="typo")


def test_custom_and_redis():
    assert actions.custom("dagucloud/duckdb@v1", query="select 1").name == "dagucloud/duckdb@v1"
    assert actions.redis("get", key="k").name == "redis.get"


def test_actions_become_valid_steps():
    with DAG("acts") as d:
        actions.noop().step("nothing")
        actions.wait.duration(duration="1s").step("pause")
        actions.jq.filter(filter=".a", data={"a": 1}).step("pick", output="PICKED")
        actions.mail.send(from_="a@x", to="b@x", subject="s", message="m").step("mail")
    d.to_yaml()  # validates against the schema
    steps = d.to_dict()["steps"]
    assert steps[0] == {"name": "nothing", "action": "noop"}
    assert steps[3]["with"]["from"] == "a@x"
