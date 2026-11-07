"""Lights over SSH, the shape of a real home-automation DAG set."""

from typing import Annotated, Literal

from daguflow import ITEM, Cron, ForEach, Pattern, Range, SSHTarget, SubDAG, dag, env, on_failure, shell, task

ROOT = env.PI_ROOT

PI_ENV = {
    "PI_USER": "${HOME_PI_USER}",
    "PI_ROOT": "${HOME_PI_ROOT}",
}

pi = SSHTarget(
    user=env.PI_USER,
    host="192.168.1.50",
    port=22,
    key="/etc/dagu/ssh/id_ed25519",
    strict_host_key=True,
    known_host_file="/etc/dagu/ssh/known_hosts",
)


def lights(args: str) -> str:
    return f"/usr/bin/python3 {ROOT}/lights.py {args}"


@dag(labels=["lights", "shortcut"], env=PI_ENV)
def set_light_effect(effect=""):
    """Set every Nanoleaf light to a named effect

    The free-text value is double-quoted with {effect:q}."""
    pi.run(lights(f"effect --name {effect:q}"), name="set-effect", output="RESULT")


@dag(schedule=Cron("* 15-22 * * *", tz="America/Los_Angeles"), labels=["lights", "schedule"],
     env=PI_ENV, timeout=300)
def schedule_lights(brightness=50, minutes_before=30):
    """Good Vibes at 50% on every light, 30 minutes before sunset"""
    pi.run(lights(f"sunset --brightness {brightness:bare} --minutes-before {minutes_before:bare}"),
               name="sunset-check", output="RESULT")


@task(runs_on=pi)
def list_lights():
    return lights("list --json")


@task(runs_on=pi)
def set_effect(light, name):
    return lights(f"effect --light {light:q} --name {name}")


@task(runs_on=pi)
def set_color(light, ct: int):
    return lights(f"color --light {light:q} --ct {ct}")


# unsafe_args: its input is our own lights.py JSON, not a caller's text.
@task.python(runs_on=pi, python="/usr/bin/python3", unsafe_args=True)
def summarize(listing: dict) -> dict:
    return {"count": len(listing.get("lights", []))}


@dag(labels=["lights"], env=PI_ENV)
def mood_per_light(mode: Literal["warm", "cool"] = "warm",
                   level: Annotated[int, Range(0, 100)] = 30,
                   label: Annotated[str, Pattern(r"^[A-Za-z ]*$")] = ""):
    """One child run per light, four at a time"""
    found = list_lights()
    with SubDAG("apply", items=found.output["names"], max_concurrent=4,
                params={"light": ITEM}, env=PI_ENV) as apply:
        e = set_effect(light=apply.params.light, name="Solid")
        c = set_color(light=apply.params.light, ct=2700)
        e >> c
    report = summarize(found)
    apply >> report
    with ForEach(["a", "b"], as_="room", max_concurrent=2) as rooms:
        shell(f"echo {rooms.item}", name="say")
    with on_failure():
        shell("echo failed", name="notify")
