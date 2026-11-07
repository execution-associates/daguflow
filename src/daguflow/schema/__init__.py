"""The dagu DAG JSON Schema daguflow targets: one dagu release's, pinned by commit and sha256.

daguflow does not ship it: the first build downloads it from dagu's repository,
checks its sha256 and caches it under
$XDG_CACHE_HOME/daguflow (default ~/.cache/daguflow). Offline, run
`daguflow schema fetch` once while online, or point DAGUFLOW_SCHEMA at a copy.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from functools import lru_cache
from pathlib import Path

DAGU_VERSION = "v2.24.0"
DAGU_COMMIT = "684692b1e307e86f7f65b6a547304ede15d5784e"
DAGU_SCHEMA_SHA256 = "8db30ca1bc0a6eb43f6e0f759a5a0039ec736c774af262d16704fc6db11b58b4"
SOURCE = f"https://raw.githubusercontent.com/dagucloud/dagu/{DAGU_COMMIT}/internal/cmn/schema/dag.schema.json"


class SchemaUnavailable(RuntimeError):
    """The pinned schema is neither cached nor downloadable, or a copy is not the pinned one."""


def cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "daguflow" / f"dag.schema-{DAGU_VERSION}-{DAGU_SCHEMA_SHA256[:12]}.json"


def _checked(data: bytes, where: str) -> bytes:
    digest = hashlib.sha256(data).hexdigest()
    if digest != DAGU_SCHEMA_SHA256:
        raise SchemaUnavailable(f"{where} is not dagu {DAGU_VERSION}'s schema "
                                f"(sha256 {digest[:12]}..., want {DAGU_SCHEMA_SHA256[:12]}...)")
    return data


def fetch(dest: Path | None = None) -> Path:
    """Download the pinned schema into the cache (or `dest`) and return where it landed."""
    dest = dest or cache_path()
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "daguflow"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = _checked(resp.read(), SOURCE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return dest


@lru_cache(maxsize=1)
def load() -> dict:
    override = os.environ.get("DAGUFLOW_SCHEMA")
    if override:
        return json.loads(_checked(Path(override).read_bytes(), override))
    path = cache_path()
    try:
        return json.loads(_checked(path.read_bytes(), str(path)))
    except (OSError, SchemaUnavailable):
        pass  # not cached yet, or a damaged copy: download it
    try:
        fetch(path)
    except OSError as e:
        raise SchemaUnavailable(
            f"dagu {DAGU_VERSION}'s schema is not cached and could not be downloaded ({e}). "
            "Run `daguflow schema fetch` while online, or set DAGUFLOW_SCHEMA to a copy.") from None
    return json.loads(path.read_bytes())


def dag_fields() -> frozenset[str]:
    return frozenset(load()["properties"])


def step_fields() -> frozenset[str]:
    return frozenset(load()["definitions"]["step"]["properties"])


def builtin_actions() -> tuple[str, ...]:
    return tuple(load()["definitions"]["actionName"]["anyOf"][0]["enum"])
