# Changelog

## 0.4.0

- **`task.expand()`, `task.partial(...).expand()` and `task.expand_kwargs()`**, Airflow's dynamic task mapping:
  one run per item, in parallel, and the next task gets the results as a list.
- **Breaking: `ITEM` is gone.** A hand-written fan-out names its item: `SubDAG("x", items=..., as_="row")`,
  then `x.params.row`; `call_dag(..., items=..., as_=...)` likewise. `SubDAG.item` is gone too.
- The README's digest and the examples map with `.expand()`.

## 0.3.0

- **`SubDAG.results`**: a fan-out's results, which a `@task` receives as a list of each child's output.
- The README leads with a Hacker News digest (`examples/hn_digest.py`), which the tests run on real dagu.
- Fixed: a `@task` named like one of the runner's own variables (`args`, `name`, `raw`, `result`, ...) failed
  at run time.

## 0.2.0

- **`@task` is the run-time Python task** (0.1.0's `@task.python`). The function runs where the step runs;
  its arguments arrive as JSON and its return value is the step's output.
- **Shell commands are `@task.bash`**, which must return a command string or an argv list. Returning an
  `Action` or a `Step` from a task is gone: use `actions.x.y(...).step(...)`.
- The README and examples are Python throughout.

## 0.1.0

First release.
