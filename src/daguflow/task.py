"""@task (build time) and @task.python (run time).

@task runs the function while the DAG is being built. It returns what the
step does: a command string, an Action, or a Step it made itself.

    @task(runs_on=pi, output="RESULT")
    def set_power(action):
        return f"/usr/bin/python3 {ROOT}/lights.py power --action {action}"

@task.python ships the function's own source to wherever the step runs and
calls it there, at run time. Arguments go in as JSON, the return value comes
back as JSON on stdout (captured as the step's output), and anything the
function prints goes to stderr so it cannot corrupt that output.

    @task.python(runs_on=pi, python="/usr/bin/python3")
    def count(catalog: dict) -> int:
        return len(catalog["effects"])

The function must be self-contained: imports inside the body, no closures,
no module globals. Build fails, naming the offenders, when it is not.
"""

from __future__ import annotations

import ast
import base64
import builtins
import functools
import inspect
import json
import textwrap
from typing import Any, Callable

from . import _context
from .refs import Ref, iter_refs
from .step import Action, Step
from .targets import ContainerTarget, SSHTarget


def _rename(step: Step, base: str) -> None:
    container = step.container
    step.name = None
    step.name = container.unique_name(base) if container is not None else base


def _link_inputs(step: Step, values: Any) -> None:
    for ref in iter_refs(list(values)):
        if ref.producer is not None and ref.producer is not step:
            step.set_upstream(ref.producer)


class TaskFunction:
    """A @task-decorated function. Call it inside a DAG to add a step."""

    def __init__(self, fn: Callable, *, runs_on: Any = None, name: str | None = None, **opts: Any):
        functools.update_wrapper(self, fn)
        self.fn = fn
        self.runs_on = runs_on
        self.task_name = name or fn.__name__
        self.opts = opts

    def override(self, **opts: Any) -> TaskFunction:
        """A copy with different options for one call: `t.override(name="b")(x)`."""
        merged = {"runs_on": self.runs_on, "name": self.task_name, **self.opts, **opts}
        return TaskFunction(self.fn, **merged)

    def __call__(self, *args: Any, **kwargs: Any) -> Step:
        container = _context.current()
        if container is None:
            raise RuntimeError(f"@task {self.task_name!r} was called outside a DAG")
        before = list(container.steps)
        result = self.fn(*args, **kwargs)
        created = [s for s in container.steps if all(s is not b for b in before)]
        if isinstance(result, Step):
            step = result
            _rename(step, self.task_name)
            step.configure(**self.opts)
        elif created:
            raise TypeError(
                f"@task {self.task_name!r} created steps but returned {type(result).__name__}; "
                "return the step (or use a SubDAG for several)"
            )
        else:
            step = self._make(result)
        _link_inputs(step, [*args, *kwargs.values()])
        return step

    def _make(self, result: Any) -> Step:
        name = _context.current().unique_name(self.task_name)
        if isinstance(result, Action):
            return Step(name, action=result, **self.opts)
        if isinstance(result, (str, list)):
            if isinstance(self.runs_on, SSHTarget):
                return self.runs_on.run(result, name, **self.opts)
            if isinstance(self.runs_on, ContainerTarget):
                return Step(name, run=result, container=self.runs_on, **self.opts)
            return Step(name, run=result, **self.opts)
        raise TypeError(
            f"@task {self.task_name!r} returned {type(result).__name__}; "
            "return a command string, an Action or a Step"
        )


# -- @task.python ---------------------------------------------------------------

_RUNNER = '''
def _daguflow_main():
    import contextlib, json, os, sys
    args = json.loads({constants!r})
    for name, (as_text, fd) in {ref_args!r}.items():
        if fd is None:
            raw = os.environ.get("DAGUFLOW_ARG_" + name, "")
        else:
            with os.fdopen(fd) as stream:
                raw = stream.read()
            raw = raw[:-1] if raw.endswith("\\n") else raw
        if as_text:
            args[name] = raw
        else:
            try:
                args[name] = json.loads(raw)
            except ValueError:
                args[name] = raw
    with contextlib.redirect_stdout(sys.stderr):
        result = {fn}(**args)
    json.dump(result, sys.stdout)
    sys.stdout.write("\\n")


_daguflow_main()
'''


class _Scope(ast.NodeVisitor):
    def __init__(self) -> None:
        self.loaded: set[str] = set()
        self.bound: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        (self.loaded if isinstance(node.ctx, ast.Load) else self.bound).add(node.id)

    def visit_arg(self, node: ast.arg) -> None:
        self.bound.add(node.arg)

    def visit_alias(self, node: ast.alias) -> None:
        self.bound.add((node.asname or node.name).split(".")[0])

    def _bind_def(self, node: Any) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _bind_def

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.bound.add(node.name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self.loaded.update(node.names)


def function_source(fn: Callable) -> str:
    """The function's own text, without decorators, checked to be self-contained."""
    if fn.__code__.co_freevars:
        raise TypeError(f"{fn.__name__} closes over {', '.join(fn.__code__.co_freevars)}; "
                        "@task.python functions must be self-contained")
    try:
        lines, _ = inspect.getsourcelines(fn)
    except (OSError, TypeError):
        raise TypeError(f"@task.python needs {fn.__name__}'s source; define it in a .py file, "
                        "not in a REPL or `python -c`") from None
    text = textwrap.dedent("".join(lines))
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    if isinstance(node, ast.AsyncFunctionDef):
        raise TypeError(f"{fn.__name__} is async; @task.python takes plain functions")
    body = "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno]) + "\n"
    scope = _Scope()
    scope.visit(ast.parse(body))
    free = scope.loaded - scope.bound - set(dir(builtins))
    if free:
        raise TypeError(
            f"{fn.__name__} uses names from outside itself: {', '.join(sorted(free))}. "
            "@task.python ships only the function's source: import inside the body "
            "and pass values as arguments"
        )
    return body


class PythonTask:
    """A @task.python-decorated function: its body runs at run time."""

    def __init__(
        self,
        fn: Callable,
        *,
        runs_on: Any = None,
        python: str = "python3",
        deps: list[str] | None = None,
        name: str | None = None,
        unsafe_args: bool = False,
        decoder: str = "base64 -d",
        **opts: Any,
    ):
        functools.update_wrapper(self, fn)
        self.fn = fn
        self.runs_on = runs_on
        self.python = python
        self.deps = list(deps or [])
        self.task_name = name or fn.__name__
        self.unsafe_args = unsafe_args
        self.decoder = decoder
        self.opts = opts
        self.source = function_source(fn)
        self.signature = inspect.signature(fn)

    def override(self, **opts: Any) -> PythonTask:
        merged = {"runs_on": self.runs_on, "python": self.python, "deps": self.deps,
                  "name": self.task_name, "unsafe_args": self.unsafe_args,
                  "decoder": self.decoder, **self.opts, **opts}
        return PythonTask(self.fn, **merged)

    def script(self, constants: dict[str, Any], ref_args: dict[str, tuple[bool, int | None]]) -> str:
        try:
            encoded = json.dumps(constants, sort_keys=True)
        except TypeError as e:
            raise TypeError(f"@task.python {self.task_name!r}: build-time arguments must be JSON: {e}") from None
        return self.source + _RUNNER.format(constants=encoded, ref_args=ref_args, fn=self.fn.__name__)

    def _launcher(self, inline: bool = False) -> str:
        """The interpreter command. inline=True takes the program from -c
        (stdin stays free for the argument heredocs) and leaves {payload}
        and {decoder} to fill in."""
        prefix = ""
        if self.deps:
            withs = " ".join(f"--with {d}" for d in self.deps)
            prefix = f"uv run --quiet --no-project {withs} -- "
        if inline:
            return prefix + self.python + ' -c "$(echo {payload} | {decoder})"'
        return f"{prefix}{self.python} -"

    def __call__(self, *args: Any, **kwargs: Any) -> Step:
        container = _context.current()
        if container is None:
            raise RuntimeError(f"@task.python {self.task_name!r} was called outside a DAG")
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        constants: dict[str, Any] = {}
        refs: dict[str, Ref] = {}
        for pname, value in bound.arguments.items():
            if isinstance(value, Step):
                value = value.output
            if isinstance(value, Ref):
                refs[pname] = value
            elif any(True for _ in iter_refs(value)):
                raise TypeError(f"@task.python {self.task_name!r}: pass Refs as whole arguments, "
                                f"not inside {pname}'s value")
            else:
                constants[pname] = value
        as_text = {p: self.signature.parameters[p].annotation in (str, "str") for p in refs}
        name = container.unique_name(self.task_name)

        if isinstance(self.runs_on, SSHTarget):
            # The remote side never sees step env. Each value rides in on its
            # own file descriptor as a quoted heredoc: quotes, `$` and JSON
            # arrive byte for byte. A value containing the line DAGUFLOW_EOF
            # ends its heredoc early and the rest runs as shell, so only values
            # dagu has already constrained may go in. Step outputs never are.
            loose = [p for p, r in refs.items() if r.constraint is None]
            if loose and not self.unsafe_args:
                raise TypeError(
                    f"@task.python {self.task_name!r} runs over ssh and takes unconstrained "
                    f"value(s) {', '.join(loose)}. Pass params with an enum, a numeric type or "
                    "a pattern that admits no newline, or pass unsafe_args=True if every "
                    "source of these values is trusted"
                )
            fds = {p: 3 + i for i, p in enumerate(refs)}
            payload = base64.b64encode(
                self.script(constants, {p: (as_text[p], fds[p]) for p in refs}).encode()).decode()
            redirects = "".join(f" {fd}<<'DAGUFLOW_EOF'" for fd in fds.values())
            bodies = "".join(f"\n{r}\nDAGUFLOW_EOF" for r in refs.values())
            command = f'{self._launcher(inline=True).format(payload=payload, decoder=self.decoder)}{redirects}{bodies}'
            step = self.runs_on.run(command, name, **self.opts)
        else:
            payload = base64.b64encode(
                self.script(constants, {p: (as_text[p], None) for p in refs}).encode()).decode()
            env = {f"DAGUFLOW_ARG_{p}": r for p, r in refs.items()}
            command = f"echo {payload} | {self.decoder} | {self._launcher()}"
            extra = {"container": self.runs_on} if isinstance(self.runs_on, ContainerTarget) else {}
            opts = dict(self.opts)
            if env:
                opts["env"] = {**env, **(opts.get("env") or {})}
            step = Step(name, run=command, **extra, **opts)
        step.output  # noqa: B018 - give it an output var so the return value is captured
        _link_inputs(step, list(refs.values()))
        return step


class _TaskDecorator:
    """`task` itself: `@task`, `@task(...)`, and `@task.python(...)`."""

    def __call__(self, fn: Callable | None = None, /, **opts: Any) -> Any:
        if fn is not None:
            return TaskFunction(fn, **opts)
        return lambda f: TaskFunction(f, **opts)

    def python(self, fn: Callable | None = None, /, **opts: Any) -> Any:
        if fn is not None:
            return PythonTask(fn, **opts)
        return lambda f: PythonTask(f, **opts)


task = _TaskDecorator()
