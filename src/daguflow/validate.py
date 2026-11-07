"""Three checks for generated YAML, from cheapest to most faithful.

1. check_documents: the pinned JSON Schema plus the document rules
   `dagu validate` adds (entrypoint has no `name`, later documents have
   unique names, `steps` is a non-empty list). Runs on every build.
2. with_binary: `dagu validate <file>` from the pinned dagu release.
3. with_server: POST /api/v1/dags/validate on a running dagu.

dagu's own loader never reads the JSON Schema (it decodes strictly into Go
structs), so 1 can pass what 2 rejects; tests run 2 against every golden file.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

from . import schema


class ValidationError(ValueError):
    pass


@lru_cache(maxsize=1)
def _validator() -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(schema.load())


def _where(error: jsonschema.ValidationError) -> str:
    return "/".join(str(p) for p in error.absolute_path) or "(document)"


def _best(error: jsonschema.ValidationError) -> jsonschema.ValidationError:
    # oneOf/anyOf failures bury the useful message in their context.
    return jsonschema.exceptions.best_match([error]) if error.context else error


def schema_errors(document: dict[str, Any]) -> list[str]:
    errors = sorted(_validator().iter_errors(document), key=lambda e: list(e.absolute_path))
    return [f"{_where(_best(e))}: {_best(e).message}" for e in errors]


def document_errors(documents: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not documents:
        return ["no documents"]
    if "name" in documents[0]:
        errors.append("document 1: the entrypoint must not set name (the filename is its name)")
    seen: set[str] = set()
    for i, doc in enumerate(documents, start=1):
        steps = doc.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"document {i}: steps must be a non-empty list")
        if i > 1:
            name = doc.get("name")
            if not name:
                errors.append(f"document {i}: a local DAG needs a name")
            elif name in seen:
                errors.append(f"document {i}: name {name!r} repeats")
            else:
                seen.add(name)
    return errors


def check_documents(documents: list[dict[str, Any]], *, label: str = "DAG") -> None:
    problems = document_errors(documents)
    for i, doc in enumerate(documents, start=1):
        problems.extend(f"document {i}: {e}" for e in schema_errors(doc))
    if problems:
        raise ValidationError(f"{label} is not valid for dagu {schema.DAGU_VERSION}:\n  " + "\n  ".join(problems))


def with_binary(path: str | Path, dagu_bin: str = "dagu") -> list[str]:
    """`dagu validate`: [] when valid, else its error lines.

    Runs with a throwaway DAGU_HOME: on first use dagu otherwise writes its
    example DAGs and a config under ~/.config/dagu.
    """
    with tempfile.TemporaryDirectory(prefix="daguflow-validate-") as home:
        env = {**os.environ, "DAGU_HOME": home}
        proc = subprocess.run([dagu_bin, "validate", str(path)], capture_output=True, text=True, env=env)
    if proc.returncode == 0:
        return []
    lines = [line for line in (proc.stderr + proc.stdout).splitlines()
             if line.strip() and "level=" not in line]
    return lines or [f"dagu validate exited {proc.returncode}"]


def with_server(spec: str, client: Any, name: str | None = None) -> list[str]:
    """POST /dags/validate on a running server: [] when valid, else its errors."""
    result = client.validate(spec, name=name)
    return [] if result.get("valid") else list(result.get("errors") or ["invalid"])
