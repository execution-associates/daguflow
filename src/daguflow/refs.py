"""References: Python stand-ins for dagu's `${...}` expressions.

A Ref renders as dagu syntax wherever a string is built, most often inside an
f-string:

    f"lights.py power --action {action}"      ->  lights.py power --action ${action}
    f"lights.py effect --name {effect:q}"     ->  lights.py effect --name "${effect}"
    f"{catalog['effects']}"                   ->  ${CATALOG.effects}

THE `:q` FORM IS FOR FREE TEXT. For an SSH target dagu replaces a
double-quoted `"${x}"` with the value re-quoted as one shell word, while an
unquoted `${x}` is split on spaces by the remote shell. Never single-quote a
reference: dagu leaves `'${x}'` unexpanded and the command receives the
literal text. Measured on dagu 2.16.2 for SSH targets; local `run:` shells
treat quoted references differently from dagu 2.25.3 on, so measure before
relying on it there.

Unqualified `${name}` is the default spelling for params because it is the
form the automations DAGs have always used and the one measured for SSH
commands; `${params.name}` is available as `ParamRef.scoped`.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .step import Step

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Ref:
    """A dagu value reference. `expr` is what goes between `${` and `}`."""

    __slots__ = ("expr", "producer", "constraint")

    def __init__(self, expr: str, *, producer: Step | None = None, constraint: str | None = None):
        self.expr = expr
        # The step whose output this reads, if any: using the Ref in another
        # step adds that step to its `depends`.
        self.producer = producer
        # Set when the value can only be something safe to put in a shell
        # word (an enum, a number, a pattern). See task.python's ssh rule.
        self.constraint = constraint

    def render(self) -> str:
        return "${" + self.expr + "}"

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"Ref({self.expr!r})"

    def __format__(self, spec: str) -> str:
        if spec == "":
            return self.render()
        if spec == "q":
            return '"' + self.render() + '"'
        if spec == "bare":
            if not _IDENT.match(self.expr):
                raise ValueError(f"{self.expr!r} has no bare $NAME form")
            return "$" + self.expr
        raise ValueError(f"unknown Ref format {spec!r}: use '' or 'q' (or 'bare')")

    def __getitem__(self, key: str | int) -> Ref:
        if isinstance(key, int):
            return Ref(f"{self.expr}[{key}]", producer=self.producer)
        return Ref(f"{self.expr}.{key}", producer=self.producer)

    def __getattr__(self, name: str) -> Ref:
        if name.startswith("_"):
            raise AttributeError(name)
        return self[name]

    # Refs are build-time placeholders; comparing or hashing them by value
    # would silently do the wrong thing inside a DAG body.
    def __eq__(self, other: object) -> bool:  # pragma: no cover - guard
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __bool__(self) -> bool:
        raise TypeError(
            "a Ref has no value at build time; branch at run time with "
            "preconditions or router.route instead of a Python `if`"
        )


class ParamRef(Ref):
    """A DAG param. Renders `${name}`; `.scoped` renders `${params.name}`."""

    __slots__ = ("name",)

    def __init__(self, name: str, *, constraint: str | None = None):
        super().__init__(name, constraint=constraint)
        self.name = name

    @property
    def scoped(self) -> Ref:
        return Ref(f"params.{self.name}", constraint=self.constraint)


class _Namespace:
    """Attribute access builds dotted refs: env.HOME -> ${env.HOME}."""

    def __init__(self, prefix: str):
        self._prefix = prefix

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        expr = f"{self._prefix}.{name}" if self._prefix else name
        return _NamespaceRef(expr)

    def __getitem__(self, name: str) -> Ref:
        return getattr(self, name)


class _NamespaceRef(Ref):
    """A Ref that keeps building dotted paths: ctx.run.id -> ${context.run.id}."""

    __slots__ = ()


env = _Namespace("env")
"""Scoped env references: `env.PI_USER` renders `${env.PI_USER}`.

SSH `with:` fields expand only scoped references, so a bare `${VAR}` there
authenticates as the literal text. Measured 2026-09-13 on dagu 2.16.2."""

consts = _Namespace("consts")
ctx = _Namespace("context")
"""Run context: `ctx.run.id`, `ctx.dag.name`, `ctx.paths.work_dir`, ..."""

ITEM = Ref("ITEM")
"""The current item of a parallel sub-DAG fan-out (`${ITEM}`)."""


def var(name: str) -> Ref:
    """Any variable by its exact name: `var("HOME_PI_USER")` -> `${HOME_PI_USER}`."""
    return Ref(name)


def raw(expr: str) -> Ref:
    """An arbitrary expression, rendered as `${expr}`."""
    return Ref(expr)


def render(value: Any) -> Any:
    """Turn Refs (and Steps, Targets) inside a value into plain YAML data."""
    from .step import Step

    if isinstance(value, Ref):
        return value.render()
    if isinstance(value, Step):
        return value.output.render()
    if hasattr(value, "__dagu__"):
        return render(value.__dagu__())
    if isinstance(value, dict):
        return {k: render(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [render(v) for v in value]
    return value


def iter_refs(value: Any):
    """Every Ref object nested inside a value (not refs written as text)."""
    from .step import Step

    if isinstance(value, Ref):
        yield value
    elif isinstance(value, Step):
        yield value.output
    elif hasattr(value, "__dagu__"):
        yield from iter_refs(value.__dagu__())
    elif isinstance(value, dict):
        for v in value.values():
            yield from iter_refs(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from iter_refs(v)
