"""A client for dagu's REST API (/api/v1).

    with Client("http://127.0.0.1:8080/api/v1") as dagu:
        run = dagu.start("set_light_effect", params={"effect": "Good Vibes"})
        done = dagu.wait("set_light_effect", run)
        print(done.status, dagu.outputs("set_light_effect", run))

Shapes measured against dagu 2.16.2 and 2.24.0:
- start/enqueue `params` is a string; a JSON object string is accepted, so
  values are never hand-quoted into `k="v"` form.
- POST /dags/validate answers 200 with `valid: false` for a bad spec.
- run details are wrapped as `dagRunDetails` on /dag-runs/{name}/{id} but as
  `dagRun` on /dags/{name}/dag-runs/{id}; `status()` reads either.
- outputs are strings keyed by camelCased names (`output: RESULT` -> `result`).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

import httpx


class Status(IntEnum):
    NOT_STARTED = 0
    RUNNING = 1
    FAILED = 2
    ABORTED = 3
    SUCCEEDED = 4
    QUEUED = 5
    PARTIALLY_SUCCEEDED = 6
    WAITING = 7
    REJECTED = 8

    @property
    def active(self) -> bool:
        return self in (Status.RUNNING, Status.QUEUED, Status.WAITING, Status.NOT_STARTED)


class DaguError(RuntimeError):
    def __init__(self, status_code: int, code: str | None, message: str):
        super().__init__(f"dagu {status_code} {code or ''}: {message}".replace("  ", " "))
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass
class Run:
    name: str
    dag_run_id: str
    status: Status
    status_label: str
    started_at: str | None = None
    finished_at: str | None = None
    params: str | None = None
    nodes: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return self.status == Status.SUCCEEDED

    def step(self, name: str) -> dict[str, Any] | None:
        for node in self.nodes:
            if node.get("step", {}).get("name") == name:
                return node
        return None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Run:
        return cls(
            name=data.get("name", ""),
            dag_run_id=data.get("dagRunId", ""),
            status=Status(int(data.get("status", 0))),
            status_label=data.get("statusLabel", ""),
            started_at=data.get("startedAt"),
            finished_at=data.get("finishedAt"),
            params=data.get("params"),
            nodes=list(data.get("nodes") or []),
            raw=data,
        )


def _params(params: dict[str, Any] | str | None) -> str | None:
    if params is None:
        return None
    if isinstance(params, str):
        return params
    return json.dumps(params)


class Client:
    def __init__(self, base_url: str, *, token: str | None = None, auth: tuple[str, str] | None = None,
                 timeout: float = 30.0, headers: dict[str, str] | None = None,
                 transport: httpx.BaseTransport | None = None):
        if not base_url.rstrip("/").endswith("/api/v1"):
            # Without the base path, requests fall through to the web UI's
            # catch-all and come back 405 with an empty body.
            base_url = base_url.rstrip("/") + "/api/v1"
        hdrs = dict(headers or {})
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        self._http = httpx.Client(base_url=base_url.rstrip("/") + "/", headers=hdrs, auth=auth,
                                  timeout=timeout, transport=transport)

    # -- plumbing ------------------------------------------------------------

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Any endpoint: `request("GET", "queues")`. Returns parsed JSON or text."""
        response = self._http.request(method, path.lstrip("/"), **kwargs)
        if response.status_code >= 400:
            try:
                body = response.json()
                code, message = body.get("code"), body.get("message", response.text)
            except ValueError:
                code, message = None, response.text[:400]
            raise DaguError(response.status_code, code, message)
        if not response.content:
            return None
        if "json" in response.headers.get("content-type", ""):
            return response.json()
        return response.text

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- DAG definitions -------------------------------------------------------

    def health(self) -> dict[str, Any]:
        return self.request("GET", "health")

    def list_dags(self, **query: Any) -> list[dict[str, Any]]:
        out, page = [], 1
        while True:
            data = self.request("GET", "dags", params={"page": page, "perPage": 100, **query})
            out.extend(data.get("dags") or data.get("items") or [])
            pagination = data.get("pagination") or {}
            if page >= int(pagination.get("totalPages") or 1):
                return out
            page += 1

    def get_dag(self, name: str) -> dict[str, Any]:
        return self.request("GET", f"dags/{name}")

    def get_spec(self, name: str) -> str:
        return self.request("GET", f"dags/{name}/spec").get("spec", "")

    def validate(self, spec: str, *, name: str | None = None) -> dict[str, Any]:
        body = {"spec": spec, **({"name": name} if name else {})}
        return self.request("POST", "dags/validate", json=body)

    def create_dag(self, name: str, spec: str | None = None) -> dict[str, Any]:
        return self.request("POST", "dags", json={"name": name, **({"spec": spec} if spec else {})})

    def update_spec(self, name: str, spec: str) -> dict[str, Any]:
        return self.request("PUT", f"dags/{name}/spec", json={"spec": spec})

    def delete_dag(self, name: str) -> None:
        self.request("DELETE", f"dags/{name}")

    def suspend(self, name: str, suspend: bool = True) -> None:
        self.request("POST", f"dags/{name}/suspend", json={"suspend": suspend})

    # -- runs -----------------------------------------------------------------

    def start(self, name: str, *, params: dict[str, Any] | str | None = None, dag_run_id: str | None = None,
              singleton: bool = False, labels: list[str] | None = None) -> str:
        body: dict[str, Any] = {}
        if (p := _params(params)) is not None:
            body["params"] = p
        if dag_run_id:
            body["dagRunId"] = dag_run_id
        if singleton:
            body["singleton"] = True
        if labels:
            body["labels"] = labels
        return self.request("POST", f"dags/{name}/start", json=body)["dagRunId"]

    def enqueue(self, name: str, *, params: dict[str, Any] | str | None = None, queue: str | None = None,
                dag_run_id: str | None = None) -> str:
        body: dict[str, Any] = {}
        if (p := _params(params)) is not None:
            body["params"] = p
        if queue:
            body["queue"] = queue
        if dag_run_id:
            body["dagRunId"] = dag_run_id
        return self.request("POST", f"dags/{name}/enqueue", json=body)["dagRunId"]

    def run_inline(self, spec: str, *, name: str | None = None, params: dict[str, Any] | str | None = None,
                   dag_run_id: str | None = None) -> str:
        """Run YAML that is not in the DAGs directory (POST /dag-runs)."""
        body: dict[str, Any] = {"spec": spec}
        if name:
            body["name"] = name
        if (p := _params(params)) is not None:
            body["params"] = p
        if dag_run_id:
            body["dagRunId"] = dag_run_id
        return self.request("POST", "dag-runs", json=body)["dagRunId"]

    def status(self, name: str, dag_run_id: str) -> Run:
        data = self.request("GET", f"dag-runs/{name}/{dag_run_id}")
        return Run.from_api(data.get("dagRunDetails") or data.get("dagRun") or data)

    def wait(self, name: str, dag_run_id: str, *, timeout: float = 300.0, interval: float = 0.5,
             max_interval: float = 3.0) -> Run:
        """Poll until the run is no longer running, queued or waiting."""
        deadline = time.monotonic() + timeout
        while True:
            run = self.status(name, dag_run_id)
            if not run.status.active:
                return run
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{name}/{dag_run_id} still {run.status_label} after {timeout}s")
            time.sleep(interval)
            interval = min(interval * 1.5, max_interval)

    def outputs(self, name: str, dag_run_id: str, *, decode: bool = False) -> dict[str, Any]:
        """The run's outputs. decode=True parses values that are JSON objects or arrays."""
        values = dict(self.request("GET", f"dag-runs/{name}/{dag_run_id}/outputs").get("outputs") or {})
        if decode:
            for key, value in values.items():
                if isinstance(value, str) and value[:1] in "[{":
                    try:
                        values[key] = json.loads(value)
                    except ValueError:
                        pass
        return values

    def step_log(self, name: str, dag_run_id: str, step: str, *, stream: str = "stdout",
                 tail: int | None = None) -> str:
        query: dict[str, Any] = {"stream": stream}
        if tail:
            query["tail"] = tail
        data = self.request("GET", f"dag-runs/{name}/{dag_run_id}/steps/{step}/log", params=query)
        return data.get("content", "") if isinstance(data, dict) else data

    def run_log(self, name: str, dag_run_id: str) -> str:
        data = self.request("GET", f"dag-runs/{name}/{dag_run_id}/log")
        return data.get("content", "") if isinstance(data, dict) else data

    def stop(self, name: str, dag_run_id: str) -> None:
        self.request("POST", f"dag-runs/{name}/{dag_run_id}/stop")

    def retry(self, name: str, dag_run_id: str, *, step: str | None = None) -> None:
        body: dict[str, Any] = {"dagRunId": dag_run_id}
        if step:
            body["stepName"] = step
        self.request("POST", f"dag-runs/{name}/{dag_run_id}/retry", json=body)

    def list_runs(self, name: str | None = None, *, limit: int = 100, **query: Any) -> list[dict[str, Any]]:
        path = f"dag-runs/{name}" if name else "dag-runs"
        data = self.request("GET", path, params={"limit": limit, **query})
        return list(data.get("dagRuns") or [])

    def sub_runs(self, name: str, dag_run_id: str) -> list[dict[str, Any]]:
        return list(self.request("GET", f"dag-runs/{name}/{dag_run_id}/sub-dag-runs").get("subRuns") or [])

    def sub_run(self, name: str, dag_run_id: str, sub_run_id: str) -> Run:
        data = self.request("GET", f"dag-runs/{name}/{dag_run_id}/sub-dag-runs/{sub_run_id}")
        return Run.from_api(data.get("dagRunDetails") or data)
