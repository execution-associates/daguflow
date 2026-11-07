"""Typing helpers shared by the generated builders."""

from __future__ import annotations

from typing import TypeVar, Union

from .refs import Ref

T = TypeVar("T")

# A value or a Ref that dagu fills in at run time.
Val = Union[T, Ref]
