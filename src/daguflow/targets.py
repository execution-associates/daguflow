"""Where a step runs: an SSH host or a container image.

    pi = SSHTarget(user=env.PI_USER, host="192.168.1.50", key=..., ...)
    @task(runs_on=pi, python="/usr/bin/python3")    # a Python function run on the host
    @task.bash(runs_on=pi)                           # a shell command run on the host
    pi.run("uptime", name="uptime", output="RESULT")  # the same, as a plain ssh.run step

An SSHTarget is also what a DAG's top-level `ssh:` key takes
(`DAG(..., ssh=pi)`), which makes every step without an action run on
that host. Mind that: it moves plain `run:` steps there too.
"""

from __future__ import annotations

from typing import Any

from .step import Action, Step

_SSH_KEYS = ("user", "host", "ip", "port", "key", "password", "strict_host_key",
             "known_host_file", "shell", "shell_args", "timeout", "bastion")


class SSHTarget:
    """Connection settings for dagu's ssh.run action, written once and reused."""

    def __init__(
        self,
        *,
        user: Any,
        host: Any,
        port: int | str | None = None,
        key: str | None = None,
        password: Any = None,
        strict_host_key: bool | None = None,
        known_host_file: str | None = None,
        shell: str | list[str] | None = None,
        **extra: Any,
    ):
        unknown = set(extra) - set(_SSH_KEYS)
        if unknown:
            raise TypeError(f"unknown ssh key(s): {', '.join(sorted(unknown))}")
        values = dict(user=user, host=host, port=port, key=key, password=password,
                      strict_host_key=strict_host_key, known_host_file=known_host_file,
                      shell=shell, **extra)
        self.config = {k: values[k] for k in _SSH_KEYS if values.get(k) is not None}

    def action(self, command: Any) -> Action:
        return Action("ssh.run", {**self.config, "command": command})

    def run(self, command: Any, name: str | None = None, **step_opts: Any) -> Step:
        """An ssh.run step on this host."""
        return Step(name, action=self.action(command), **step_opts)

    def with_(self, **overrides: Any) -> SSHTarget:
        """A copy with some settings changed."""
        return SSHTarget(**{**self.config, **overrides})

    def __dagu__(self) -> dict[str, Any]:
        return dict(self.config)

    def __repr__(self) -> str:
        return f"SSHTarget({self.config.get('user')!r}@{self.config.get('host')!r})"


class ContainerTarget:
    """A step-level `container:` (an image to run the step's command in)."""

    def __init__(self, image: str, **config: Any):
        self.config = {"image": image, **config}

    def __dagu__(self) -> dict[str, Any]:
        return dict(self.config)

    def run(self, command: Any, name: str | None = None, **step_opts: Any) -> Step:
        return Step(name, run=command, container=self, **step_opts)


def container(image: str, **config: Any) -> ContainerTarget:
    return ContainerTarget(image, **config)
