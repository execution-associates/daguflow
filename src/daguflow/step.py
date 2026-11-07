"""Steps, the containers that hold them, and the `>>` dependency operators."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any, Iterable

from . import _context, schema
from .refs import Ref, iter_refs, render

# Emission order for a step's keys. Anything not listed follows, in the order
# it was given.
STEP_KEY_ORDER = (
    "name", "id", "description", "depends", "preconditions",
    "run", "action", "with", "parallel", "foreach",
    "container", "env", "working_dir", "output", "output_schema", "outputs", "stdout", "stderr",
    "retry_policy", "repeat_policy", "continue_on", "timeout_sec", "signal_on_stop",
    "mail_on_error", "approval", "worker_selector", "pass_env", "stdin", "log_output",
)

_STEP_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_RESERVED_IDS = {"env", "params", "args", "stdout", "stderr", "output", "outputs"}


class Action:
    """A named dagu action and its `with:` block, not yet a step.

    Builders in `daguflow.actions` return these; turn one into a step with
    `.step(...)` or with `Step(action=...)`.
    """

    __slots__ = ("name", "with_")

    def __init__(self, name: str, with_: dict[str, Any] | None = None):
        self.name = name
        self.with_ = {k: v for k, v in (with_ or {}).items() if v is not None}

    def step(self, name: str | None = None, **opts: Any) -> Step:
        return Step(name, action=self, **opts)

    def __repr__(self) -> str:
        return f"Action({self.name!r}, {self.with_!r})"


def _seconds(value: int | float | timedelta | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    return int(value)


DEFAULT_RETRY_INTERVAL = 5


def retry_policy(retries: int | dict | None, interval: int | float | timedelta | None = None) -> dict | None:
    """`retries=3` -> {limit: 3, interval_sec: 5}. dagu requires interval_sec
    whenever a retry_policy is present (measured on 2.24.0); a dict passes through."""
    if retries is None or isinstance(retries, dict):
        return retries
    return {"limit": retries, "interval_sec": _seconds(interval) or DEFAULT_RETRY_INTERVAL}


def _env_list(env: Any) -> Any:
    """A dict becomes dagu's ordered list of one-key maps; lists pass through."""
    if isinstance(env, dict):
        return [{k: v} for k, v in env.items()]
    return env


def _flatten(items: Any) -> list[Step]:
    if isinstance(items, Step):
        return [items]
    out: list[Step] = []
    for item in items:
        out.extend(_flatten(item))
    return out


class Container:
    """Something steps can join: a DAG, a foreach body, a handler slot."""

    def __init__(self) -> None:
        self.steps: list[Step] = []

    def add(self, step: Step) -> None:
        self.steps.append(step)
        step.container = self

    def remove(self, step: Step) -> None:
        self.steps.remove(step)
        step.container = None

    def unique_name(self, base: str) -> str:
        """Airflow's rule for a task called twice: base, base__1, base__2, ..."""
        taken = {s.name for s in self.steps if s.name}
        if base not in taken:
            return base
        n = 1
        while f"{base}__{n}" in taken:
            n += 1
        return f"{base}__{n}"

    def __enter__(self):
        _context.push(self)
        return self

    def __exit__(self, *exc) -> None:
        _context.pop(self)


class Step:
    """One dagu step.

    Keyword arguments are dagu's own step keys (`retry_policy`, `continue_on`,
    `repeat_policy`, `signal_on_stop`, ...), checked against the pinned
    schema so a typo fails at build time rather than at dagu's load. A few
    Python conveniences translate: `retries` (int -> retry_policy, with
    `retry_interval` seconds between tries, default 5),
    `timeout` (seconds or timedelta -> timeout_sec), `env` (dict -> ordered
    list), `shell` (for `run` steps -> with.shell), `with_` (the `with` block).
    """

    def __init__(
        self,
        name: str | None = None,
        *,
        run: str | list[str] | None = None,
        action: Action | str | None = None,
        with_: dict[str, Any] | None = None,
        depends: Step | str | Iterable[Step | str] | None = None,
        output: str | dict | None = None,
        id: str | None = None,
        retries: int | dict | None = None,
        retry_interval: int | float | timedelta | None = None,
        timeout: int | float | timedelta | None = None,
        env: dict[str, Any] | list | None = None,
        shell: str | list[str] | None = None,
        register: bool = True,
        **fields: Any,
    ):
        unknown = set(fields) - schema.step_fields()
        if unknown:
            raise TypeError(f"unknown dagu step key(s): {', '.join(sorted(unknown))}")
        if "with" in fields:
            raise TypeError("pass the with block as with_=")
        if run is not None and action is not None:
            raise TypeError("a step takes run= or action=, not both")
        if id is not None and (not _STEP_ID.match(id) or id.lower() in _RESERVED_IDS or len(id) > 40):
            raise ValueError(f"invalid step id {id!r}: [A-Za-z][A-Za-z0-9_]*, max 40, not reserved")

        self.name = name
        self.id = id
        self.body: Container | None = None  # a foreach step's inline steps
        self.container: Container | None = None
        self.upstream: list[Step | str] = []
        self.spec: dict[str, Any] = {}

        if run is not None:
            self.spec["run"] = run
        self._set_action(action, with_)
        if shell is not None:
            if run is None:
                raise TypeError("shell= applies to run steps; ssh targets take shell in their with block")
            self.spec.setdefault("with", {})["shell"] = shell
        self.configure(env=env, output=output, retries=retries, retry_interval=retry_interval,
                       timeout=timeout, depends=depends, **fields)

        container = _context.current() if register else None
        if container is not None:
            if self.name is None:
                self.name = container.unique_name(self._default_name())
            container.add(self)

    def _set_action(self, action: Action | str | None, with_: dict[str, Any] | None) -> None:
        if isinstance(action, Action):
            self.spec["action"] = action.name
            merged = dict(action.with_)
            merged.update(with_ or {})
            if merged or action.name != "noop":
                self.spec["with"] = merged
        elif action is not None:
            self.spec["action"] = action
            if with_ is not None:
                self.spec["with"] = dict(with_)
        elif with_ is not None:
            self.spec["with"] = dict(with_)

    def configure(
        self,
        *,
        env: Any = None,
        output: Any = None,
        retries: int | dict | None = None,
        retry_interval: int | float | timedelta | None = None,
        timeout: int | float | timedelta | None = None,
        depends: Any = None,
        **fields: Any,
    ) -> Step:
        """Set step options after creation."""
        unknown = set(fields) - schema.step_fields()
        if unknown:
            raise TypeError(f"unknown dagu step key(s): {', '.join(sorted(unknown))}")
        if env is not None:
            self.spec["env"] = _env_list(env)
        if output is not None:
            self.spec["output"] = output
        if retries is not None:
            self.spec["retry_policy"] = retry_policy(retries, retry_interval)
        if timeout is not None:
            self.spec["timeout_sec"] = _seconds(timeout)
        for key, value in fields.items():
            if value is not None:
                self.spec[key] = value
        if depends is not None:
            self.set_upstream(depends if not isinstance(depends, (str, Step)) else [depends])
        return self

    # -- naming -------------------------------------------------------------

    def _default_name(self) -> str:
        if self.id:
            return self.id
        action = self.spec.get("action")
        if action:
            return str(action).replace(".", "-")
        return "step"

    @property
    def ref_name(self) -> str:
        """How other steps address this one in `${<step>.outputs...}` refs."""
        return self.id or self.name or ""

    # -- outputs ------------------------------------------------------------

    def _task_input(self) -> Ref:
        """What a @task receives when this step is passed to it: its output."""
        return self.output

    @property
    def output(self) -> Ref:
        """This step's captured stdout as a Ref (`${VAR}`).

        Reading it gives a step with no `output:` one named after the step,
        upper-cased, so `fetch` captures into FETCH.
        """
        out = self.spec.get("output")
        if out is None:
            var = re.sub(r"[^A-Za-z0-9_]", "_", self.ref_name).upper() or "OUTPUT"
            self.spec["output"] = var
            out = var
        if isinstance(out, str):
            return Ref(out, producer=self)
        return Ref(f"{self.ref_name}.output", producer=self)

    @property
    def outputs(self) -> Ref:
        """`${<step>.outputs}`: action outputs, or a child DAG's published outputs."""
        return Ref(f"{self.ref_name}.outputs", producer=self)

    @property
    def exit_code(self) -> Ref:
        return Ref(f"{self.ref_name}.exit_code", producer=self)

    def __getitem__(self, key: str | int) -> Ref:
        return self.output[key]

    def __format__(self, spec: str) -> str:
        # f"{fetch}" means the step's output, as in TaskFlow.
        return format(self.output, spec)

    # -- dependencies -------------------------------------------------------

    def set_upstream(self, others: Any) -> None:
        for other in ([others] if isinstance(others, (Step, str)) else others):
            if isinstance(other, (list, tuple)):
                self.set_upstream(other)
            elif other is self:
                raise ValueError(f"step {self.name!r} cannot depend on itself")
            elif all(other is not u for u in self.upstream):
                self.upstream.append(other)

    def set_downstream(self, others: Any) -> None:
        for other in _flatten(others):
            other.set_upstream(self)

    def __rshift__(self, other: Any) -> Any:
        self.set_downstream(other)
        return other

    def __lshift__(self, other: Any) -> Any:
        self.set_upstream(_flatten(other))
        return other

    def __rrshift__(self, other: Any) -> Step:
        # [a, b] >> step
        self.set_upstream(_flatten(other))
        return self

    def __rlshift__(self, other: Any) -> Any:
        # [a, b] << step
        for s in _flatten(other):
            s.set_upstream(self)
        return other

    def refs(self) -> list[Ref]:
        """Ref objects this step was given, its foreach body's included."""
        found = list(iter_refs(self.spec))
        if self.body is not None:
            for inner in self.body.steps:
                found.extend(inner.refs())
        return found

    def text(self) -> str:
        """Everything this step renders, as one string, for reference scanning."""
        import json

        parts = [json.dumps(render(self.spec))]
        if self.body is not None:
            parts.extend(inner.text() for inner in self.body.steps)
        return "\n".join(parts)

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if self.name:
            body["name"] = self.name
        if self.id:
            body["id"] = self.id
        if self.upstream:
            names = [u if isinstance(u, str) else u.name for u in self.upstream]
            body["depends"] = names[0] if len(names) == 1 else names
        rendered = render(self.spec)
        if self.body is not None:
            loop = rendered["foreach"]
            loop["steps"] = [s.to_dict() for s in self.body.steps]
            rendered["foreach"] = {k: loop[k] for k in ("items", "as", "key", "max_concurrent", "steps", "collect") if k in loop}
        for key in STEP_KEY_ORDER:
            if key in rendered and key not in body:
                body[key] = rendered[key]
        for key, value in rendered.items():
            if key not in body:
                body[key] = value
        return body

    def __repr__(self) -> str:
        return f"Step({self.name!r})"


def step(name: str | None = None, **opts: Any) -> Step:
    """Operator-style step creation: `step("build", run="make")`."""
    return Step(name, **opts)


def shell(command: str | list[str], name: str | None = None, **opts: Any) -> Step:
    """A local `run:` step."""
    return Step(name, run=command, **opts)


def chain(*steps: Any) -> None:
    """chain(a, b, [c, d], e): each element runs after the one before it."""
    for left, right in zip(steps, steps[1:]):
        for r in _flatten(right):
            r.set_upstream(_flatten(left))
