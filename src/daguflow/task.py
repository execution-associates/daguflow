"""@task (Python at run time) and @task.bash (a shell command, written at build time).

@task ships the function's own source to wherever the step runs and calls it
there. Arguments go in as JSON, the return value comes back as JSON on stdout
(the step's output), and anything the function prints goes to stderr so it
cannot corrupt that output.

    @task(runs_on=pi, python="/usr/bin/python3")
    def cpu_temp() -> float:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000

The function must be self-contained: imports inside the body, no closures, no
module globals. Build fails, naming the offenders, when it is not. Python must
exist where the step runs.

@task.bash is for a step whose job really is a shell command. The function runs
while the DAG is built and returns the command:

    @task.bash(runs_on=pi)
    def reboot() -> str:
        return "sudo systemctl reboot"
"""

from __future__ import annotations

import ast
import base64
import builtins
import functools
import inspect
import itertools
import json
import textwrap
from typing import Any, Callable

from . import _context
from .groups import _ITEM, Mapped
from .refs import Gathered, Ref, iter_refs
from .step import Step
from .targets import ContainerTarget, SSHTarget


def _link_inputs(step: Step, values: Any) -> None:
    for ref in iter_refs(list(values)):
        if ref.producer is not None and ref.producer is not step:
            step.set_upstream(ref.producer)


class BashTask:
    """A @task.bash function: it runs at build time and returns the step's shell command."""

    def __init__(self, fn: Callable, *, runs_on: Any = None, name: str | None = None, **opts: Any):
        functools.update_wrapper(self, fn)
        self.fn = fn
        self.runs_on = runs_on
        self.task_name = name or fn.__name__
        self.opts = opts

    def override(self, **opts: Any) -> BashTask:
        """A copy with different options for one call: `t.override(name="b")(x)`."""
        merged = {"runs_on": self.runs_on, "name": self.task_name, **self.opts, **opts}
        return BashTask(self.fn, **merged)

    def __call__(self, *args: Any, **kwargs: Any) -> Step:
        container = _context.current()
        if container is None:
            raise RuntimeError(f"@task.bash {self.task_name!r} was called outside a DAG")
        result = self.fn(*args, **kwargs)
        if not isinstance(result, (str, list)):
            raise TypeError(f"@task.bash {self.task_name!r} returned {type(result).__name__}; "
                            "return a command string (or an argv list). Logic belongs in @task")
        name = container.unique_name(self.task_name)
        if isinstance(self.runs_on, SSHTarget):
            step = self.runs_on.run(result, name, **self.opts)
        elif isinstance(self.runs_on, ContainerTarget):
            step = Step(name, run=result, container=self.runs_on, **self.opts)
        else:
            step = Step(name, run=result, **self.opts)
        _link_inputs(step, [*args, *kwargs.values()])
        return step


# -- @task ----------------------------------------------------------------------

_RUNNER = '''
_daguflow_fn = {fn}


def _daguflow_main():
    import contextlib, json, os, sys
    args = json.loads({constants!r})
    for name, (as_text, fd, gather, spread) in {ref_args!r}.items():
        if fd is None:
            raw = os.environ.get("DAGUFLOW_ARG_" + name, "")
        else:
            with os.fdopen(fd) as stream:
                raw = stream.read()
            raw = raw[:-1] if raw.endswith("\\n") else raw
        if spread:
            args.update(json.loads(raw))
        elif gather is not None:
            try:
                outputs = json.loads(raw).get("outputs") or []
            except (ValueError, AttributeError):
                outputs = []
            args[name] = []
            for out in outputs:
                value = out.get(gather, next(iter(out.values())) if len(out) == 1 else None)
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        pass
                args[name].append(value)
        elif as_text:
            args[name] = raw
        else:
            try:
                args[name] = json.loads(raw)
            except ValueError:
                args[name] = raw
    with contextlib.redirect_stdout(sys.stderr):
        result = _daguflow_fn(**args)
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
                        "@task functions must be self-contained")
    try:
        lines, _ = inspect.getsourcelines(fn)
    except (OSError, TypeError):
        raise TypeError(f"@task needs {fn.__name__}'s source; define it in a .py file, "
                        "not in a REPL or `python -c`") from None
    text = textwrap.dedent("".join(lines))
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    if isinstance(node, ast.AsyncFunctionDef):
        raise TypeError(f"{fn.__name__} is async; @task takes plain functions")
    body = "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno]) + "\n"
    scope = _Scope()
    scope.visit(ast.parse(body))
    free = scope.loaded - scope.bound - set(dir(builtins))
    if free:
        raise TypeError(
            f"{fn.__name__} uses names from outside itself: {', '.join(sorted(free))}. "
            "@task ships only the function's source: import inside the body "
            "and pass values as arguments"
        )
    return body


class PythonTask:
    """A @task function: its body runs at run time, where the step runs."""

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

    def partial(self, **fixed: Any) -> PartialTask:
        """Fix the arguments every mapped call shares: `t.partial(api=URL).expand(id=ids)`."""
        return PartialTask(self, fixed)

    def expand(self, *, max_concurrent: int | None = None, **mapped: Any) -> Step:
        """One run per item, in parallel. See PartialTask.expand."""
        return PartialTask(self, {}).expand(max_concurrent=max_concurrent, **mapped)

    def expand_kwargs(self, items: Any, *, max_concurrent: int | None = None) -> Step:
        """One run per dict of arguments. See PartialTask.expand_kwargs."""
        return PartialTask(self, {}).expand_kwargs(items, max_concurrent=max_concurrent)

    def override(self, **opts: Any) -> PythonTask:
        merged = {"runs_on": self.runs_on, "python": self.python, "deps": self.deps,
                  "name": self.task_name, "unsafe_args": self.unsafe_args,
                  "decoder": self.decoder, **self.opts, **opts}
        return PythonTask(self.fn, **merged)

    def script(self, constants: dict[str, Any], ref_args: dict[str, tuple[bool, int | None, str | None, bool]]) -> str:
        try:
            encoded = json.dumps(constants, sort_keys=True)
        except TypeError as e:
            raise TypeError(f"@task {self.task_name!r}: build-time arguments must be JSON: {e}") from None
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
        return self._call(args, kwargs, spread=None)

    def _call(self, args: tuple, kwargs: dict, spread: Ref | None) -> Step:
        """spread: a Ref to a JSON object whose keys become keyword arguments at run time."""
        container = _context.current()
        if container is None:
            raise RuntimeError(f"@task {self.task_name!r} was called outside a DAG")
        if spread is None:
            bound = self.signature.bind(*args, **kwargs)
            bound.apply_defaults()
        else:
            bound = self.signature.bind_partial(*args, **kwargs)  # the rest arrive at run time
        constants: dict[str, Any] = {}
        refs: dict[str, Ref] = {}
        for pname, value in bound.arguments.items():
            if isinstance(value, Step):
                value = value._task_input()
            if isinstance(value, Ref):
                refs[pname] = value
            elif any(True for _ in iter_refs(value)):
                raise TypeError(f"@task {self.task_name!r}: pass Refs as whole arguments, "
                                f"not inside {pname}'s value")
            else:
                constants[pname] = value
        if spread is not None:
            refs[_SPREAD] = spread
        as_text = {p: p in self.signature.parameters and self.signature.parameters[p].annotation in (str, "str")
                   for p in refs}
        gather = {p: r.key if isinstance(r, Gathered) else None for p, r in refs.items()}
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
                    f"@task {self.task_name!r} runs over ssh and takes unconstrained "
                    f"value(s) {', '.join(loose)}. Pass params with an enum, a numeric type or "
                    "a pattern that admits no newline, or pass unsafe_args=True if every "
                    "source of these values is trusted"
                )
            fds = {p: 3 + i for i, p in enumerate(refs)}
            payload = base64.b64encode(
                self.script(constants, {p: (as_text[p], fds[p], gather[p], p == _SPREAD) for p in refs}).encode()).decode()
            redirects = "".join(f" {fd}<<'DAGUFLOW_EOF'" for fd in fds.values())
            bodies = "".join(f"\n{r}\nDAGUFLOW_EOF" for r in refs.values())
            command = f'{self._launcher(inline=True).format(payload=payload, decoder=self.decoder)}{redirects}{bodies}'
            step = self.runs_on.run(command, name, **self.opts)
        else:
            payload = base64.b64encode(
                self.script(constants, {p: (as_text[p], None, gather[p], p == _SPREAD) for p in refs}).encode()).decode()
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


def _child_dag_name(base: str) -> str:
    """A name no other document in the file has: every local DAG becomes one."""
    dag = _context.current_dag()
    while dag.parent is not None:
        dag = dag.parent
    taken = {d.name for d in dag.all_dags()} | {s.name for s in _context.current().steps if s.name}
    if base not in taken:
        return base
    n = 1
    while f"{base}__{n}" in taken:
        n += 1
    return f"{base}__{n}"


def _mapped_list(value: Any, arg: str) -> Any:
    if isinstance(value, Step):
        value = value._task_input()
    if isinstance(value, Gathered):
        raise TypeError(f"expand({arg}=...): a mapped task's results are not a list dagu can fan out over; "
                        "pass them through a @task that returns the list")
    if isinstance(value, Ref):
        return value
    if isinstance(value, (list, tuple)):
        if any(True for _ in iter_refs(list(value))):
            raise TypeError(f"expand({arg}=...): a literal list cannot hold step outputs; build it in a @task")
        return list(value)
    raise TypeError(f"expand({arg}=...) takes a list or a step's output, not {type(value).__name__}")


# The child param a mapped run's keyword-argument dict arrives in.
_SPREAD = "mapped_kwargs"


class PartialTask:
    """A @task with some arguments fixed, ready to map over the rest."""

    def __init__(self, task: PythonTask, fixed: dict[str, Any]):
        self.task = task
        self.fixed = fixed

    def expand(self, *, max_concurrent: int | None = None, **mapped: Any) -> Step:
        """One run of the task per item, at most max_concurrent at once (dagu's default is 10).

        One mapped argument takes a list or a step's output. Several take literal
        lists and run every combination, as in Airflow. Passed to another @task,
        the result is the list of each run's return value, in item order.
        dagu runs identical items once.
        """
        if not mapped:
            raise TypeError(f"expand() on {self.task.task_name!r} needs at least one mapped argument")
        if len(mapped) == 1:
            (arg, value), = mapped.items()
            return self._fan_out(_mapped_list(value, arg), {arg: _ITEM}, max_concurrent)
        lists = {arg: _mapped_list(value, arg) for arg, value in mapped.items()}
        if any(isinstance(v, Ref) for v in lists.values()):
            raise TypeError("expand() over several arguments needs literal lists; for run-time values, "
                            "return the argument dicts from a @task and use expand_kwargs()")
        combos = [dict(zip(lists, values)) for values in itertools.product(*lists.values())]
        return self._fan_out(combos, {}, max_concurrent, spread=list(lists))

    def expand_kwargs(self, items: Any, *, max_concurrent: int | None = None) -> Step:
        """One run per dict of keyword arguments: a literal list of dicts, or a step that outputs one.

        A key a dict leaves out takes the function's default, so dicts may differ.
        """
        items = _mapped_list(items, "kwargs")
        keys: list[str] = []
        if not isinstance(items, Ref):
            if not items or not all(isinstance(i, dict) for i in items):
                raise TypeError("expand_kwargs() takes a non-empty list of dicts")
            keys = list(dict.fromkeys(k for i in items for k in i))
            unknown = [k for k in keys if k not in self.task.signature.parameters]
            if unknown:
                raise TypeError(f"@task {self.task.task_name!r} has no argument(s) {', '.join(unknown)}")
            for i, item in enumerate(items):
                try:
                    self.task.signature.bind(**{n: None for n in [*self.fixed, *item]})
                except TypeError as e:
                    raise TypeError(f"expand_kwargs() item {i}: {e}") from None
        return self._fan_out(items, {}, max_concurrent, spread=keys)

    def _fan_out(self, items: Any, per_item: dict[str, Ref], max_concurrent: int | None,
                 spread: list[str] | None = None) -> Step:
        """spread: each item is a dict of keyword arguments (these keys, when known at build time)."""
        task = self.task
        if _context.current_dag() is None:
            raise RuntimeError(f"@task {task.task_name!r} was expanded outside a DAG")
        params = task.signature.parameters
        mapped_names = [*per_item, *(spread or [])]
        names = [*self.fixed, *mapped_names]
        unknown = [n for n in names if n not in params]
        if unknown:
            raise TypeError(f"@task {task.task_name!r} has no argument(s) {', '.join(unknown)}")
        both = set(self.fixed) & set(mapped_names)
        if both:
            raise TypeError(f"@task {task.task_name!r}: {', '.join(sorted(both))} is both fixed and mapped")
        if spread is None:  # names a missing required argument; dicts are checked above or at run time
            task.signature.bind(**{n: None for n in names})
        if _SPREAD in params:
            raise TypeError(f"@task {task.task_name!r}: {_SPREAD!r} is reserved for mapped keyword arguments")
        passed: dict[str, Any] = dict(per_item)
        if spread is not None:
            passed[_SPREAD] = _ITEM
        constants: dict[str, Any] = {}
        for name, value in self.fixed.items():
            if isinstance(value, Step):
                value = value._task_input()
            if isinstance(value, Ref):
                passed[name] = value  # child runs see only what they are passed
            elif any(True for _ in iter_refs(value)):
                raise TypeError(f"partial({name}=...): pass Refs as whole arguments")
            else:
                constants[name] = value
        if isinstance(items, list) and any(isinstance(i, (dict, list)) for i in items):
            # dagu turns every value of a literal map item into a string; a JSON list keeps the types.
            items = json.dumps(items)
        mapped = Mapped(_child_dag_name(task.task_name), params=passed, items=items,
                        max_concurrent=max_concurrent)
        with mapped:
            child_args = {n: mapped.params[n] for n in passed if n != _SPREAD}
            task._call((), {**constants, **child_args},
                       spread=mapped.params[_SPREAD] if spread is not None else None)
        return mapped


class _TaskDecorator:
    """`task` itself: `@task`, `@task(...)`, `@task.bash` and `@task.bash(...)`."""

    def __call__(self, fn: Callable | None = None, /, **opts: Any) -> Any:
        if fn is not None:
            return PythonTask(fn, **opts)
        return lambda f: PythonTask(f, **opts)

    def bash(self, fn: Callable | None = None, /, **opts: Any) -> Any:
        if fn is not None:
            return BashTask(fn, **opts)
        return lambda f: BashTask(f, **opts)


task = _TaskDecorator()
