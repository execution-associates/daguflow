"""Schedule helpers. A plain cron string works everywhere these do."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Cron:
    """A 5-field cron expression, optionally pinned to a timezone.

    `Cron("0 23 * * *", tz="America/Los_Angeles")` renders
    `CRON_TZ=America/Los_Angeles 0 23 * * *`, which makes the schedule
    independent of the scheduler host's timezone.
    """

    expression: str
    tz: str | None = None
    profile: str | None = None

    def __dagu__(self) -> Any:
        text = f"CRON_TZ={self.tz} {self.expression}" if self.tz else self.expression
        if self.profile:
            return {"kind": "cron", "expression": text, "profile": self.profile}
        return text


@dataclass(frozen=True)
class At:
    """A one-off run at an exact time (RFC 3339 with offset, whole minutes)."""

    when: datetime | str
    profile: str | None = None

    def __dagu__(self) -> Any:
        when = self.when
        if isinstance(when, datetime):
            if when.tzinfo is None:
                raise ValueError("At() needs a timezone-aware datetime")
            when = when.replace(second=0, microsecond=0).isoformat()
        out: dict[str, Any] = {"kind": "at", "at": when}
        if self.profile:
            out["profile"] = self.profile
        return out


@dataclass(frozen=True)
class StartStop:
    """`schedule: {start, stop, restart}`; stop and restart take cron only."""

    start: Any = None
    stop: Any = None
    restart: Any = None

    def __dagu__(self) -> Any:
        return {k: v for k, v in (("start", self.start), ("stop", self.stop),
                                   ("restart", self.restart)) if v is not None}
