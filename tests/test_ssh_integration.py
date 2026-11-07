"""ssh.run steps and @task over SSH, on a real dagu against a real sshd.

The free-text value goes through dagu's "${x}" re-quoting and the heredoc
argument path exactly as it would to a remote host.
"""

from __future__ import annotations

import sys
from typing import Annotated

import pytest

from daguflow import Pattern, SSHTarget, dag, task
from daguflow.client import Status

pytestmark = pytest.mark.dagu

SAFE_TEXT = r"^[A-Za-z0-9 '&()-]*$"  # what the automations bridge admits
NASTY = {"q": "it's \"quoted\"", "dollar": "$HOME ${PATH} $(id)", "back": "`id`", "amp": "a & b; c"}


def test_ssh_quoting_and_python_over_ssh(dagu_server, built_examples, sshd):
    target = SSHTarget(user=sshd.user, host="127.0.0.1", port=sshd.port, key=sshd.key,
                       strict_host_key=True, known_host_file=sshd.known_hosts)

    @task(runs_on=target, python=sys.executable)
    def make() -> dict:
        return {"q": "it's \"quoted\"", "dollar": "$HOME ${PATH} $(id)", "back": "`id`", "amp": "a & b; c"}

    @task(runs_on=target, python=sys.executable, unsafe_args=True)
    def echo_back(payload: dict, label: str) -> dict:
        return {"payload": payload, "label": label}

    @dag
    def ssh_roundtrip(effect: Annotated[str, Pattern(SAFE_TEXT)] = "x"):
        made = make()
        target.run(f"{sys.executable} -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "
                   f"--name {effect:q}", name="quoted", output="QUOTED")
        echo_back(made, effect)

    (built_examples / "ssh_roundtrip.yaml").write_text(ssh_roundtrip.to_yaml())
    effect = "Rock 'n' Roll (Live) & More"
    run_id = dagu_server.start("ssh_roundtrip", params={"effect": effect})
    run = dagu_server.wait("ssh_roundtrip", run_id, timeout=120)
    assert run.status == Status.SUCCEEDED, [n.get("error") for n in run.nodes]
    outputs = dagu_server.outputs("ssh_roundtrip", run_id, decode=True)
    assert outputs["quoted"] == ["--name", effect]
    assert outputs["echoBack"] == {"payload": NASTY, "label": effect}
