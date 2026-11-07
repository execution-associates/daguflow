"""DAG params from Python signatures.

    def set_all_brightness(value=50): ...                 ->  - value: 50
    def set_volume(value: Annotated[int, Range(0, 100)] = 20): ...
        ->  - name: value
              type: integer
              default: 20
              minimum: 0
              maximum: 100

A plain default (annotated or not) emits dagu's one-key form, exactly what a
hand-written DAG has. The rich form, which makes dagu itself refuse bad
values at start, is opt-in: a `Literal[...]` annotation, `Annotated[...,
Range | Pattern | Length | Doc]`, a `Param(...)` default, or no default at
all (a required param).

A param literally called `name` always uses the rich form: in a params list a
one-key map whose key is `name` is read as an inline definition and fails
every start ("inline parameter definition field "name" must not be empty").
"""

from __future__ import annotations

import inspect
import re
import typing
from dataclasses import dataclass, field
from typing import Any

from .refs import ParamRef

_MISSING = object()
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_PY_TO_DAGU = {int: "integer", float: "number", bool: "boolean", str: "string"}


def _admits_no_newline(pattern: str) -> bool:
    """False for a pattern that would accept a value with a line break in it.

    A probe, not a proof: Python's re stands in for dagu's Go regexp. It catches
    the usual ways a newline gets in (no anchors, `\\s`, `(?s)`, `[^...]`).
    """
    try:
        compiled = re.compile(pattern)
    except re.error:
        return False
    return not any(compiled.search(probe) for probe in
                   ("x\nDAGUFLOW_EOF\nx", "\nDAGUFLOW_EOF\n"))


@dataclass(frozen=True)
class Range:
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class Length:
    min_length: int | None = None
    max_length: int | None = None


@dataclass(frozen=True)
class Pattern:
    pattern: str


@dataclass(frozen=True)
class Doc:
    description: str


@dataclass
class Param:
    """An explicit param definition, usable as a default or in DAG(params=...)."""

    default: Any = _MISSING
    type: str | None = None
    enum: list[Any] | None = None
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    description: str | None = None
    required: bool | None = None
    eval: str | None = None


@dataclass
class ParamDef:
    name: str
    default: Any = _MISSING
    rich: bool = False
    fields: dict[str, Any] = field(default_factory=dict)

    @property
    def constraint(self) -> str | None:
        if self.fields.get("enum"):
            return "enum"
        if self.fields.get("type") in ("integer", "number", "boolean"):
            return "number"
        if self.fields.get("pattern") and _admits_no_newline(self.fields["pattern"]):
            return "pattern"
        return None

    def ref(self) -> ParamRef:
        return ParamRef(self.name, constraint=self.constraint)

    def to_yaml(self) -> dict[str, Any]:
        if not self.rich and self.name != "name":
            return {self.name: "" if self.default is _MISSING else self.default}
        out: dict[str, Any] = {"name": self.name}
        if "type" in self.fields:
            out["type"] = self.fields["type"]
        if self.default is not _MISSING:
            out["default"] = self.default
        for key in ("required", "enum", "minimum", "maximum", "min_length", "max_length",
                    "pattern", "description", "eval"):
            if self.fields.get(key) is not None:
                out[key] = self.fields[key]
        if len(out) == 1:
            out["default"] = ""
        return out


def _check_name(name: str) -> None:
    if not _NAME.match(name):
        raise ValueError(f"param {name!r} is not referenceable: names match [A-Za-z][A-Za-z0-9_]*")


def from_param(name: str, p: Param) -> ParamDef:
    _check_name(name)
    fields = {k: getattr(p, k) for k in ("type", "enum", "minimum", "maximum", "min_length",
                                          "max_length", "pattern", "description", "required", "eval")}
    if fields["type"] is None and p.default is not _MISSING and type(p.default) in _PY_TO_DAGU:
        fields["type"] = _PY_TO_DAGU[type(p.default)]
    return ParamDef(name, p.default, rich=True, fields={k: v for k, v in fields.items() if v is not None})


def from_value(name: str, value: Any) -> ParamDef:
    if isinstance(value, Param):
        return from_param(name, value)
    _check_name(name)
    return ParamDef(name, value)


def from_annotation(name: str, annotation: Any, default: Any) -> ParamDef:
    if isinstance(default, Param):
        return from_param(name, default)
    _check_name(name)
    fields: dict[str, Any] = {}
    rich = default is inspect.Parameter.empty
    base = annotation
    if typing.get_origin(annotation) is typing.Annotated:
        base, *extras = typing.get_args(annotation)
        for extra in extras:
            if isinstance(extra, Range):
                fields.update(minimum=extra.minimum, maximum=extra.maximum)
                rich = True
            elif isinstance(extra, Length):
                fields.update(min_length=extra.min_length, max_length=extra.max_length)
                rich = True
            elif isinstance(extra, Pattern):
                fields["pattern"] = extra.pattern
                rich = True
            elif isinstance(extra, Doc):
                fields["description"] = extra.description
                rich = True
    if typing.get_origin(base) is typing.Literal:
        values = list(typing.get_args(base))
        fields["enum"] = values
        kinds = {type(v) for v in values}
        if len(kinds) == 1 and kinds.pop() in _PY_TO_DAGU:
            fields["type"] = _PY_TO_DAGU[type(values[0])]
        rich = True
    elif rich and base in _PY_TO_DAGU:
        fields["type"] = _PY_TO_DAGU[base]
    if default is inspect.Parameter.empty:
        fields["required"] = True
        default = _MISSING
    return ParamDef(name, default, rich=rich, fields={k: v for k, v in fields.items() if v is not None})


def from_signature(fn: Any) -> list[ParamDef]:
    hints = typing.get_type_hints(fn, include_extras=True)
    defs = []
    for p in inspect.signature(fn).parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            raise TypeError(f"@dag functions take named params only; {fn.__name__} has *{p.name}")
        defs.append(from_annotation(p.name, hints.get(p.name, inspect.Parameter.empty), p.default))
    return defs


def from_spec(params: Any) -> list[ParamDef]:
    """DAG(params=...) accepts a dict of name -> default | Param, or a list of ParamDef/Param pairs."""
    if params is None:
        return []
    if isinstance(params, dict):
        return [from_value(k, v) for k, v in params.items()]
    out = []
    for item in params:
        if isinstance(item, ParamDef):
            out.append(item)
        elif isinstance(item, tuple) and len(item) == 2:
            out.append(from_value(*item))
        else:
            raise TypeError(f"params entries are (name, default) pairs or ParamDef, not {item!r}")
    return out
