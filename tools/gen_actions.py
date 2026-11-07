#!/usr/bin/env python3
"""Write src/daguflow/actions/_generated.py from the pinned dagu dag.schema.json.

    python tools/gen_actions.py > src/daguflow/actions/_generated.py

One keyword-only builder per builtin action, grouped by the name's first
segment: `http.request` -> `http.request(...)`, `git.worktree.add` ->
`git.worktree_add(...)`, `exec` -> `exec_(...)`. Each returns an Action.
The schema says which `with:` definition each action takes (the step's
`if action == X then with: $ref` rules); its properties become arguments,
its `required` list the arguments without defaults. Where the schema leaves
`with` open (additionalProperties, or no definition), the builder also takes
**extra. tests/test_actions.py fails when this output and the committed file
differ.
"""

from __future__ import annotations

import importlib.util
import json
import keyword
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The schema module alone (stdlib only), so this runs without daguflow's dependencies.
_spec = importlib.util.spec_from_file_location("daguflow_schema", ROOT / "src/daguflow/schema/__init__.py")
schema = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(schema)

SCHEMA = schema.load()
DEFS = SCHEMA["definitions"]
VERSION = schema.DAGU_VERSION

# Actions whose `with` the schema types loosely (ssh.run's is just
# {command} plus anything) but whose real keys live in another definition.
AUGMENT = {"ssh.run": ["sshExecutorConfig"]}


def action_configs() -> dict[str, tuple[dict | None, bool]]:
    out: dict[str, tuple[dict | None, bool]] = {}
    for rule in DEFS["step"]["allOf"]:
        cond = rule.get("if", {}).get("properties", {}).get("action", {})
        names = [cond["const"]] if "const" in cond else cond.get("enum", [])
        if not names:
            continue
        then = rule.get("then", {})
        with_schema = then.get("properties", {}).get("with")
        required = "with" in then.get("required", [])
        for name in names:
            out[name] = (with_schema, required)
    return out


def resolve(node: dict | None, depth: int = 0) -> dict:
    if not node:
        return {}
    if "$ref" in node and depth < 8:
        return resolve(DEFS[node["$ref"].split("/")[-1]], depth + 1)
    return node


def merged_properties(node: dict) -> tuple[dict, list[str], bool]:
    """Properties, required names and openness, folding allOf parts in."""
    node = resolve(node)
    props: dict = dict(node.get("properties", {}))
    required = list(node.get("required", []))
    open_ = node.get("additionalProperties", True) is not False or not props
    for part in node.get("allOf", []):
        p, r, o = merged_properties(part)
        for k, v in p.items():
            props.setdefault(k, v)
        required.extend(x for x in r if x not in required)
        open_ = open_ and o
    return props, required, open_


def pytype(node: dict, depth: int = 0) -> str:
    node = resolve(node, depth)
    if depth > 6:
        return "Any"
    if "enum" in node and all(isinstance(v, str) for v in node["enum"]) and len(node["enum"]) <= 12:
        return "Literal[" + ", ".join(json.dumps(v) for v in node["enum"]) + "]"
    if "const" in node and isinstance(node["const"], str):
        return f"Literal[{json.dumps(node['const'])}]"
    kinds = node.get("type")
    if isinstance(kinds, list):
        return " | ".join(dict.fromkeys(pytype({"type": k}, depth + 1) for k in kinds))
    simple = {"string": "str", "integer": "int", "number": "float", "boolean": "bool",
              "array": "list[Any]", "object": "dict[str, Any]", "null": "None"}
    if kinds in simple:
        return simple[kinds]
    for union in ("oneOf", "anyOf"):
        if union in node:
            parts = dict.fromkeys(pytype(p, depth + 1) for p in node[union])
            return " | ".join(parts) if "Any" not in parts else "Any"
    return "Any"


def py_name(key: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]", "_", key)
    if keyword.iskeyword(name) or name in ("extra",):
        name += "_"
    return name


def builder(action: str, with_schema: dict | None, required_with: bool) -> tuple[str, str, str]:
    namespace, _, rest = action.partition(".")
    fn = py_name(rest.replace(".", "_")) if rest else py_name(action)
    if not rest and fn == action and action in ("exec",):
        fn = action + "_"
    props: dict = {}
    required: list[str] = []
    open_ = True
    for extra_def in AUGMENT.get(action, []):
        p, _, _ = merged_properties({"$ref": f"#/definitions/{extra_def}"})
        props.update(p)
    if with_schema:
        p, r, o = merged_properties(with_schema)
        for k, v in p.items():
            props.setdefault(k, v)
        required = r
        open_ = o
    lines = []
    params = []
    for key, node in props.items():
        name = py_name(key)
        annotation = pytype(node)
        if key in required:
            params.append(f"{name}: Val[{annotation}]")
        else:
            params.append(f"{name}: Val[{annotation}] | None = None")
    if open_:
        params.append("**extra: Any")
    if params and params != ["**extra: Any"]:
        signature = ", ".join(["*", *params])
    else:
        signature = ", ".join(params)
    # Names and types only: dagu's descriptions are GPL text, and this file ships under MIT.
    required_names = [py_name(k) for k in props if k in required]
    summary = f"The `{action}` action" + (f"; requires {', '.join(required_names)}." if required_names else ".")
    if rest:
        lines.append("    @staticmethod")
    indent = "    " if rest else ""
    lines.append(f"{indent}def {fn}({signature}) -> Action:")
    lines.append(f'{indent}    """{summary}"""')
    entries = ", ".join(f'"{k}": {py_name(k)}' for k in props)
    body = "{" + entries + "}"
    if open_:
        body = body + " | extra" if props else "dict(extra)"
    lines.append(f'{indent}    return Action("{action}", {body})')
    return namespace if rest else "", fn, "\n".join(lines)


def main() -> None:
    configs = action_configs()
    actions = SCHEMA["definitions"]["actionName"]["anyOf"][0]["enum"]
    groups: dict[str, list[str]] = {}
    top: list[str] = []
    names: dict[str, list[str]] = {}
    for action in actions:
        with_schema, required_with = configs.get(action, (None, False))
        namespace, fn, code = builder(action, with_schema, required_with)
        if namespace:
            groups.setdefault(namespace, []).append(code)
            names.setdefault(namespace, []).append(fn)
        else:
            top.append(code)
            names.setdefault("", []).append(fn)
    out = [
        f'"""Builders for every builtin dagu action, generated from dagu {VERSION}\'s dag.schema.json.',
        "",
        "Do not edit: run `python tools/gen_actions.py > src/daguflow/actions/_generated.py`.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal",
        "",
        "from .._types import Val",
        "from ..step import Action",
        "",
    ]
    for code in top:
        out += ["", code, ""]
    for namespace, codes in groups.items():
        cls = py_name(namespace)
        out += ["", f"class {cls}:", f'    """`{namespace}.*` actions."""', ""]
        for code in codes:
            out += [code, ""]
    exported = sorted([py_name(g) for g in groups] + names.get("", []))
    out += ["", "__all__ = [" + ", ".join(json.dumps(n) for n in exported) + "]", ""]
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n\n", text)
    text = re.sub(r"(class [^\n]+:\n    \"\"\"[^\n]+\"\"\"\n)\n+", r"\1\n", text)
    sys.stdout.write(text.rstrip() + "\n")


if __name__ == "__main__":
    main()
