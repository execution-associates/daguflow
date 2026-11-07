"""Context managers that group steps: SubDAG (a child DAG) and ForEach (an inline loop).

    with SubDAG("apply", items=lights, params={"light": ITEM}, env=PI_ENV) as apply:
        e = set_effect(light=apply.params.light)
        c = set_color(light=apply.params.light)
        e >> c
    fetch >> apply >> report

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
from .refs import ITEM, Gathered, Ref
from .step import Action, Container, Step


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
    items:           a list or a Ref to a JSON array: run the child once per
                     item, in parallel (`parallel:`). `ITEM` is the item.
    max_concurrent:  cap on parallel children (dagu's default is 10).
    enqueue:         queue the child and move on, instead of waiting for it.
    env, dag_fields: the child DAG's own env and other top-level keys.
    Remaining keyword arguments configure the call step (retries, timeout,
    continue_on, preconditions, output, ...).
    """

    def __init__(
        self,
        name: str,
        *,
        params: dict[str, Any] | None = None,
        child_params: dict[str, Any] | None = None,
        items: Any = None,
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
    def item(self) -> Ref:
        """The current item of a parallel fan-out: `${ITEM}` (`.field` for maps)."""
        return ITEM

    @property
    def params(self):
        """The child's params, for use inside the block: `sub.params.light`."""
        return self.child.params

    @property
    def results(self) -> Gathered:
        """Each child run's result, in item order, for a @task: it receives a list.

        A result is the output of the child's one step that has an output (a
        @task always has one), JSON-decoded. Only successful children report,
        and dagu fails the fan-out when any child fails.
        """
        if self.spec.get("parallel") is None:
            raise TypeError(f"SubDAG {self.child.name!r}: results needs a fan-out (items=); use .outputs")
        outs = [s.spec["output"] for s in self.child.steps if isinstance(s.spec.get("output"), str)]
        if len(outs) != 1:
            raise TypeError(f"SubDAG {self.child.name!r}: results needs exactly one child step with an "
                            f"output, found {outs or 'none'}")
        return Gathered(self.output.expr, producer=self, key=outs[0])

    @property
    def outputs(self) -> Ref:
        """The child's outputs, read through this step's captured result.

        `sub.outputs.GREETING` renders `${SUB.outputs.GREETING}`. For a
        parallel fan-out the result holds a list: `sub.output["outputs"][0]`.
        """
        return self.output["outputs"]


def call_dag(
    dag: str | DAG,
    name: str | None = None,
    *,
    params: dict[str, Any] | str | None = None,
    items: Any = None,
    max_concurrent: int | None = None,
    enqueue: bool = False,
    queue: str | None = None,
    **step_opts: Any,
) -> Step:
    """Run another DAG (by name or file path under the DAGs dir) as a step."""
    target = dag.name if isinstance(dag, DAG) else dag
    with_: dict[str, Any] = {"dag": target}
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
