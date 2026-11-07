"""The stack of open DAG / sub-DAG / foreach / handler blocks.

A Step created while a block is open joins the innermost one, the way an
Airflow operator joins the `with DAG(...)` it is created in.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .step import Container

_local = threading.local()


def _stack() -> list[Container]:
    if not hasattr(_local, "stack"):
        _local.stack = []
    return _local.stack


def push(container: Container) -> None:
    _stack().append(container)


def pop(container: Container) -> None:
    stack = _stack()
    if not stack or stack[-1] is not container:
        raise RuntimeError("daguflow blocks closed out of order")
    stack.pop()


def current() -> Container | None:
    stack = _stack()
    return stack[-1] if stack else None


def current_dag():
    from .dag import DAG

    for container in reversed(_stack()):
        if isinstance(container, DAG):
            return container
    return None
