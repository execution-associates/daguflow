"""Every daguflow feature on local steps, runnable on any dagu worker with python3.

tests/test_integration.py runs these against the pinned dagu binary.
"""

from typing import Annotated, Literal

from daguflow import (
    DAG, ITEM, Cron, ForEach, Param, Range, SubDAG, call_dag, chain, ctx, dag, on_exit, on_failure,
    shell, step, task,
)
from daguflow import actions


@dag(labels=["examples"])
def hello(who="world"):
    """Say hello and capture it as an output."""
    shell(f"echo hello {who}", name="greet", output="GREETING")


@task
def make_items(count: int) -> list:
    return [{"n": i, "label": f"item-{i}"} for i in range(count)]


@task
def total(items: list) -> dict:
    import math

    print("this goes to stderr, not the output")
    return {"sum": sum(i["n"] for i in items), "sqrt": math.isqrt(len(items))}


@task
def describe(summary: dict) -> str:
    return f"sum={summary['sum']}"


@task
def square_of(n: int) -> int:
    return n * n


@task
def paint(color: str) -> str:
    return color.upper()


@dag(labels=["examples"], schedule=Cron("0 6 * * 1-5", tz="America/Los_Angeles"), timeout=600,
     max_active_steps=4)
def pipeline(count: Annotated[int, Range(1, 20)] = 3, mode: Literal["fast", "slow"] = "fast"):
    """Python tasks passing JSON, a parallel sub-DAG fan-out, an inline loop and handlers.

    The body reads like Airflow TaskFlow: outputs passed as arguments
    become dependencies on their own."""
    items = make_items(3)
    summary = total(items)
    describe(summary)

    with SubDAG("square", items=items.output, max_concurrent=2,
                child_params={"n": "0", "label": ""}) as square:
        square_of(square.params.n)
    items >> square

    with ForEach(["red", "green"], as_="color", max_concurrent=2, name="colors") as colors:
        paint(colors.item)

    checked = shell("test -n \"$HOME\" && echo ok", name="check", retries=2,
                    preconditions=[{"condition": "${mode}", "expected": "re:fast|slow"}])
    tolerant = shell("exit 3", name="tolerant", continue_on={"exit_code": [3]})
    chain(checked, tolerant)

    with on_exit():
        shell("echo run ${context.run.id} finished", name="cleanup")
    with on_failure():
        shell("echo failed >&2", name="alert")


with DAG("classic", description="The `with DAG(...)` style, operator objects and >> wiring",
         labels=["examples"], params={"name": Param("dagu", description="who to greet")},
         env={"GREETING": "hi"}) as classic:
    a = step("first", run="echo ${GREETING} ${name}", output="FIRST")
    b = actions.log.write(message="first said ${FIRST}").step("log")
    c = shell("echo third", name="third")
    a >> [b, c]


@dag(labels=["examples"])
def calls_hello():
    """Run another DAG file by name and read its outputs."""
    child = call_dag("hello", params={"who": "from-parent"}, output="CHILD")
    shell(f"echo child said {child.output['outputs']['GREETING']}", name="echo-child")
    shell(f"echo run {ctx.run.id}", name="whoami")


@dag(labels=["examples"])
def nested():
    """A sub-DAG inside a sub-DAG: both become documents in this one file."""
    with SubDAG("outer", params={"word": "hi"}) as outer:
        with SubDAG("inner", params={"word": outer.params.word}) as inner:
            shell(f"echo inner {inner.params.word}", name="say-inner", output="INNER")
        shell("echo outer done", name="say-outer")
