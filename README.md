# daguflow

Write [dagu](https://github.com/dagucloud/dagu) workflows in Python, the way Airflow does it: `@dag` and
`@task` decorators, `>>` for dependencies, and context managers for sub-DAGs and loops. `daguflow build` turns
them into the YAML dagu runs. Each file is checked against the schema of the dagu version daguflow pins
(**v2.24.0**), so a typo fails at build time, not when dagu loads the file.

```console
$ pip install daguflow        # or: uv add daguflow
```

```python
from typing import Annotated
from daguflow import ITEM, Cron, Range, SSHTarget, SubDAG, dag, env, task

pi = SSHTarget(user=env.PI_USER, host="192.168.1.50", key="/etc/dagu/ssh/id_ed25519",
                   strict_host_key=True, known_host_file="/etc/dagu/ssh/known_hosts")

@task(runs_on=pi)
def list_lights():
    return "lights.py list --json"

@task(runs_on=pi)
def set_level(light, level):
    return f"lights.py brightness --light {light:q} --value {level}"

# Runs on the Pi at run time. unsafe_args: its input is our own lights.py JSON.
@task.python(runs_on=pi, python="/usr/bin/python3", unsafe_args=True)
def count(listing: dict) -> int:
    return len(listing["names"])

@dag(schedule=Cron("30 22 * * *", tz="America/Los_Angeles"), labels=["lights"])
def dim_each(level: Annotated[int, Range(0, 100)] = 20):
    """Dim every light, four at a time."""
    found = list_lights()
    with SubDAG("one", items=found["names"], max_concurrent=4,
                params={"light": ITEM, "level": level}) as one:
        set_level(one.params.light, one.params.level)
    one >> count(found)
```

```console
$ daguflow build workflows -o dags/          # one YAML file per DAG
$ daguflow build workflows -o dags/ --check  # exit 1 with a diff if dags/ is stale
```

## How it maps to dagu

| Python | dagu YAML |
|---|---|
| `@dag` function / `with DAG("name"):` | one file, `<name>.yaml` (the filename is the name) |
| function parameters | `params:`: plain defaults give `- value: 50`; `Literal`, `Annotated[.., Range/Pattern/Length/Doc]`, `Param(...)` or no default give rich definitions dagu enforces at start |
| first docstring line / the rest | `description:` / the file's header comment |
| `@task` call, `shell(...)`, `step(...)`, `target.run(...)`, `actions.x.y(...).step()` | a step |
| `a >> b`, `[a, b] >> c`, `chain(a, b, c)` | `depends:` |
| reading another step's output | `depends:` added for you (dagu won't infer it) |
| `with SubDAG("x"):` | a `---` local DAG in the same file and a `dag.run` step; `items=` adds `parallel:` |
| `with ForEach(items):` | an inline `foreach:` step |
| `call_dag("other")` | `action: dag.run` against another file |
| `with on_failure():` (and `on_success/exit/abort/init/wait`) | `handler_on:` |
| `Cron("0 9 * * *", tz=...)` | `CRON_TZ=... 0 9 * * *` |

Every other dagu key is passed by its own name, e.g. `Step(..., repeat_policy={...})` or
`DAG(..., max_active_steps=4)`, and checked against the schema. A few Python conveniences translate:
- `timeout=`: seconds or a `timedelta`, becomes `timeout_sec`.
- `retries=` with `retry_interval=` (default 5s): dagu requires an interval for any `retry_policy`.
- `env=`: a dict, becomes dagu's ordered list.
- `tags=`: becomes `labels`.

## References and quoting

Refs are build-time stand-ins for dagu's `${...}`. Format them in f-strings:

| Python | renders |
|---|---|
| `f"{effect}"` | `${effect}` |
| `f"{effect:q}"` | `"${effect}"` |
| `f"{value:bare}"` | `$value` |
| `step.output["field"]` | `${STEP.field}` |
| `env.HOME` | `${env.HOME}` |
| `ctx.run.id` | `${context.run.id}` |
| `ITEM` | `${ITEM}` |
| `var("NAME")` | `${NAME}` |

**Use `{x:q}` for free text in SSH commands.** For an SSH target, dagu replaces a double-quoted `"${x}"` with the
value re-quoted as one shell word, so `Rock 'n' Roll (Live) & More` arrives as one argument. Unquoted, the
remote shell splits it. Single-quoted, dagu leaves it unexpanded. Measured on dagu 2.16.2 and 2.24.0
(`tests/test_ssh_integration.py`).

**SSH `with:` fields expand only scoped references.** Write `user=env.PI_USER`, never `"${PI_USER}"`.

## `@task` and `@task.python`

- **`@task` runs at build time.** It returns a command string, an `Action`, or a `Step`, and calling it inside
  a DAG adds the step. Decorator kwargs are step options (`output=`, `retries=`, `timeout=`, `continue_on=`,
  ...). `runs_on=` takes an `SSHTarget` or `container(image)`. `task.override(name=...)` changes them for one
  call. Calling a task twice names the second step `name__1`, as in Airflow.
- **`@task.python` runs at run time.** The function's own source ships to wherever the step runs: the dagu
  worker (`run:`), an SSH host, or a container.
  - Arguments go in as JSON. The return value comes back as JSON on stdout and becomes the step's output.
  - The function's own `print`s go to stderr, so they can't corrupt that output.
  - Passing another step (or its output) as an argument makes it upstream.
  - `deps=["httpx"]` runs it through `uv run --with`.
  - **The function must be self-contained**: imports inside the body, no closures, no module globals. Build
    fails and names any outside names it uses.
  - **Python must exist where the step runs.** dagu's official image has none.
  - **How run-time values arrive:**
    - Locally, through step `env:`, so values are never spliced into code.
    - Over SSH, each on its own file descriptor as a quoted heredoc, so quotes, `$` and JSON arrive byte for
      byte. A value containing the line `DAGUFLOW_EOF` ends its heredoc early, and the rest runs as shell on
      the host. **So build accepts only params dagu constrains**: an `enum`, a numeric type, or a `pattern`
      that admits no newline. Step outputs, env and unconstrained params are refused; `unsafe_args=True`
      overrides, for values whose every source you trust.

## Actions

`daguflow.actions` has a typed, keyword-only builder for every builtin action at the pinned dagu version,
generated from its schema (`tools/gen_actions.py`):

```python
from daguflow import actions
actions.http.request(method="GET", url="https://example.com", timeout=10).step("fetch", output="PAGE")
actions.jq.filter(filter=".items[]", data=page.output).step("items")
actions.custom("dagucloud/duckdb@v1", query="select 1").step("duck")
```

- Required keys are enforced, and keys dagu would reject raise `TypeError`.
- Python keywords take a trailing underscore: `from_=`, `import_=`.
- `SSHTarget(...)` (also `actions.ssh.Target`) writes SSH settings once. Use `.run(cmd)` for a step, as
  `@task(runs_on=...)`, or as a DAG's `ssh=` default.
- **A DAG-level `ssh=` moves every step without an action onto that host,** plain `run:` steps included.

## CLI

- `daguflow build TARGET... -o DIR` writes one YAML per DAG. TARGET is a module, a package directory or a
  `.py` file.
  - `--check` writes nothing and exits 1 with a diff when DIR is stale.
  - `--prune` deletes files daguflow generated that no DAG produces any more. Hand-written files are left
    alone.
- `daguflow validate FILE...` checks the schema plus dagu's document rules.
  - `--dagu-bin dagu` also runs `dagu validate`.
  - `--server URL` also asks a running dagu's `/dags/validate`.
- `daguflow run DAG --server URL -p k=v --wait` starts a run and prints its outputs. `--inline MODULE` sends
  the DAG's YAML without a file on the server.
- `daguflow schema show` names the pinned schema and its cache; `daguflow schema fetch [--out PATH]`
  downloads it ahead of an offline build.
- `daguflow schema update --version vX.Y.Z`, in a daguflow checkout, repins another dagu release. Then run
  `mise run gen` and the tests.

## The dagu schema

daguflow validates against the schema of one dagu release, pinned by commit and sha256, but does not ship
it: dagu is GPL-3.0-or-later and daguflow is MIT. The first build downloads it from dagu's repository,
checks the hash and caches it in `$XDG_CACHE_HOME/daguflow` (`~/.cache/daguflow`). Offline, run
`daguflow schema fetch` while you still have a network, or set `DAGUFLOW_SCHEMA` to a copy; either way the
hash is checked.

## Client

```python
from daguflow.client import Client
with Client("http://127.0.0.1:8080") as dagu:
    run_id = dagu.start("set_light_effect", params={"effect": "Good Vibes"})
    run = dagu.wait("set_light_effect", run_id)
    print(run.status, dagu.outputs("set_light_effect", run_id, decode=True))
```

Covered calls:
- `validate`, `run_inline`, `start`, `enqueue`, `wait`, `status`, `outputs`, `step_log`, `run_log`, `stop`,
  `retry`.
- `list_dags`, `list_runs`, `sub_runs`, `suspend`, `create_dag` / `update_spec` / `delete_dag`.
- `request()` for anything else.

API quirks the client absorbs:
- Params go as a JSON object string.
- The run-detail wrapper key differs by endpoint (`dagRunDetails` vs `dagRun`).
- Outputs come back as strings under camelCased keys (`output: RESULT` → `result`).

## Development

`mise run test` runs everything in a throwaway isb sandbox:
- the unit tests;
- golden YAML for `examples/`;
- `dagu validate` on every golden file, using the pinned release binary;
- the examples running on a real dagu server, and SSH steps against a throwaway sshd.

Without isb: `uv run --extra test pytest`. The integration tier runs when `DAGUFLOW_DAGU_BIN` points at
the pinned dagu binary (`tools/fetch-dagu.sh` downloads it).

`mise run gen` regenerates the action builders. A test fails when they drift from the schema.

## License

MIT. dagu's schema, which daguflow downloads at build time, is GPL-3.0-or-later and stays dagu's.
