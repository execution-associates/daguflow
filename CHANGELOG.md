# Changelog

## 0.2.0

- **`@task` is the run-time Python task** (0.1.0's `@task.python`). The function runs where the step runs;
  its arguments arrive as JSON and its return value is the step's output.
- **Shell commands are `@task.bash`**, which must return a command string or an argv list. Returning an
  `Action` or a `Step` from a task is gone: use `actions.x.y(...).step(...)`.
- The README and examples are Python throughout.

## 0.1.0

First release.
