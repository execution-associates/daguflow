"""Builders for every builtin dagu action, generated from dagu v2.24.0's dag.schema.json.

Do not edit: run `python tools/gen_actions.py > src/daguflow/actions/_generated.py`.
"""

# ruff: noqa: E501
from __future__ import annotations

from typing import Any, Literal

from .._types import Val
from ..step import Action


def exec_(*, command: Val[str], args: Val[list[Any]] | None = None) -> Action:
    """The `exec` action; requires command."""
    return Action("exec", {"command": command, "args": args})


def noop(**extra: Any) -> Action:
    """The `noop` action."""
    return Action("noop", dict(extra))


class archive:
    """`archive.*` actions."""

    @staticmethod
    def create(*, source: Val[str], destination: Val[str] | None = None, format: Val[str] | None = None, compression_level: Val[int] | None = None, password: Val[str] | None = None, overwrite: Val[bool] | None = None, preserve_paths: Val[bool] | None = None, strip_components: Val[int] | None = None, include: Val[list[Any]] | None = None, exclude: Val[list[Any]] | None = None, dry_run: Val[bool] | None = None, verbose: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, verify_integrity: Val[bool] | None = None, continue_on_error: Val[bool] | None = None) -> Action:
        """The `archive.create` action; requires source."""
        return Action("archive.create", {"source": source, "destination": destination, "format": format, "compression_level": compression_level, "password": password, "overwrite": overwrite, "preserve_paths": preserve_paths, "strip_components": strip_components, "include": include, "exclude": exclude, "dry_run": dry_run, "verbose": verbose, "follow_symlinks": follow_symlinks, "verify_integrity": verify_integrity, "continue_on_error": continue_on_error})

    @staticmethod
    def extract(*, source: Val[str], destination: Val[str] | None = None, format: Val[str] | None = None, compression_level: Val[int] | None = None, password: Val[str] | None = None, overwrite: Val[bool] | None = None, preserve_paths: Val[bool] | None = None, strip_components: Val[int] | None = None, include: Val[list[Any]] | None = None, exclude: Val[list[Any]] | None = None, dry_run: Val[bool] | None = None, verbose: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, verify_integrity: Val[bool] | None = None, continue_on_error: Val[bool] | None = None) -> Action:
        """The `archive.extract` action; requires source."""
        return Action("archive.extract", {"source": source, "destination": destination, "format": format, "compression_level": compression_level, "password": password, "overwrite": overwrite, "preserve_paths": preserve_paths, "strip_components": strip_components, "include": include, "exclude": exclude, "dry_run": dry_run, "verbose": verbose, "follow_symlinks": follow_symlinks, "verify_integrity": verify_integrity, "continue_on_error": continue_on_error})

    @staticmethod
    def list(*, source: Val[str], destination: Val[str] | None = None, format: Val[str] | None = None, compression_level: Val[int] | None = None, password: Val[str] | None = None, overwrite: Val[bool] | None = None, preserve_paths: Val[bool] | None = None, strip_components: Val[int] | None = None, include: Val[list[Any]] | None = None, exclude: Val[list[Any]] | None = None, dry_run: Val[bool] | None = None, verbose: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, verify_integrity: Val[bool] | None = None, continue_on_error: Val[bool] | None = None) -> Action:
        """The `archive.list` action; requires source."""
        return Action("archive.list", {"source": source, "destination": destination, "format": format, "compression_level": compression_level, "password": password, "overwrite": overwrite, "preserve_paths": preserve_paths, "strip_components": strip_components, "include": include, "exclude": exclude, "dry_run": dry_run, "verbose": verbose, "follow_symlinks": follow_symlinks, "verify_integrity": verify_integrity, "continue_on_error": continue_on_error})


class artifact:
    """`artifact.*` actions."""

    @staticmethod
    def list(*, path: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, include_dirs: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `artifact.list` action."""
        return Action("artifact.list", {"path": path, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "atomic": atomic, "recursive": recursive, "include_dirs": include_dirs, "max_bytes": max_bytes})

    @staticmethod
    def read(*, path: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, include_dirs: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `artifact.read` action."""
        return Action("artifact.read", {"path": path, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "atomic": atomic, "recursive": recursive, "include_dirs": include_dirs, "max_bytes": max_bytes})

    @staticmethod
    def write(*, path: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, include_dirs: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `artifact.write` action."""
        return Action("artifact.write", {"path": path, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "atomic": atomic, "recursive": recursive, "include_dirs": include_dirs, "max_bytes": max_bytes})


class browser:
    """`browser.*` actions."""

    @staticmethod
    def extract(*, url: Val[str], instruction: Val[str], schema: Val[dict[str, Any]], timeout: Val[str] | None = None, llm: Val[Any] | None = None, browser: Val[dict[str, Any]] | None = None, variables: Val[dict[str, Any]] | None = None) -> Action:
        """The `browser.extract` action; requires url, instruction, schema."""
        return Action("browser.extract", {"url": url, "instruction": instruction, "schema": schema, "timeout": timeout, "llm": llm, "browser": browser, "variables": variables})

    @staticmethod
    def run(*, url: Val[str] | None = None, do: Val[list[Any]], ai: Val[Literal["every_run", "on_miss", "never"]] | None = None, cache: Val[bool] | None = None, llm: Val[Any] | None = None, browser: Val[dict[str, Any]] | None = None, variables: Val[dict[str, Any]] | None = None) -> Action:
        """The `browser.run` action; requires do."""
        return Action("browser.run", {"url": url, "do": do, "ai": ai, "cache": cache, "llm": llm, "browser": browser, "variables": variables})


class chat:
    """`chat.*` actions."""

    @staticmethod
    def completion(*, prompt: Val[str] | None = None, messages: Val[list[Any]] | None = None, files: Val[str | list[Any]] | None = None, **extra: Any) -> Action:
        """The `chat.completion` action."""
        return Action("chat.completion", {"prompt": prompt, "messages": messages, "files": files} | extra)


class clickhouse:
    """`clickhouse.*` actions."""

    @staticmethod
    def query(*, url: Val[str], user: Val[str] | None = None, password: Val[str] | None = None, database: Val[str] | None = None, query: Val[str] | None = None, file: Val[str] | None = None, params: Val[dict[str, Any]] | None = None, settings: Val[dict[str, Any]] | None = None, output_format: Val[Literal["jsonl", "json", "csv"]] | None = None, headers: Val[bool | str] | None = None, timeout: Val[int | str] | None = None, tls_skip_verify: Val[bool | str] | None = None, tls_ca: Val[str] | None = None) -> Action:
        """The `clickhouse.query` action; requires url."""
        return Action("clickhouse.query", {"url": url, "user": user, "password": password, "database": database, "query": query, "file": file, "params": params, "settings": settings, "output_format": output_format, "headers": headers, "timeout": timeout, "tls_skip_verify": tls_skip_verify, "tls_ca": tls_ca})


class computer:
    """`computer.*` actions."""

    @staticmethod
    def extract(*, instruction: Val[str], schema: Val[dict[str, Any]], timeout: Val[str] | None = None, llm: Val[Any] | None = None, mode: Val[Literal["auto", "native", "generic"]] | None = None, screenshots: Val[Literal["on_failure", "final", "each", "never"]] | None = None) -> Action:
        """The `computer.extract` action; requires instruction, schema."""
        return Action("computer.extract", {"instruction": instruction, "schema": schema, "timeout": timeout, "llm": llm, "mode": mode, "screenshots": screenshots})

    @staticmethod
    def run(*, do: Val[list[Any]], mode: Val[Literal["auto", "native", "generic"]] | None = None, variables: Val[dict[str, Any]] | None = None, visible: Val[list[Any]] | None = None, screenshots: Val[Literal["on_failure", "final", "each", "never"]] | None = None, ai: Val[Literal["every_run", "on_miss", "never"]] | None = None, cache: Val[bool] | None = None, max_actions: Val[int] | None = None, on_confirmation: Val[Literal["fail", "allow"]] | None = None, idle: Val[str] | None = None, find_within: Val[str] | None = None, input: Val[Literal["screen", "direct"]] | None = None, max_rows: Val[int] | None = None, maximize: Val[bool] | None = None, handle: Val[list[Any]] | None = None, llm: Val[Any] | None = None) -> Action:
        """The `computer.run` action; requires do."""
        return Action("computer.run", {"do": do, "mode": mode, "variables": variables, "visible": visible, "screenshots": screenshots, "ai": ai, "cache": cache, "max_actions": max_actions, "on_confirmation": on_confirmation, "idle": idle, "find_within": find_within, "input": input, "max_rows": max_rows, "maximize": maximize, "handle": handle, "llm": llm})


class container:
    """`container.*` actions."""

    @staticmethod
    def run(*, command: Val[str | list[Any]] | None = None, image: Val[str] | None = None, container_name: Val[str] | None = None, platform: Val[str] | None = None, pull: Val[bool | Literal["always", "never", "missing", "fallback"]] | None = None, auto_remove: Val[bool | str] | None = None, working_dir: Val[str] | None = None, volumes: Val[list[Any]] | None = None, container: Val[dict[str, Any]] | None = None, host: Val[dict[str, Any]] | None = None, network: Val[dict[str, Any]] | None = None, exec: Val[dict[str, Any]] | None = None) -> Action:
        """The `container.run` action."""
        return Action("container.run", {"command": command, "image": image, "container_name": container_name, "platform": platform, "pull": pull, "auto_remove": auto_remove, "working_dir": working_dir, "volumes": volumes, "container": container, "host": host, "network": network, "exec": exec})


class dag:
    """`dag.*` actions."""

    @staticmethod
    def enqueue(*, dag: Val[str], params: Val[str | list[Any] | dict[str, Any]] | None = None, queue: Val[str] | None = None) -> Action:
        """The `dag.enqueue` action; requires dag."""
        return Action("dag.enqueue", {"dag": dag, "params": params, "queue": queue})

    @staticmethod
    def run(*, dag: Val[str], params: Val[str | list[Any] | dict[str, Any]] | None = None) -> Action:
        """The `dag.run` action; requires dag."""
        return Action("dag.run", {"dag": dag, "params": params})


class data:
    """`data.*` actions."""

    @staticmethod
    def convert(*, from_: Val[Literal["json", "yaml", "csv", "tsv", "text"]], to: Val[Literal["json", "yaml", "csv", "tsv", "text"]], data: Val[Any] | None = None, input: Val[str] | None = None, has_header: Val[bool] | None = None, headers: Val[bool] | None = None, delimiter: Val[str] | None = None, columns: Val[list[Any]] | None = None) -> Action:
        """The `data.convert` action; requires from_, to."""
        return Action("data.convert", {"from": from_, "to": to, "data": data, "input": input, "has_header": has_header, "headers": headers, "delimiter": delimiter, "columns": columns})

    @staticmethod
    def pick(*, from_: Val[Literal["json", "yaml", "csv", "tsv", "text"]], to: Val[Literal["json", "yaml", "csv", "tsv", "text"]] | None = None, select: Val[str], raw: Val[bool] | None = None, data: Val[Any] | None = None, input: Val[str] | None = None, has_header: Val[bool] | None = None, headers: Val[bool] | None = None, delimiter: Val[str] | None = None, columns: Val[list[Any]] | None = None) -> Action:
        """The `data.pick` action; requires from_, select."""
        return Action("data.pick", {"from": from_, "to": to, "select": select, "raw": raw, "data": data, "input": input, "has_header": has_header, "headers": headers, "delimiter": delimiter, "columns": columns})


class decision:
    """`decision.*` actions."""

    @staticmethod
    def evaluate(*, provider: Val[str], model: Val[str], base_url: Val[str] | None = None, api_key_name: Val[str] | None = None, state: Val[str | dict[str, Any] | list[Any]], questions: Val[dict[str, Any]]) -> Action:
        """The `decision.evaluate` action; requires provider, model, state, questions."""
        return Action("decision.evaluate", {"provider": provider, "model": model, "base_url": base_url, "api_key_name": api_key_name, "state": state, "questions": questions})


class docker:
    """`docker.*` actions."""

    @staticmethod
    def run(*, command: Val[str | list[Any]] | None = None, image: Val[str] | None = None, container_name: Val[str] | None = None, platform: Val[str] | None = None, pull: Val[bool | Literal["always", "never", "missing", "fallback"]] | None = None, auto_remove: Val[bool | str] | None = None, working_dir: Val[str] | None = None, volumes: Val[list[Any]] | None = None, container: Val[dict[str, Any]] | None = None, host: Val[dict[str, Any]] | None = None, network: Val[dict[str, Any]] | None = None, exec: Val[dict[str, Any]] | None = None) -> Action:
        """The `docker.run` action."""
        return Action("docker.run", {"command": command, "image": image, "container_name": container_name, "platform": platform, "pull": pull, "auto_remove": auto_remove, "working_dir": working_dir, "volumes": volumes, "container": container, "host": host, "network": network, "exec": exec})


class file:
    """`file.*` actions."""

    @staticmethod
    def copy(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.copy` action."""
        return Action("file.copy", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def delete(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.delete` action."""
        return Action("file.delete", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def list(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.list` action."""
        return Action("file.list", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def mkdir(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.mkdir` action."""
        return Action("file.mkdir", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def move(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.move` action."""
        return Action("file.move", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def read(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.read` action."""
        return Action("file.read", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def stat(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.stat` action."""
        return Action("file.stat", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})

    @staticmethod
    def write(*, path: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, content: Val[str] | None = None, mode: Val[str] | None = None, format: Val[Literal["raw", "json"]] | None = None, pattern: Val[str] | None = None, overwrite: Val[bool] | None = None, create_dirs: Val[bool] | None = None, atomic: Val[bool] | None = None, recursive: Val[bool] | None = None, missing_ok: Val[bool] | None = None, dry_run: Val[bool] | None = None, include_dirs: Val[bool] | None = None, follow_symlinks: Val[bool] | None = None, max_bytes: Val[int] | None = None) -> Action:
        """The `file.write` action."""
        return Action("file.write", {"path": path, "source": source, "destination": destination, "content": content, "mode": mode, "format": format, "pattern": pattern, "overwrite": overwrite, "create_dirs": create_dirs, "atomic": atomic, "recursive": recursive, "missing_ok": missing_ok, "dry_run": dry_run, "include_dirs": include_dirs, "follow_symlinks": follow_symlinks, "max_bytes": max_bytes})


class git:
    """`git.*` actions."""

    @staticmethod
    def checkout(*, repository: Val[str], ref: Val[str] | None = None, path: Val[str], depth: Val[int] | None = None, force: Val[bool] | None = None, token: Val[str] | None = None, username: Val[str] | None = None, password: Val[str] | None = None, ssh_key_path: Val[str] | None = None, ssh_passphrase: Val[str] | None = None) -> Action:
        """The `git.checkout` action; requires repository, path."""
        return Action("git.checkout", {"repository": repository, "ref": ref, "path": path, "depth": depth, "force": force, "token": token, "username": username, "password": password, "ssh_key_path": ssh_key_path, "ssh_passphrase": ssh_passphrase})

    @staticmethod
    def worktree_add(*, branch: Val[str] | None = None, path: Val[str] | None = None, create_branch: Val[bool] | None = None, base: Val[str] | None = None) -> Action:
        """The `git.worktree.add` action."""
        return Action("git.worktree.add", {"branch": branch, "path": path, "create_branch": create_branch, "base": base})

    @staticmethod
    def worktree_remove(*, branch: Val[str] | None = None, path: Val[str] | None = None, force: Val[bool] | None = None, delete_branch: Val[bool] | None = None, force_delete_branch: Val[bool] | None = None) -> Action:
        """The `git.worktree.remove` action."""
        return Action("git.worktree.remove", {"branch": branch, "path": path, "force": force, "delete_branch": delete_branch, "force_delete_branch": force_delete_branch})


class harness:
    """`harness.*` actions."""

    @staticmethod
    def run(*, provider: Val[str] | None = None, fallback: Val[list[Any]] | None = None, model: Val[str] | None = None, prompt: Val[str], stdin: Val[str] | None = None, **extra: Any) -> Action:
        """The `harness.run` action; requires prompt."""
        return Action("harness.run", {"provider": provider, "fallback": fallback, "model": model, "prompt": prompt, "stdin": stdin} | extra)


class http:
    """`http.*` actions."""

    @staticmethod
    def request(*, method: Val[str], url: Val[str], timeout: Val[int] | None = None, headers: Val[dict[str, Any]] | None = None, query: Val[dict[str, Any]] | None = None, body: Val[str] | None = None, form: Val[dict[str, Any]] | None = None, files: Val[dict[str, Any]] | None = None, silent: Val[bool] | None = None, debug: Val[bool] | None = None, json: Val[bool] | None = None, format: Val[Literal["json"]] | None = None, skip_tls_verify: Val[bool] | None = None, output: Val[str] | None = None) -> Action:
        """The `http.request` action; requires method, url."""
        return Action("http.request", {"method": method, "url": url, "timeout": timeout, "headers": headers, "query": query, "body": body, "form": form, "files": files, "silent": silent, "debug": debug, "json": json, "format": format, "skip_tls_verify": skip_tls_verify, "output": output})


class human:
    """`human.*` actions."""

    @staticmethod
    def task(*, prompt: Val[str], form: Val[dict[str, Any]] | None = None, artifacts: Val[list[Any]] | None = None, push_back: Val[dict[str, Any]] | None = None) -> Action:
        """The `human.task` action; requires prompt."""
        return Action("human.task", {"prompt": prompt, "form": form, "artifacts": artifacts, "push_back": push_back})


class jq:
    """`jq.*` actions."""

    @staticmethod
    def filter(*, filter: Val[str], data: Val[Any] | None = None, input: Val[str] | None = None, args: Val[dict[str, Any]] | None = None, **extra: Any) -> Action:
        """The `jq.filter` action; requires filter."""
        return Action("jq.filter", {"filter": filter, "data": data, "input": input, "args": args} | extra)


class js:
    """`js.*` actions."""

    @staticmethod
    def run(*, script: Val[str], input: Val[Any] | None = None, input_file: Val[str] | None = None, format: Val[Literal["auto", "text", "json"]] | None = None, timeout: Val[int | str] | None = None) -> Action:
        """The `js.run` action; requires script."""
        return Action("js.run", {"script": script, "input": input, "input_file": input_file, "format": format, "timeout": timeout})


class k8s:
    """`k8s.*` actions."""

    @staticmethod
    def run(*, command: Val[str | list[Any]] | None = None, image: Val[str] | None = None, namespace: Val[str] | None = None, kubeconfig: Val[str] | None = None, context: Val[str] | None = None, service_account: Val[str] | None = None, working_dir: Val[str] | None = None, image_pull_policy: Val[str] | None = None, image_pull_secrets: Val[list[Any]] | None = None, env: Val[list[Any]] | None = None, env_from: Val[list[Any]] | None = None, resources: Val[dict[str, Any]] | None = None, node_selector: Val[dict[str, Any]] | None = None, tolerations: Val[list[Any]] | None = None, security_context: Val[dict[str, Any]] | None = None, pod_security_context: Val[dict[str, Any]] | None = None, affinity: Val[dict[str, Any]] | None = None, termination_grace_period_seconds: Val[int] | None = None, priority_class_name: Val[str] | None = None, labels: Val[dict[str, Any]] | None = None, annotations: Val[dict[str, Any]] | None = None, volumes: Val[list[Any]] | None = None, volume_mounts: Val[list[Any]] | None = None, active_deadline: Val[int] | None = None, backoff_limit: Val[int] | None = None, ttl_after_finished: Val[int] | None = None, cleanup_policy: Val[str] | None = None, pod_failure_policy: Val[dict[str, Any]] | None = None) -> Action:
        """The `k8s.run` action."""
        return Action("k8s.run", {"command": command, "image": image, "namespace": namespace, "kubeconfig": kubeconfig, "context": context, "service_account": service_account, "working_dir": working_dir, "image_pull_policy": image_pull_policy, "image_pull_secrets": image_pull_secrets, "env": env, "env_from": env_from, "resources": resources, "node_selector": node_selector, "tolerations": tolerations, "security_context": security_context, "pod_security_context": pod_security_context, "affinity": affinity, "termination_grace_period_seconds": termination_grace_period_seconds, "priority_class_name": priority_class_name, "labels": labels, "annotations": annotations, "volumes": volumes, "volume_mounts": volume_mounts, "active_deadline": active_deadline, "backoff_limit": backoff_limit, "ttl_after_finished": ttl_after_finished, "cleanup_policy": cleanup_policy, "pod_failure_policy": pod_failure_policy})


class kubernetes:
    """`kubernetes.*` actions."""

    @staticmethod
    def run(*, command: Val[str | list[Any]] | None = None, image: Val[str] | None = None, namespace: Val[str] | None = None, kubeconfig: Val[str] | None = None, context: Val[str] | None = None, service_account: Val[str] | None = None, working_dir: Val[str] | None = None, image_pull_policy: Val[str] | None = None, image_pull_secrets: Val[list[Any]] | None = None, env: Val[list[Any]] | None = None, env_from: Val[list[Any]] | None = None, resources: Val[dict[str, Any]] | None = None, node_selector: Val[dict[str, Any]] | None = None, tolerations: Val[list[Any]] | None = None, security_context: Val[dict[str, Any]] | None = None, pod_security_context: Val[dict[str, Any]] | None = None, affinity: Val[dict[str, Any]] | None = None, termination_grace_period_seconds: Val[int] | None = None, priority_class_name: Val[str] | None = None, labels: Val[dict[str, Any]] | None = None, annotations: Val[dict[str, Any]] | None = None, volumes: Val[list[Any]] | None = None, volume_mounts: Val[list[Any]] | None = None, active_deadline: Val[int] | None = None, backoff_limit: Val[int] | None = None, ttl_after_finished: Val[int] | None = None, cleanup_policy: Val[str] | None = None, pod_failure_policy: Val[dict[str, Any]] | None = None) -> Action:
        """The `kubernetes.run` action."""
        return Action("kubernetes.run", {"command": command, "image": image, "namespace": namespace, "kubeconfig": kubeconfig, "context": context, "service_account": service_account, "working_dir": working_dir, "image_pull_policy": image_pull_policy, "image_pull_secrets": image_pull_secrets, "env": env, "env_from": env_from, "resources": resources, "node_selector": node_selector, "tolerations": tolerations, "security_context": security_context, "pod_security_context": pod_security_context, "affinity": affinity, "termination_grace_period_seconds": termination_grace_period_seconds, "priority_class_name": priority_class_name, "labels": labels, "annotations": annotations, "volumes": volumes, "volume_mounts": volume_mounts, "active_deadline": active_deadline, "backoff_limit": backoff_limit, "ttl_after_finished": ttl_after_finished, "cleanup_policy": cleanup_policy, "pod_failure_policy": pod_failure_policy})


class log:
    """`log.*` actions."""

    @staticmethod
    def write(*, message: Val[str]) -> Action:
        """The `log.write` action; requires message."""
        return Action("log.write", {"message": message})


class mail:
    """`mail.*` actions."""

    @staticmethod
    def organize(*, mailbox: Val[str], emails: Val[Any], mark: Val[Literal["read", "unread", "flagged", "unflagged"]] | None = None, move: Val[Literal["folder", "archive", "trash"]] | None = None, folder: Val[str] | None = None, dry_run: Val[bool | str] | None = None) -> Action:
        """The `mail.organize` action; requires mailbox, emails."""
        return Action("mail.organize", {"mailbox": mailbox, "emails": emails, "mark": mark, "move": move, "folder": folder, "dry_run": dry_run})

    @staticmethod
    def search(*, mailbox: Val[str], folder: Val[str] | None = None, unread: Val[bool | str] | None = None, from_: Val[str] | None = None, subject: Val[str] | None = None, within: Val[str] | None = None, has_attachments: Val[bool | str] | None = None, save_attachments: Val[bool | str] | None = None, limit: Val[int | str] | None = None) -> Action:
        """The `mail.search` action; requires mailbox."""
        return Action("mail.search", {"mailbox": mailbox, "folder": folder, "unread": unread, "from": from_, "subject": subject, "within": within, "has_attachments": has_attachments, "save_attachments": save_attachments, "limit": limit})

    @staticmethod
    def send(*, mailbox: Val[str] | None = None, in_reply_to: Val[str | dict[str, Any]] | None = None, from_: Val[str] | None = None, to: Val[str | list[Any]] | None = None, subject: Val[str] | None = None, message: Val[str], attachments: Val[list[Any]] | None = None) -> Action:
        """The `mail.send` action; requires message."""
        return Action("mail.send", {"mailbox": mailbox, "in_reply_to": in_reply_to, "from": from_, "to": to, "subject": subject, "message": message, "attachments": attachments})


class outputs:
    """`outputs.*` actions."""

    @staticmethod
    def write(*, values: Val[dict[str, Any]]) -> Action:
        """The `outputs.write` action; requires values."""
        return Action("outputs.write", {"values": values})


class postgres:
    """`postgres.*` actions."""

    @staticmethod
    def import_(*, import_: Val[dict[str, Any]], **extra: Any) -> Action:
        """The `postgres.import` action; requires import_."""
        return Action("postgres.import", {"import": import_} | extra)

    @staticmethod
    def query(*, query: Val[str], **extra: Any) -> Action:
        """The `postgres.query` action; requires query."""
        return Action("postgres.query", {"query": query} | extra)


class router:
    """`router.*` actions."""

    @staticmethod
    def route(*, value: Val[str], routes: Val[dict[str, Any]]) -> Action:
        """The `router.route` action; requires value, routes."""
        return Action("router.route", {"value": value, "routes": routes})


class s3:
    """`s3.*` actions."""

    @staticmethod
    def delete(*, region: Val[str] | None = None, endpoint: Val[str] | None = None, access_key_id: Val[str] | None = None, secret_access_key: Val[str] | None = None, session_token: Val[str] | None = None, profile: Val[str] | None = None, bucket: Val[str] | None = None, force_path_style: Val[bool] | None = None, disable_ssl: Val[bool] | None = None, key: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, prefix: Val[str] | None = None, content_type: Val[str] | None = None, storage_class: Val[Literal["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]] | None = None, metadata: Val[dict[str, Any]] | None = None, tags: Val[dict[str, Any]] | None = None, sse: Val[Literal["AES256", "aws:kms"]] | None = None, sse_kms_key_id: Val[str] | None = None, acl: Val[Literal["private", "public-read", "public-read-write", "authenticated-read", "aws-exec-read", "bucket-owner-read", "bucket-owner-full-control"]] | None = None, part_size: Val[int] | None = None, concurrency: Val[int] | None = None, max_keys: Val[int] | None = None, delimiter: Val[str] | None = None, recursive: Val[bool] | None = None, output_format: Val[Literal["json", "jsonl"]] | None = None, quiet: Val[bool] | None = None, **extra: Any) -> Action:
        """The `s3.delete` action."""
        return Action("s3.delete", {"region": region, "endpoint": endpoint, "access_key_id": access_key_id, "secret_access_key": secret_access_key, "session_token": session_token, "profile": profile, "bucket": bucket, "force_path_style": force_path_style, "disable_ssl": disable_ssl, "key": key, "source": source, "destination": destination, "prefix": prefix, "content_type": content_type, "storage_class": storage_class, "metadata": metadata, "tags": tags, "sse": sse, "sse_kms_key_id": sse_kms_key_id, "acl": acl, "part_size": part_size, "concurrency": concurrency, "max_keys": max_keys, "delimiter": delimiter, "recursive": recursive, "output_format": output_format, "quiet": quiet} | extra)

    @staticmethod
    def download(*, region: Val[str] | None = None, endpoint: Val[str] | None = None, access_key_id: Val[str] | None = None, secret_access_key: Val[str] | None = None, session_token: Val[str] | None = None, profile: Val[str] | None = None, bucket: Val[str] | None = None, force_path_style: Val[bool] | None = None, disable_ssl: Val[bool] | None = None, key: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, prefix: Val[str] | None = None, content_type: Val[str] | None = None, storage_class: Val[Literal["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]] | None = None, metadata: Val[dict[str, Any]] | None = None, tags: Val[dict[str, Any]] | None = None, sse: Val[Literal["AES256", "aws:kms"]] | None = None, sse_kms_key_id: Val[str] | None = None, acl: Val[Literal["private", "public-read", "public-read-write", "authenticated-read", "aws-exec-read", "bucket-owner-read", "bucket-owner-full-control"]] | None = None, part_size: Val[int] | None = None, concurrency: Val[int] | None = None, max_keys: Val[int] | None = None, delimiter: Val[str] | None = None, recursive: Val[bool] | None = None, output_format: Val[Literal["json", "jsonl"]] | None = None, quiet: Val[bool] | None = None, **extra: Any) -> Action:
        """The `s3.download` action."""
        return Action("s3.download", {"region": region, "endpoint": endpoint, "access_key_id": access_key_id, "secret_access_key": secret_access_key, "session_token": session_token, "profile": profile, "bucket": bucket, "force_path_style": force_path_style, "disable_ssl": disable_ssl, "key": key, "source": source, "destination": destination, "prefix": prefix, "content_type": content_type, "storage_class": storage_class, "metadata": metadata, "tags": tags, "sse": sse, "sse_kms_key_id": sse_kms_key_id, "acl": acl, "part_size": part_size, "concurrency": concurrency, "max_keys": max_keys, "delimiter": delimiter, "recursive": recursive, "output_format": output_format, "quiet": quiet} | extra)

    @staticmethod
    def list(*, region: Val[str] | None = None, endpoint: Val[str] | None = None, access_key_id: Val[str] | None = None, secret_access_key: Val[str] | None = None, session_token: Val[str] | None = None, profile: Val[str] | None = None, bucket: Val[str] | None = None, force_path_style: Val[bool] | None = None, disable_ssl: Val[bool] | None = None, key: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, prefix: Val[str] | None = None, content_type: Val[str] | None = None, storage_class: Val[Literal["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]] | None = None, metadata: Val[dict[str, Any]] | None = None, tags: Val[dict[str, Any]] | None = None, sse: Val[Literal["AES256", "aws:kms"]] | None = None, sse_kms_key_id: Val[str] | None = None, acl: Val[Literal["private", "public-read", "public-read-write", "authenticated-read", "aws-exec-read", "bucket-owner-read", "bucket-owner-full-control"]] | None = None, part_size: Val[int] | None = None, concurrency: Val[int] | None = None, max_keys: Val[int] | None = None, delimiter: Val[str] | None = None, recursive: Val[bool] | None = None, output_format: Val[Literal["json", "jsonl"]] | None = None, quiet: Val[bool] | None = None, **extra: Any) -> Action:
        """The `s3.list` action."""
        return Action("s3.list", {"region": region, "endpoint": endpoint, "access_key_id": access_key_id, "secret_access_key": secret_access_key, "session_token": session_token, "profile": profile, "bucket": bucket, "force_path_style": force_path_style, "disable_ssl": disable_ssl, "key": key, "source": source, "destination": destination, "prefix": prefix, "content_type": content_type, "storage_class": storage_class, "metadata": metadata, "tags": tags, "sse": sse, "sse_kms_key_id": sse_kms_key_id, "acl": acl, "part_size": part_size, "concurrency": concurrency, "max_keys": max_keys, "delimiter": delimiter, "recursive": recursive, "output_format": output_format, "quiet": quiet} | extra)

    @staticmethod
    def upload(*, region: Val[str] | None = None, endpoint: Val[str] | None = None, access_key_id: Val[str] | None = None, secret_access_key: Val[str] | None = None, session_token: Val[str] | None = None, profile: Val[str] | None = None, bucket: Val[str] | None = None, force_path_style: Val[bool] | None = None, disable_ssl: Val[bool] | None = None, key: Val[str] | None = None, source: Val[str] | None = None, destination: Val[str] | None = None, prefix: Val[str] | None = None, content_type: Val[str] | None = None, storage_class: Val[Literal["STANDARD", "REDUCED_REDUNDANCY", "STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]] | None = None, metadata: Val[dict[str, Any]] | None = None, tags: Val[dict[str, Any]] | None = None, sse: Val[Literal["AES256", "aws:kms"]] | None = None, sse_kms_key_id: Val[str] | None = None, acl: Val[Literal["private", "public-read", "public-read-write", "authenticated-read", "aws-exec-read", "bucket-owner-read", "bucket-owner-full-control"]] | None = None, part_size: Val[int] | None = None, concurrency: Val[int] | None = None, max_keys: Val[int] | None = None, delimiter: Val[str] | None = None, recursive: Val[bool] | None = None, output_format: Val[Literal["json", "jsonl"]] | None = None, quiet: Val[bool] | None = None, **extra: Any) -> Action:
        """The `s3.upload` action."""
        return Action("s3.upload", {"region": region, "endpoint": endpoint, "access_key_id": access_key_id, "secret_access_key": secret_access_key, "session_token": session_token, "profile": profile, "bucket": bucket, "force_path_style": force_path_style, "disable_ssl": disable_ssl, "key": key, "source": source, "destination": destination, "prefix": prefix, "content_type": content_type, "storage_class": storage_class, "metadata": metadata, "tags": tags, "sse": sse, "sse_kms_key_id": sse_kms_key_id, "acl": acl, "part_size": part_size, "concurrency": concurrency, "max_keys": max_keys, "delimiter": delimiter, "recursive": recursive, "output_format": output_format, "quiet": quiet} | extra)


class sftp:
    """`sftp.*` actions."""

    @staticmethod
    def download(*, user: Val[str] | None = None, host: Val[str] | None = None, ip: Val[str] | None = None, port: Val[str | int] | None = None, key: Val[str] | None = None, password: Val[str] | None = None, strict_host_key: Val[bool] | None = None, known_host_file: Val[str] | None = None, timeout: Val[str] | None = None, direction: Val[Literal["upload", "download"]] | None = None, source: Val[str], destination: Val[str], bastion: Val[dict[str, Any]] | None = None) -> Action:
        """The `sftp.download` action; requires source, destination."""
        return Action("sftp.download", {"user": user, "host": host, "ip": ip, "port": port, "key": key, "password": password, "strict_host_key": strict_host_key, "known_host_file": known_host_file, "timeout": timeout, "direction": direction, "source": source, "destination": destination, "bastion": bastion})

    @staticmethod
    def upload(*, user: Val[str] | None = None, host: Val[str] | None = None, ip: Val[str] | None = None, port: Val[str | int] | None = None, key: Val[str] | None = None, password: Val[str] | None = None, strict_host_key: Val[bool] | None = None, known_host_file: Val[str] | None = None, timeout: Val[str] | None = None, direction: Val[Literal["upload", "download"]] | None = None, source: Val[str], destination: Val[str], bastion: Val[dict[str, Any]] | None = None) -> Action:
        """The `sftp.upload` action; requires source, destination."""
        return Action("sftp.upload", {"user": user, "host": host, "ip": ip, "port": port, "key": key, "password": password, "strict_host_key": strict_host_key, "known_host_file": known_host_file, "timeout": timeout, "direction": direction, "source": source, "destination": destination, "bastion": bastion})


class sqlite:
    """`sqlite.*` actions."""

    @staticmethod
    def import_(*, import_: Val[dict[str, Any]], **extra: Any) -> Action:
        """The `sqlite.import` action; requires import_."""
        return Action("sqlite.import", {"import": import_} | extra)

    @staticmethod
    def query(*, query: Val[str], **extra: Any) -> Action:
        """The `sqlite.query` action; requires query."""
        return Action("sqlite.query", {"query": query} | extra)


class ssh:
    """`ssh.*` actions."""

    @staticmethod
    def run(*, user: Val[str] | None = None, host: Val[str] | None = None, ip: Val[str] | None = None, port: Val[str | int] | None = None, key: Val[str] | None = None, password: Val[str] | None = None, strict_host_key: Val[bool] | None = None, known_host_file: Val[str] | None = None, shell: Val[str | list[Any]] | None = None, command: Val[str], **extra: Any) -> Action:
        """The `ssh.run` action; requires command."""
        return Action("ssh.run", {"user": user, "host": host, "ip": ip, "port": port, "key": key, "password": password, "strict_host_key": strict_host_key, "known_host_file": known_host_file, "shell": shell, "command": command} | extra)


class state:
    """`state.*` actions."""

    @staticmethod
    def delete(*, scope: Val[Literal["dag", "root_dag", "global", "custom"]] | None = None, namespace: Val[str] | None = None, key: Val[str], prefix: Val[str] | None = None, value: Val[Any] | None = None, default: Val[Any] | None = None, expected_version: Val[int] | None = None, create_only: Val[bool] | None = None, required: Val[bool] | None = None, update: Val[bool] | None = None, limit: Val[int] | None = None, include_values: Val[bool] | None = None) -> Action:
        """The `state.delete` action; requires key."""
        return Action("state.delete", {"scope": scope, "namespace": namespace, "key": key, "prefix": prefix, "value": value, "default": default, "expected_version": expected_version, "create_only": create_only, "required": required, "update": update, "limit": limit, "include_values": include_values})

    @staticmethod
    def diff(*, scope: Val[Literal["dag", "root_dag", "global", "custom"]] | None = None, namespace: Val[str] | None = None, key: Val[str], prefix: Val[str] | None = None, value: Val[Any], default: Val[Any] | None = None, expected_version: Val[int] | None = None, create_only: Val[bool] | None = None, required: Val[bool] | None = None, update: Val[bool] | None = None, limit: Val[int] | None = None, include_values: Val[bool] | None = None) -> Action:
        """The `state.diff` action; requires key, value."""
        return Action("state.diff", {"scope": scope, "namespace": namespace, "key": key, "prefix": prefix, "value": value, "default": default, "expected_version": expected_version, "create_only": create_only, "required": required, "update": update, "limit": limit, "include_values": include_values})

    @staticmethod
    def get(*, scope: Val[Literal["dag", "root_dag", "global", "custom"]] | None = None, namespace: Val[str] | None = None, key: Val[str], prefix: Val[str] | None = None, value: Val[Any] | None = None, default: Val[Any] | None = None, expected_version: Val[int] | None = None, create_only: Val[bool] | None = None, required: Val[bool] | None = None, update: Val[bool] | None = None, limit: Val[int] | None = None, include_values: Val[bool] | None = None) -> Action:
        """The `state.get` action; requires key."""
        return Action("state.get", {"scope": scope, "namespace": namespace, "key": key, "prefix": prefix, "value": value, "default": default, "expected_version": expected_version, "create_only": create_only, "required": required, "update": update, "limit": limit, "include_values": include_values})

    @staticmethod
    def list(*, scope: Val[Literal["dag", "root_dag", "global", "custom"]] | None = None, namespace: Val[str] | None = None, key: Val[str] | None = None, prefix: Val[str] | None = None, value: Val[Any] | None = None, default: Val[Any] | None = None, expected_version: Val[int] | None = None, create_only: Val[bool] | None = None, required: Val[bool] | None = None, update: Val[bool] | None = None, limit: Val[int] | None = None, include_values: Val[bool] | None = None) -> Action:
        """The `state.list` action."""
        return Action("state.list", {"scope": scope, "namespace": namespace, "key": key, "prefix": prefix, "value": value, "default": default, "expected_version": expected_version, "create_only": create_only, "required": required, "update": update, "limit": limit, "include_values": include_values})

    @staticmethod
    def set(*, scope: Val[Literal["dag", "root_dag", "global", "custom"]] | None = None, namespace: Val[str] | None = None, key: Val[str], prefix: Val[str] | None = None, value: Val[Any], default: Val[Any] | None = None, expected_version: Val[int] | None = None, create_only: Val[bool] | None = None, required: Val[bool] | None = None, update: Val[bool] | None = None, limit: Val[int] | None = None, include_values: Val[bool] | None = None) -> Action:
        """The `state.set` action; requires key, value."""
        return Action("state.set", {"scope": scope, "namespace": namespace, "key": key, "prefix": prefix, "value": value, "default": default, "expected_version": expected_version, "create_only": create_only, "required": required, "update": update, "limit": limit, "include_values": include_values})


class template:
    """`template.*` actions."""

    @staticmethod
    def render(*, template: Val[str] | None = None, template_ref: Val[str] | None = None, **extra: Any) -> Action:
        """The `template.render` action."""
        return Action("template.render", {"template": template, "template_ref": template_ref} | extra)


class wait:
    """`wait.*` actions."""

    @staticmethod
    def duration(*, duration: Val[str] | None = None, until: Val[str] | None = None, offset: Val[str] | None = None, timezone: Val[str] | None = None, if_past: Val[str] | None = None, window: Val[str] | None = None, path: Val[str] | None = None, state: Val[str] | None = None, url: Val[str] | None = None, method: Val[str] | None = None, status: Val[int | str] | None = None, headers: Val[dict[str, Any]] | None = None, body: Val[str] | None = None, poll_interval: Val[str] | None = None, request_timeout: Val[str] | None = None) -> Action:
        """The `wait.duration` action."""
        return Action("wait.duration", {"duration": duration, "until": until, "offset": offset, "timezone": timezone, "if_past": if_past, "window": window, "path": path, "state": state, "url": url, "method": method, "status": status, "headers": headers, "body": body, "poll_interval": poll_interval, "request_timeout": request_timeout})

    @staticmethod
    def file(*, duration: Val[str] | None = None, until: Val[str] | None = None, offset: Val[str] | None = None, timezone: Val[str] | None = None, if_past: Val[str] | None = None, window: Val[str] | None = None, path: Val[str] | None = None, state: Val[str] | None = None, url: Val[str] | None = None, method: Val[str] | None = None, status: Val[int | str] | None = None, headers: Val[dict[str, Any]] | None = None, body: Val[str] | None = None, poll_interval: Val[str] | None = None, request_timeout: Val[str] | None = None) -> Action:
        """The `wait.file` action."""
        return Action("wait.file", {"duration": duration, "until": until, "offset": offset, "timezone": timezone, "if_past": if_past, "window": window, "path": path, "state": state, "url": url, "method": method, "status": status, "headers": headers, "body": body, "poll_interval": poll_interval, "request_timeout": request_timeout})

    @staticmethod
    def http(*, duration: Val[str] | None = None, until: Val[str] | None = None, offset: Val[str] | None = None, timezone: Val[str] | None = None, if_past: Val[str] | None = None, window: Val[str] | None = None, path: Val[str] | None = None, state: Val[str] | None = None, url: Val[str] | None = None, method: Val[str] | None = None, status: Val[int | str] | None = None, headers: Val[dict[str, Any]] | None = None, body: Val[str] | None = None, poll_interval: Val[str] | None = None, request_timeout: Val[str] | None = None) -> Action:
        """The `wait.http` action."""
        return Action("wait.http", {"duration": duration, "until": until, "offset": offset, "timezone": timezone, "if_past": if_past, "window": window, "path": path, "state": state, "url": url, "method": method, "status": status, "headers": headers, "body": body, "poll_interval": poll_interval, "request_timeout": request_timeout})

    @staticmethod
    def until(*, duration: Val[str] | None = None, until: Val[str] | None = None, offset: Val[str] | None = None, timezone: Val[str] | None = None, if_past: Val[str] | None = None, window: Val[str] | None = None, path: Val[str] | None = None, state: Val[str] | None = None, url: Val[str] | None = None, method: Val[str] | None = None, status: Val[int | str] | None = None, headers: Val[dict[str, Any]] | None = None, body: Val[str] | None = None, poll_interval: Val[str] | None = None, request_timeout: Val[str] | None = None) -> Action:
        """The `wait.until` action."""
        return Action("wait.until", {"duration": duration, "until": until, "offset": offset, "timezone": timezone, "if_past": if_past, "window": window, "path": path, "state": state, "url": url, "method": method, "status": status, "headers": headers, "body": body, "poll_interval": poll_interval, "request_timeout": request_timeout})


class xlsx:
    """`xlsx.*` actions."""

    @staticmethod
    def append(**extra: Any) -> Action:
        """The `xlsx.append` action."""
        return Action("xlsx.append", dict(extra))

    @staticmethod
    def convert(**extra: Any) -> Action:
        """The `xlsx.convert` action."""
        return Action("xlsx.convert", dict(extra))

    @staticmethod
    def extract(**extra: Any) -> Action:
        """The `xlsx.extract` action."""
        return Action("xlsx.extract", dict(extra))

    @staticmethod
    def info(*, path: Val[str], password: Val[str] | None = None, sheet: Val[str] | None = None, range: Val[str] | None = None, header: Val[bool | int | list[Any] | str] | None = None, columns: Val[list[Any] | str] | None = None, merged: Val[Literal["fill", "first"]] | None = None, stop_at_blank: Val[bool | str] | None = None, keep_empty_rows: Val[bool | str] | None = None, skip_hidden: Val[bool | str] | None = None, trim: Val[bool | str] | None = None, formulas: Val[Literal["cached", "text", "calculate"]] | None = None, types: Val[dict[str, Any]] | None = None, on_type_error: Val[Any] | None = None, where: Val[dict[str, Any]] | None = None, max_rows: Val[int | str] | None = None, rows: Val[list[Any] | str] | None = None, input: Val[str] | None = None, format: Val[Literal["json", "jsonl", "csv"]] | None = None, mode: Val[Literal["replace", "append"]] | None = None, style: Val[Literal["table", "none"]] | None = None, atomic: Val[bool | str] | None = None, dry_run: Val[bool | str] | None = None, wait_for_unlock: Val[str] | None = None, key: Val[str] | None = None, set: Val[dict[str, Any]] | None = None, missing: Val[Literal["fail", "skip", "append"]] | None = None, artifact: Val[bool | str] | None = None, required: Val[list[Any] | str] | None = None, not_blank: Val[list[Any] | str] | None = None, unique: Val[list[Any] | str] | None = None, allowed: Val[dict[str, Any]] | None = None, on_problem: Val[Literal["warn", "fail"]] | None = None, max_problems: Val[int | str] | None = None, cells: Val[dict[str, Any]] | None = None, merge: Val[list[Any] | str] | None = None, output: Val[str] | None = None, operation: Val[Literal["add", "copy", "rename", "delete"]] | None = None, to: Val[str] | None = None, if_exists: Val[Literal["fail", "skip", "replace"]] | None = None, position: Val[int | str] | None = None, encoding: Val[Literal["utf-8", "utf-8-bom", "shift_jis", "cp932", "windows-31j", "sjis", "ms932"]] | None = None, delimiter: Val[str] | None = None, instruction: Val[str] | None = None, schema: Val[dict[str, Any] | str] | None = None, send_values: Val[bool | str] | None = None, cache: Val[bool | str] | None = None, llm: Val[Any] | None = None) -> Action:
        """The `xlsx.info` action; requires path."""
        return Action("xlsx.info", {"path": path, "password": password, "sheet": sheet, "range": range, "header": header, "columns": columns, "merged": merged, "stop_at_blank": stop_at_blank, "keep_empty_rows": keep_empty_rows, "skip_hidden": skip_hidden, "trim": trim, "formulas": formulas, "types": types, "on_type_error": on_type_error, "where": where, "max_rows": max_rows, "rows": rows, "input": input, "format": format, "mode": mode, "style": style, "atomic": atomic, "dry_run": dry_run, "wait_for_unlock": wait_for_unlock, "key": key, "set": set, "missing": missing, "artifact": artifact, "required": required, "not_blank": not_blank, "unique": unique, "allowed": allowed, "on_problem": on_problem, "max_problems": max_problems, "cells": cells, "merge": merge, "output": output, "operation": operation, "to": to, "if_exists": if_exists, "position": position, "encoding": encoding, "delimiter": delimiter, "instruction": instruction, "schema": schema, "send_values": send_values, "cache": cache, "llm": llm})

    @staticmethod
    def list_sheets(*, path: Val[str], password: Val[str] | None = None, sheet: Val[str] | None = None, range: Val[str] | None = None, header: Val[bool | int | list[Any] | str] | None = None, columns: Val[list[Any] | str] | None = None, merged: Val[Literal["fill", "first"]] | None = None, stop_at_blank: Val[bool | str] | None = None, keep_empty_rows: Val[bool | str] | None = None, skip_hidden: Val[bool | str] | None = None, trim: Val[bool | str] | None = None, formulas: Val[Literal["cached", "text", "calculate"]] | None = None, types: Val[dict[str, Any]] | None = None, on_type_error: Val[Any] | None = None, where: Val[dict[str, Any]] | None = None, max_rows: Val[int | str] | None = None, rows: Val[list[Any] | str] | None = None, input: Val[str] | None = None, format: Val[Literal["json", "jsonl", "csv"]] | None = None, mode: Val[Literal["replace", "append"]] | None = None, style: Val[Literal["table", "none"]] | None = None, atomic: Val[bool | str] | None = None, dry_run: Val[bool | str] | None = None, wait_for_unlock: Val[str] | None = None, key: Val[str] | None = None, set: Val[dict[str, Any]] | None = None, missing: Val[Literal["fail", "skip", "append"]] | None = None, artifact: Val[bool | str] | None = None, required: Val[list[Any] | str] | None = None, not_blank: Val[list[Any] | str] | None = None, unique: Val[list[Any] | str] | None = None, allowed: Val[dict[str, Any]] | None = None, on_problem: Val[Literal["warn", "fail"]] | None = None, max_problems: Val[int | str] | None = None, cells: Val[dict[str, Any]] | None = None, merge: Val[list[Any] | str] | None = None, output: Val[str] | None = None, operation: Val[Literal["add", "copy", "rename", "delete"]] | None = None, to: Val[str] | None = None, if_exists: Val[Literal["fail", "skip", "replace"]] | None = None, position: Val[int | str] | None = None, encoding: Val[Literal["utf-8", "utf-8-bom", "shift_jis", "cp932", "windows-31j", "sjis", "ms932"]] | None = None, delimiter: Val[str] | None = None, instruction: Val[str] | None = None, schema: Val[dict[str, Any] | str] | None = None, send_values: Val[bool | str] | None = None, cache: Val[bool | str] | None = None, llm: Val[Any] | None = None) -> Action:
        """The `xlsx.list_sheets` action; requires path."""
        return Action("xlsx.list_sheets", {"path": path, "password": password, "sheet": sheet, "range": range, "header": header, "columns": columns, "merged": merged, "stop_at_blank": stop_at_blank, "keep_empty_rows": keep_empty_rows, "skip_hidden": skip_hidden, "trim": trim, "formulas": formulas, "types": types, "on_type_error": on_type_error, "where": where, "max_rows": max_rows, "rows": rows, "input": input, "format": format, "mode": mode, "style": style, "atomic": atomic, "dry_run": dry_run, "wait_for_unlock": wait_for_unlock, "key": key, "set": set, "missing": missing, "artifact": artifact, "required": required, "not_blank": not_blank, "unique": unique, "allowed": allowed, "on_problem": on_problem, "max_problems": max_problems, "cells": cells, "merge": merge, "output": output, "operation": operation, "to": to, "if_exists": if_exists, "position": position, "encoding": encoding, "delimiter": delimiter, "instruction": instruction, "schema": schema, "send_values": send_values, "cache": cache, "llm": llm})

    @staticmethod
    def read(*, path: Val[str], password: Val[str] | None = None, sheet: Val[str] | None = None, range: Val[str] | None = None, header: Val[bool | int | list[Any] | str] | None = None, columns: Val[list[Any] | str] | None = None, merged: Val[Literal["fill", "first"]] | None = None, stop_at_blank: Val[bool | str] | None = None, keep_empty_rows: Val[bool | str] | None = None, skip_hidden: Val[bool | str] | None = None, trim: Val[bool | str] | None = None, formulas: Val[Literal["cached", "text", "calculate"]] | None = None, types: Val[dict[str, Any]] | None = None, on_type_error: Val[Any] | None = None, where: Val[dict[str, Any]] | None = None, max_rows: Val[int | str] | None = None, rows: Val[list[Any] | str] | None = None, input: Val[str] | None = None, format: Val[Literal["json", "jsonl", "csv"]] | None = None, mode: Val[Literal["replace", "append"]] | None = None, style: Val[Literal["table", "none"]] | None = None, atomic: Val[bool | str] | None = None, dry_run: Val[bool | str] | None = None, wait_for_unlock: Val[str] | None = None, key: Val[str] | None = None, set: Val[dict[str, Any]] | None = None, missing: Val[Literal["fail", "skip", "append"]] | None = None, artifact: Val[bool | str] | None = None, required: Val[list[Any] | str] | None = None, not_blank: Val[list[Any] | str] | None = None, unique: Val[list[Any] | str] | None = None, allowed: Val[dict[str, Any]] | None = None, on_problem: Val[Literal["warn", "fail"]] | None = None, max_problems: Val[int | str] | None = None, cells: Val[dict[str, Any]] | None = None, merge: Val[list[Any] | str] | None = None, output: Val[str] | None = None, operation: Val[Literal["add", "copy", "rename", "delete"]] | None = None, to: Val[str] | None = None, if_exists: Val[Literal["fail", "skip", "replace"]] | None = None, position: Val[int | str] | None = None, encoding: Val[Literal["utf-8", "utf-8-bom", "shift_jis", "cp932", "windows-31j", "sjis", "ms932"]] | None = None, delimiter: Val[str] | None = None, instruction: Val[str] | None = None, schema: Val[dict[str, Any] | str] | None = None, send_values: Val[bool | str] | None = None, cache: Val[bool | str] | None = None, llm: Val[Any] | None = None) -> Action:
        """The `xlsx.read` action; requires path."""
        return Action("xlsx.read", {"path": path, "password": password, "sheet": sheet, "range": range, "header": header, "columns": columns, "merged": merged, "stop_at_blank": stop_at_blank, "keep_empty_rows": keep_empty_rows, "skip_hidden": skip_hidden, "trim": trim, "formulas": formulas, "types": types, "on_type_error": on_type_error, "where": where, "max_rows": max_rows, "rows": rows, "input": input, "format": format, "mode": mode, "style": style, "atomic": atomic, "dry_run": dry_run, "wait_for_unlock": wait_for_unlock, "key": key, "set": set, "missing": missing, "artifact": artifact, "required": required, "not_blank": not_blank, "unique": unique, "allowed": allowed, "on_problem": on_problem, "max_problems": max_problems, "cells": cells, "merge": merge, "output": output, "operation": operation, "to": to, "if_exists": if_exists, "position": position, "encoding": encoding, "delimiter": delimiter, "instruction": instruction, "schema": schema, "send_values": send_values, "cache": cache, "llm": llm})

    @staticmethod
    def sheet(**extra: Any) -> Action:
        """The `xlsx.sheet` action."""
        return Action("xlsx.sheet", dict(extra))

    @staticmethod
    def update_rows(**extra: Any) -> Action:
        """The `xlsx.update_rows` action."""
        return Action("xlsx.update_rows", dict(extra))

    @staticmethod
    def validate(**extra: Any) -> Action:
        """The `xlsx.validate` action."""
        return Action("xlsx.validate", dict(extra))

    @staticmethod
    def write(**extra: Any) -> Action:
        """The `xlsx.write` action."""
        return Action("xlsx.write", dict(extra))

    @staticmethod
    def write_cells(**extra: Any) -> Action:
        """The `xlsx.write_cells` action."""
        return Action("xlsx.write_cells", dict(extra))


__all__ = ["archive", "artifact", "browser", "chat", "clickhouse", "computer", "container", "dag", "data", "decision", "docker", "exec_", "file", "git", "harness", "http", "human", "jq", "js", "k8s", "kubernetes", "log", "mail", "noop", "outputs", "postgres", "router", "s3", "sftp", "sqlite", "ssh", "state", "template", "wait", "xlsx"]
