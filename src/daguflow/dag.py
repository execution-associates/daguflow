"""DAGs: the `with DAG(...)` block and the `@dag` decorator."""

from __future__ import annotations

import inspect
import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable

from . import _context, params as _params, schema
from .refs import ParamRef, render
from .step import Container, Step, _env_list, _seconds, retry_policy

DAG_KEY_ORDER = (
    "name", "description", "group", "labels", "type", "schedule", "skip_if_successful",
    "catchup_window", "overlap_policy", "restart_wait_sec", "params", "consts", "env", "dotenv",
    "secrets", "working_dir", "shell", "shell_args", "container", "ssh", "tools", "preconditions",
    "timeout_sec", "delay_sec", "max_active_steps", "max_clean_up_time_sec", "max_output_size",
    "queue", "retry_policy", "defaults",
)
HANDLER_KINDS = ("init", "success", "failure", "abort", "exit", "wait")
_DAG_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")

_registry: list[DAG] = []


class _Params:
    def __init__(self, dag: DAG):
        self._dag = dag

    def __getattr__(self, name: str) -> ParamRef:
        for p in self._dag.param_defs:
            if p.name == name:
                return p.ref()
        raise AttributeError(f"DAG {self._dag.name!r} has no param {name!r}")

    __getitem__ = __getattr__


class DAG(Container):
    """A dagu DAG. Use as `with DAG("name", ...) as dag:` or through `@dag`.

    Keyword arguments are dagu's own top-level keys, checked against the
    vendored schema. Conveniences: `timeout` (seconds or timedelta ->
    timeout_sec), `retries` (-> retry_policy.limit), `env` (dict -> ordered
    list), `tags` (-> labels; dagu deprecated `tags`), `params` (dict of
    name -> default or Param), and `doc` (text for the YAML header comment).
    """

    def __init__(
        self,
        name: str,
        *,
        description: str | None = None,
        doc: str | None = None,
        params: Any = None,
        schedule: Any = None,
        labels: Any = None,
        tags: Any = None,
        env: Any = None,
        timeout: int | float | timedelta | None = None,
        retries: int | None = None,
        auto_depends: bool = True,
        source: str | None = None,
        **fields: Any,
    ):
        super().__init__()
        if not _DAG_NAME.match(name) or len(name) > 40:
            raise ValueError(f"invalid DAG name {name!r}: [a-zA-Z0-9_.-]+, max 40 characters")
        unknown = set(fields) - schema.dag_fields()
        if unknown:
            raise TypeError(f"unknown dagu DAG key(s): {', '.join(sorted(unknown))}")
        for key in ("steps", "handler_on", "name", "tags"):
            fields.pop(key, None)
        if labels is not None and tags is not None:
            raise TypeError("labels= and tags= are the same field; use labels=")
        self.name = name
        self.doc = doc
        self.auto_depends = auto_depends
        self.param_defs = _params.from_spec(params) if not _is_defs(params) else list(params)
        self.handlers: dict[str, Step] = {}
        self.locals: list[DAG] = []
        self.parent: DAG | None = None
        self.source = source or _caller_file()
        self.spec: dict[str, Any] = {}
        if description is not None:
            self.spec["description"] = description
        if labels is not None or tags is not None:
            self.spec["labels"] = labels if labels is not None else tags
        if schedule is not None:
            self.spec["schedule"] = schedule
        if env is not None:
            self.spec["env"] = _env_list(env)
        if timeout is not None:
            self.spec["timeout_sec"] = _seconds(timeout)
        if retries is not None:
            self.spec["retry_policy"] = retry_policy(retries)
        for key, value in fields.items():
            if value is not None:
                self.spec[key] = value

    # -- authoring -----------------------------------------------------------

    @property
    def params(self) -> _Params:
        return _Params(self)

    def __enter__(self) -> DAG:
        _context.push(self)
        return self

    def __exit__(self, *exc) -> None:
        _context.pop(self)
        if self.parent is None and exc[0] is None and self not in _registry:
            _registry.append(self)

    def set_handler(self, kind: str, step: Step) -> Step:
        if kind not in HANDLER_KINDS:
            raise ValueError(f"handler kind must be one of {HANDLER_KINDS}")
        if step.container is not None:
            step.container.remove(step)
        if step.upstream:
            raise ValueError("handler steps cannot have depends")
        self.handlers[kind] = step
        return step

    # -- compilation ---------------------------------------------------------

    def all_dags(self) -> list[DAG]:
        """This DAG and every local sub-DAG under it, depth first."""
        out = [self]
        for child in self.locals:
            out.extend(child.all_dags())
        return out

    def to_dict(self, *, entry: bool = True) -> dict[str, Any]:
        finalize(self.steps, auto=self.auto_depends)
        body: dict[str, Any] = {}
        if not entry:
            body["name"] = self.name
        spec = render(self.spec)
        if self.param_defs:
            spec["params"] = [p.to_yaml() for p in self.param_defs]
        for key in DAG_KEY_ORDER:
            if key in spec and key not in body:
                body[key] = spec[key]
        for key, value in spec.items():
            if key not in body:
                body[key] = value
        body["steps"] = [s.to_dict() for s in self.steps]
        if self.handlers:
            body["handler_on"] = {k: self.handlers[k].to_dict() for k in HANDLER_KINDS if k in self.handlers}
        return body

    def documents(self) -> list[dict[str, Any]]:
        dags = self.all_dags()
        names = [d.name for d in dags]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValueError(f"DAG names repeat within {self.name}.yaml: {', '.join(sorted(dupes))}")
        return [d.to_dict(entry=(d is self)) for d in dags]

    def to_yaml(self, *, root: Path | None = None) -> str:
        from .compile import to_yaml

        return to_yaml(self, root=root)

    @property
    def description(self) -> str | None:
        return self.spec.get("description")

    def __repr__(self) -> str:
        return f"DAG({self.name!r})"


def _is_defs(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, _params.ParamDef) for v in value) and bool(value)


def _caller_file() -> str | None:
    frame = inspect.currentframe()
    while frame is not None:
        filename = frame.f_code.co_filename
        if "daguflow" not in Path(filename).parts[-2:-1] and not filename.startswith("<"):
            return filename
        frame = frame.f_back
    return None


def _split_doc(doc: str | None) -> tuple[str | None, str | None]:
    if not doc:
        return None, None
    first, _, rest = doc.strip().partition("\n")
    return first.strip() or None, rest.strip() or None


def dag(fn: Callable | None = None, /, **kwargs: Any) -> Any:
    """Build a DAG from a function, Airflow TaskFlow style.

    The function's parameters become the DAG's params (see daguflow.params)
    and arrive in the body as Refs. Its docstring's first line becomes the
    `description` unless one is given; the rest becomes the YAML header
    comment. The function runs once, at decoration, and the name is bound
    to the resulting DAG.
    """

    def wrap(fn: Callable) -> DAG:
        defs = _params.from_signature(fn)
        description, rest = _split_doc(inspect.getdoc(fn))
        if "description" in kwargs:
            doc = inspect.getdoc(fn)
        else:
            kwargs["description"] = description
            doc = rest
        name = kwargs.pop("name", fn.__name__)
        d = DAG(name, params=defs or None, doc=kwargs.pop("doc", doc),
                source=inspect.getsourcefile(fn), **kwargs)
        d.param_defs = defs
        with d:
            fn(**{p.name: p.ref() for p in defs})
        return d

    return wrap(fn) if fn is not None else wrap


class _HandlerSlot(Container):
    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind
        self.dag = _context.current_dag()
        if self.dag is None:
            raise RuntimeError(f"on_{kind}() must be used inside a DAG")

    def __exit__(self, *exc) -> None:
        super().__exit__(*exc)
        if exc[0] is not None:
            return
        if len(self.steps) != 1:
            raise ValueError(f"on_{self.kind} takes exactly one step, got {len(self.steps)}")
        self.dag.set_handler(self.kind, self.steps[0])


def on_init() -> _HandlerSlot:
    return _HandlerSlot("init")


def on_success() -> _HandlerSlot:
    return _HandlerSlot("success")


def on_failure() -> _HandlerSlot:
    return _HandlerSlot("failure")


def on_abort() -> _HandlerSlot:
    return _HandlerSlot("abort")


def on_exit() -> _HandlerSlot:
    return _HandlerSlot("exit")


def on_wait() -> _HandlerSlot:
    return _HandlerSlot("wait")


# -- automatic depends ---------------------------------------------------------

_BRACED = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?")
_BARE = re.compile(r"(?<![\\$])\$([A-Za-z_][A-Za-z0-9_]*)")


def _reachable(start: Step, target: Step, by_name: dict[str, Step]) -> bool:
    seen: set[int] = set()
    todo = list(start.upstream)
    while todo:
        node = todo.pop()
        node = by_name.get(node) if isinstance(node, str) else node
        if node is None or id(node) in seen:
            continue
        if node is target:
            return True
        seen.add(id(node))
        todo.extend(node.upstream)
    return False


def finalize(steps: list[Step], *, auto: bool = True) -> None:
    """Add `depends` for every output a step reads, then check for cycles.

    dagu never infers a dependency from a reference: a step that reads
    `${FETCH}` before `fetch` has run sees the literal text. So, as in
    Airflow's TaskFlow, reading another step's output makes it upstream.
    Both Ref objects and references written as text are found. Pass
    auto_depends=False to a DAG to turn this off.
    """
    by_name = {s.name: s for s in steps if s.name}
    by_ref = {s.ref_name: s for s in steps if s.ref_name}
    if auto:
        by_var: dict[str, Step] = {}
        members = {id(s) for s in steps}
        for s in steps:
            found: list[Step] = []
            for ref in s.refs():
                if ref.producer is not None and id(ref.producer) in members and ref.producer is not s:
                    found.append(ref.producer)
            text = s.text()
            for m in _BRACED.finditer(text):
                head, nxt = m.group(1), m.group(2)
                if head == "steps" and nxt in by_ref:
                    found.append(by_ref[nxt])
                elif head in by_var:
                    found.append(by_var[head])
                elif head in by_ref and nxt in ("stdout", "stderr", "exit_code", "exitCode", "output", "outputs"):
                    found.append(by_ref[head])
            for m in _BARE.finditer(text):
                if m.group(1) in by_var:
                    found.append(by_var[m.group(1)])
            for producer in found:
                if producer is not s and not _reachable(s, producer, by_name):
                    s.set_upstream(producer)
            out = s.spec.get("output")
            if isinstance(out, str):
                by_var[out] = s
    names = [s.name for s in steps]
    dupes = sorted({n for n in names if n and names.count(n) > 1})
    if dupes:
        raise ValueError(f"step names repeat: {', '.join(dupes)}")
    for s in steps:
        for u in s.upstream:
            if isinstance(u, str) and u not in by_name and u not in by_ref:
                raise ValueError(f"step {s.name!r} depends on unknown step {u!r}")
        if _reachable(s, s, by_name):
            raise ValueError(f"dependency cycle through step {s.name!r}")
        if s.body is not None:
            finalize(s.body.steps, auto=auto)


def registered() -> list[DAG]:
    return list(_registry)


def clear_registry() -> None:
    _registry.clear()


def collect(namespace: dict[str, Any] | Any) -> list[DAG]:
    """Top-level DAGs defined in a module (or its globals dict)."""
    values = namespace.values() if isinstance(namespace, dict) else vars(namespace).values()
    return [v for v in values if isinstance(v, DAG) and v.parent is None]


__all__ = ["DAG", "dag", "on_init", "on_success", "on_failure", "on_abort", "on_exit", "on_wait"]
