# daguflow

Write [dagu](https://github.com/dagucloud/dagu) workflows in Python, the way Airflow's TaskFlow does it:
`@dag` and `@task` decorators, and context managers for sub-DAGs and loops. A `@task` is a Python function
that runs when the step runs. Its arguments arrive as JSON and its return value becomes the step's output,
so passing one task's result to another is the dependency. `daguflow build` writes the YAML dagu schedules.
Each file is checked against the schema of the dagu version daguflow pins (**v2.24.0**), so a typo fails at
build time, not when dagu loads the file.

```console
$ pip install daguflow        # or: uv add daguflow
```

Every morning, fetch Hacker News' top stories, eight at a time, and rank the ones worth reading:

```python
from daguflow import ITEM, Cron, SubDAG, dag, task


@task
def top_ids(api: str, limit: int) -> list:
    import json, urllib.request
    with urllib.request.urlopen(f"{api}/topstories.json", timeout=10) as r:
        return json.load(r)[:limit]


@task(retries=3)
def story(api: str, story_id: int) -> dict:
    import json, urllib.request
    with urllib.request.urlopen(f"{api}/item/{story_id}.json", timeout=10) as r:
        s = json.load(r)
    return {"title": s["title"], "score": s["score"], "comments": s.get("descendants", 0)}


@task
def digest(stories: list, min_score: int) -> str:
    hot = sorted((s for s in stories if s["score"] >= min_score), key=lambda s: -s["score"])
    return "\n".join(f"{s['score']:>5}  {s['title']}" for s in hot)


@dag(schedule=Cron("0 8 * * *"))
def hn_digest(limit: int = 30, min_score: int = 100, api: str = "https://hacker-news.firebaseio.com/v0"):
    """This morning's Hacker News, best first."""
    ids = top_ids(api, limit)
    with SubDAG("fetch", items=ids.output, max_concurrent=8,
                params={"story_id": ITEM, "api": api}) as fetch:
        story(fetch.params.api, fetch.params.story_id)
    digest(fetch.results, min_score)
```

`fetch` runs once per story ID, and `fetch.results` hands `digest` every story as a list. Each step
is its own process, so one slow or failed fetch retries alone and shows in dagu's UI.

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
| `@task` call, `@task.bash` call, `actions.x.y(...).step()`, `shell(...)`, `step(...)`, `target.run(...)` | a step |
| `a >> b`, `[a, b] >> c`, `chain(a, b, c)` | `depends:` |
| reading another step's output | `depends:` added for you (dagu won't infer it) |
| `with SubDAG("x"):` | a `---` local DAG in the same file and a `dag.run` step; `items=` adds `parallel:`, and `sub.results` gives a `@task` every child's result as a list |
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

These matter in the places a step is a shell command: `@task.bash`, `shell()` and `SSHTarget.run()`. A
`@task` never needs them: its arguments arrive as values.

**Use `{x:q}` for free text in SSH commands.** For an SSH target, dagu replaces a double-quoted `"${x}"` with the
value re-quoted as one shell word, so `Rock 'n' Roll (Live) & More` arrives as one argument. Unquoted, the
remote shell splits it. Single-quoted, dagu leaves it unexpanded. Measured on dagu 2.16.2 and 2.24.0
(`tests/test_ssh_integration.py`).

**SSH `with:` fields expand only scoped references.** Write `user=env.PI_USER`, never `"${PI_USER}"`.

## `@task` and `@task.bash`

- **`@task` is Python that runs when the step runs.** The function's own source ships to wherever the step
  runs: the dagu worker (`run:`), an SSH host (`runs_on=SSHTarget(...)`), or a container
  (`runs_on=container(image)`).
  - Arguments go in as JSON. The return value comes back as JSON on stdout and becomes the step's output.
  - The function's own `print`s go to stderr, so they can't corrupt that output.
  - Passing another step (or its output) as an argument makes it upstream.
  - Decorator kwargs are step options (`output=`, `retries=`, `timeout=`, `continue_on=`, ...), and
    `task.override(name=...)` changes them for one call. Calling a task twice names the second step
    `name__1`, as in Airflow.
  - `deps=["httpx"]` runs it through `uv run --with`.
  - **The function must be self-contained**: imports inside the body, no closures, no module globals. Build
    fails and names any outside names it uses. Pass configuration as arguments, or import your own package
    where the step runs.
  - **Python must exist where the step runs.** dagu's official image has none: build `FROM` it with
    `python3` added, run the step in a container, or send it to a host that has Python.
  - **How run-time values arrive:**
    - Locally, through step `env:`, so values are never spliced into code.
    - Over SSH, each on its own file descriptor as a quoted heredoc, so quotes, `$` and JSON arrive byte for
      byte. A value containing the line `DAGUFLOW_EOF` ends its heredoc early, and the rest runs as shell on
      the host. **So build accepts only params dagu constrains**: an `enum`, a numeric type, or a `pattern`
      that admits no newline. Step outputs, env and unconstrained params are refused; `unsafe_args=True`
      overrides, for values whose every source you trust.
- **`@task.bash` is for steps whose job really is a shell command.** The function runs at build time and
  returns the command string (or an argv list); anything else is refused. `runs_on=` works as for `@task`.

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

daguflow validates against the schema of one dagu release, pinned by commit and sha256. The first build
downloads it from dagu's repository and caches it in `$XDG_CACHE_HOME/daguflow` (`~/.cache/daguflow`). To
build offline, run `daguflow schema fetch` once while online, or set `DAGUFLOW_SCHEMA` to a copy; either way
the hash is checked.

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

MIT.
