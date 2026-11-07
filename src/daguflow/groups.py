"""Context managers that group steps: SubDAG (a child DAG) and ForEach (an inline loop).

    with SubDAG("apply", items=lights.output, as_="light", max_concurrent=4) as apply:
        e = set_effect(apply.params.light)
        c = set_color(apply.params.light)
        e >> c
    report(apply.results)

For one task per item, `task.expand(...)` writes this for you.

The block's steps become a local child DAG: an extra `---` document in the
parent's file, which dagu looks up first, by name. The `with` statement
itself is a `dag.run` step in the parent, so it takes part in `>>` like any
step. Children do not inherit the parent's `env`; pass `env=` (or
`pass_env=`) explicitly.
"""

from __future__ import annotations

from typing import Any

from . import _context, params as _params
from .dag import DAG
from .refs import Gathered, Ref
from .step import Action, Container, Step

# dagu's name for the current item; daguflow binds it to a named param and never exposes it.
_ITEM = Ref("ITEM")


def _parallel(items: Any, max_concurrent: int | None) -> Any:
    if items is None:
        return None
    if max_concurrent is None:
        return items
    return {"items": items, "max_concurrent": max_concurrent}


class SubDAG(Step):
    """A local child DAG, run by one `dag.run` (or `dag.enqueue`) step in the parent.

    params:          values passed to the child, by name. The child declares
                     them (with an empty default) unless child_params says
                     otherwise.
    child_params:    the child's own param definitions (name -> default | Param).
    items:           a list, or a step (or Ref) whose output is a JSON list: run
                     the child once per item, in parallel (`parallel:`).
    as_:             the child param each item arrives in (required with items):
                     `sub.params.<as_>` inside the block.
    max_concurrent:  cap on parallel children (dagu's default is 10).
    enqueue:         queue the child and move on, instead of waiting for it.
    env, dag_fields: the child DAG's own env and other top-level keys.
    Remaining keyword arguments configure the call step (retries, timeout,
    continue_on, preconditions, output, ...).
    """

    _names_items = True  # Mapped binds its own items

    def __init__(
        self,
        name: str,
        *,
        params: dict[str, Any] | None = None,
        child_params: dict[str, Any] | None = None,
        items: Any = None,
        as_: str | None = None,
        max_concurrent: int | None = None,
        enqueue: bool = False,
        queue: str | None = None,
        env: Any = None,
        dag_fields: dict[str, Any] | None = None,
        step_name: str | None = None,
        **step_opts: Any,
    ):
        parent = _context.current_dag()
        if parent is None:
            raise RuntimeError("SubDAG must be opened inside a DAG")
        if isinstance(items, Step):
            items = items._task_input()
        params = dict(params or {})
        if as_ is not None:
            if items is None:
                raise TypeError(f"SubDAG {name!r}: as_= names the item of a fan-out; pass items=")
            if as_ in params:
                raise TypeError(f"SubDAG {name!r}: {as_!r} is both the item (as_=) and a param")
            params[as_] = _ITEM
        elif items is not None and self._names_items:
            raise TypeError(f"SubDAG {name!r}: name the item with as_=, e.g. as_=\"row\"; "
                            "it arrives as sub.params.<as_>")
        if child_params is not None:
            defs = _params.from_spec(child_params)
        else:
            defs = [_params.from_value(k, "") for k in (params or {})]
        child = DAG(name, params=defs or None, env=env, source=parent.source, **(dag_fields or {}))
        child.param_defs = defs
        child.parent = parent
        parent.locals.append(child)
        self.child = child

        with_: dict[str, Any] = {"dag": name}
        if params:
            with_["params"] = dict(params)
        if queue is not None:
            if not enqueue:
                raise TypeError("queue= needs enqueue=True")
            with_["queue"] = queue
        super().__init__(
            step_name or name,
            action=Action("dag.enqueue" if enqueue else "dag.run", with_),
            parallel=_parallel(items, max_concurrent),
            **step_opts,
        )

    def __enter__(self) -> SubDAG:
        _context.push(self.child)
        return self

    def __exit__(self, *exc) -> None:
        _context.pop(self.child)
        if exc[0] is None and not self.child.steps:
            raise ValueError(f"SubDAG {self.child.name!r} has no steps")

    @property
    def params(self):
        """The child's params, for use inside the block: `sub.params.light`."""
        return self.child.params

    @property
    def results(self) -> Gathered:
        """Each child run's result, in item order, for a @task: it receives a list.

        A result is the output of the child's last step: the one step with an
        output that no other child step depends on (a @task always has an
        output), JSON-decoded. Only successful children report, and dagu fails
        the fan-out when any child fails.
        """
        if self.spec.get("parallel") is None:
            raise TypeError(f"SubDAG {self.child.name!r}: results needs a fan-out (items=); use .outputs")
        steps = [s for s in self.child.steps if isinstance(s.spec.get("output"), str)]
        upstream = {id(u) for s in self.child.steps for u in s.upstream if isinstance(u, Step)}
        names = {u for s in self.child.steps for u in s.upstream if isinstance(u, str)}
        last = [s for s in steps if id(s) not in upstream and s.name not in names] if len(steps) > 1 else steps
        if len(last) != 1:
            found = [s.name for s in last] or "none"
            raise TypeError(f"SubDAG {self.child.name!r}: results reads the one last child step with an "
                            f"output, found {found}; chain the steps or end the block with one step")
        return Gathered(self.output.expr, producer=self, key=last[0].spec["output"])

    @property
    def outputs(self) -> Ref:
        """The child's outputs, read through this step's captured result.

        `sub.outputs.GREETING` renders `${SUB.outputs.GREETING}`. For a
        parallel fan-out the result holds a list: `sub.output["outputs"][0]`.
        """
        return self.output["outputs"]


class Mapped(SubDAG):
    """What `task.expand(...)` returns: one child run per item. Passed to a @task, it is the list of results."""

    _names_items = False

    def _task_input(self) -> Gathered:
        return self.results


def call_dag(
    dag: str | DAG,
    name: str | None = None,
    *,
    params: dict[str, Any] | str | None = None,
    items: Any = None,
    as_: str | None = None,
    max_concurrent: int | None = None,
    enqueue: bool = False,
    queue: str | None = None,
    **step_opts: Any,
) -> Step:
    """Run another DAG (by name or file path under the DAGs dir) as a step.

    With items=, it runs once per item; as_= names the param each item arrives
    in. Without as_=, dagu passes a map item's keys as the params.
    """
    target = dag.name if isinstance(dag, DAG) else dag
    with_: dict[str, Any] = {"dag": target}
    if as_ is not None:
        if items is None:
            raise TypeError("as_= names the item of a fan-out; pass items=")
        if isinstance(params, str):
            raise TypeError("as_= needs params as a dict")
        params = {**(params or {}), as_: _ITEM}
    if params:
        with_["params"] = params
    if queue is not None:
        with_["queue"] = queue
    return Step(
        name or target.replace("/", "-").removesuffix(".yaml"),
        action=Action("dag.enqueue" if enqueue else "dag.run", with_),
        parallel=_parallel(items, max_concurrent),
        **step_opts,
    )


ExternalDAG = call_dag


class ForEach(Step):
    """An inline `foreach:` step: the block's steps run once per item.

    `loop.item` is the current item (`${foreach.item}`, or `${foreach.<as_>}`),
    `loop.index` its position. `collect` maps output names to expressions
    evaluated per item after the body ran.
    """

    def __init__(
        self,
        items: Any,
        *,
        name: str | None = None,
        as_: str = "item",
        key: str | Ref | None = None,
        max_concurrent: int | None = None,
        collect: dict[str, Any] | None = None,
        **step_opts: Any,
    ):
        loop: dict[str, Any] = {"items": items}
        if as_ != "item":
            loop["as"] = as_
        if key is not None:
            loop["key"] = key
        if max_concurrent is not None:
            loop["max_concurrent"] = max_concurrent
        if collect is not None:
            loop["collect"] = collect
        self._as = as_
        super().__init__(name or "foreach", foreach=loop, **step_opts)
        self.body = Container()

    def __enter__(self) -> ForEach:
        _context.push(self.body)
        return self

    def __exit__(self, *exc) -> None:
        _context.pop(self.body)
        if exc[0] is None and not self.body.steps:
            raise ValueError(f"ForEach {self.name!r} has no steps")

    @property
    def item(self) -> Ref:
        return Ref(f"foreach.{self._as}")

    @property
    def index(self) -> Ref:
        return Ref("foreach.index")

    @property
    def key(self) -> Ref:
        return Ref("foreach.key")
