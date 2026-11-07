"""Typed builders for dagu actions.

    from daguflow import actions
    actions.http.request(method="GET", url="https://example.com").step("fetch")

Every builtin action at the pinned dagu version has a builder (generated
from the schema; see tools/gen_actions.py). Each returns an Action, which
becomes a step through `.step(...)` or `Step(action=...)`. `custom()` covers custom actions declared in
`actions:` and remote ones (`owner/repo@v1`, `name@v1`, `source:...@v1`);
`redis()` covers the `redis.<op>` family.
"""

from __future__ import annotations

from typing import Any

from ..step import Action
from ..targets import SSHTarget
from ._generated import *  # noqa: F403
from ._generated import __all__ as _generated_all
from ._generated import ssh

ssh.Target = SSHTarget  # type: ignore[attr-defined]


def custom(name: str, **with_: Any) -> Action:
    """A custom or remote action: `custom("dagucloud/duckdb@v1", query=...)`."""
    return Action(name, with_)


def redis(op: str, **with_: Any) -> Action:
    """`redis.<op>`: `redis("get", key="k")`."""
    return Action(f"redis.{op}", with_)


__all__ = [*_generated_all, "custom", "redis", "Action", "SSHTarget"]
