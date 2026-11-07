from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DAGU_BIN = os.environ.get("DAGUFLOW_DAGU_BIN")


@pytest.fixture(autouse=True)
def _fresh_registry():
    from daguflow.dag import clear_registry

    yield
    clear_registry()


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def dagu_bin() -> str:
    if not DAGU_BIN:
        pytest.skip("DAGUFLOW_DAGU_BIN not set")
    return DAGU_BIN


@pytest.fixture(scope="session")
def built_examples(tmp_path_factory) -> Path:
    from daguflow.cli import main

    out = tmp_path_factory.mktemp("dags")
    assert main(["build", str(REPO / "examples"), "-o", str(out), "--root", str(REPO)]) == 0
    return out


@pytest.fixture(scope="session")
def dagu_server(dagu_bin, built_examples, tmp_path_factory):
    """A real dagu (the pinned release) serving the built examples."""
    from daguflow.client import Client

    home = tmp_path_factory.mktemp("dagu-home")
    port = _free_port()
    config = home / "config.yaml"
    config.write_text(
        f"host: 127.0.0.1\nport: {port}\napi_base_path: /api/v1\nauth:\n  mode: none\n"
        f"paths:\n  dags_dir: {built_examples}\n  data_dir: {home}/data\n  log_dir: {home}/logs\n"
    )
    log = (home / "server.log").open("w")
    env = {**os.environ, "DAGU_HOME": str(home)}
    proc = subprocess.Popen([dagu_bin, "start-all", "--config", str(config)], stdout=log,
                            stderr=subprocess.STDOUT, env=env)
    client = Client(f"http://127.0.0.1:{port}/api/v1")
    deadline = time.monotonic() + 60
    while True:
        try:
            if client.health().get("status") == "healthy":
                break
        except Exception:
            pass
        if proc.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("dagu did not start:\n" + (home / "server.log").read_text()[-3000:])
        time.sleep(0.3)
    try:
        yield client
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        client.close()


@pytest.fixture(scope="session")
def sshd(tmp_path_factory):
    """A throwaway sshd on 127.0.0.1 with all three host-key types pinned.

    dagu's Go client picks the host-key algorithm the server prefers and
    answers "key mismatch" when known_hosts lacks that type, so the pin file
    carries ed25519, ecdsa and rsa, as production's does.
    """
    import getpass
    import shutil
    from types import SimpleNamespace

    sshd_bin = shutil.which("sshd") or ("/usr/sbin/sshd" if Path("/usr/sbin/sshd").exists() else None)
    if not sshd_bin or not shutil.which("ssh-keygen"):
        pytest.skip("openssh-server not installed")
    root = tmp_path_factory.mktemp("sshd")
    for kind in ("ed25519", "ecdsa", "rsa"):
        subprocess.run(["ssh-keygen", "-q", "-t", kind, "-N", "", "-f", str(root / f"host_{kind}")], check=True)
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(root / "client")], check=True)
    (root / "authorized_keys").write_text((root / "client.pub").read_text())
    port = _free_port()
    config = root / "sshd_config"
    config.write_text("\n".join([
        f"Port {port}", "ListenAddress 127.0.0.1",
        *(f"HostKey {root}/host_{k}" for k in ("ed25519", "ecdsa", "rsa")),
        f"AuthorizedKeysFile {root}/authorized_keys", "PasswordAuthentication no",
        "KbdInteractiveAuthentication no", "UsePAM no", "StrictModes no", "PermitRootLogin yes",
        f"PidFile {root}/sshd.pid", "",
    ]))
    known = "".join(f"[127.0.0.1]:{port} " + " ".join((root / f"host_{k}.pub").read_text().split()[:2]) + "\n"
                    for k in ("ed25519", "ecdsa", "rsa"))
    (root / "known_hosts").write_text(known)
    Path("/run/sshd").mkdir(mode=0o755, exist_ok=True)  # sshd's privilege-separation dir
    proc = subprocess.Popen([sshd_bin, "-D", "-e", "-f", str(config)], stderr=(root / "sshd.log").open("w"))
    deadline = time.monotonic() + 20
    while True:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break
        if proc.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("sshd did not start: " + (root / "sshd.log").read_text())
        time.sleep(0.1)
    try:
        yield SimpleNamespace(port=port, user=getpass.getuser(), key=str(root / "client"),
                              known_hosts=str(root / "known_hosts"))
    finally:
        proc.terminate()
        proc.wait(timeout=10)
