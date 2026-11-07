"""Home lights: dagu schedules, Python decides and acts.

The lights hub's HTTP API is reached from the dagu worker; one reading comes
from the Pi itself over SSH.
"""

from typing import Annotated, Literal

from daguflow import ITEM, Cron, Range, SSHTarget, SubDAG, dag, env, on_failure, task

HUB = "http://192.168.1.60:8080"

pi = SSHTarget(user=env.PI_USER, host="192.168.1.50", key="/etc/dagu/ssh/id_ed25519",
               strict_host_key=True, known_host_file="/etc/dagu/ssh/known_hosts")


@task
def list_lights(hub: str) -> list:
    import json
    import urllib.request

    with urllib.request.urlopen(f"{hub}/lights", timeout=10) as resp:
        return [light["name"] for light in json.load(resp) if light["reachable"]]


@task
def set_light(hub: str, light: str, mode: str, level: int) -> dict:
    import json
    import urllib.request

    ct = {"warm": 2700, "cool": 5000}[mode]
    body = json.dumps({"on": True, "brightness": level, "ct": ct}).encode()
    req = urllib.request.Request(f"{hub}/lights/{light}", data=body, method="PUT",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


@task
def sunset_trigger(lat: float, lng: float, minutes_before: int) -> dict:
    import datetime
    import json
    import urllib.request

    with urllib.request.urlopen(f"https://api.sunrisesunset.io/json?lat={lat}&lng={lng}", timeout=10) as resp:
        sunset = json.load(resp)["results"]["sunset"]
    at = datetime.datetime.strptime(sunset, "%I:%M:%S %p") - datetime.timedelta(minutes=minutes_before)
    return {"sunset": sunset, "trigger": at.strftime("%H:%M")}


# Runs on the Pi: the reading only exists there.
@task(runs_on=pi, python="/usr/bin/python3")
def pi_temperature() -> float:
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read()) / 1000


@dag(labels=["lights"])
def mood(mode: Literal["warm", "cool"] = "warm", level: Annotated[int, Range(0, 100)] = 30):
    """Every reachable light in one mood, four at a time"""
    found = list_lights(HUB)
    with SubDAG("one", items=found.output, max_concurrent=4,
                params={"light": ITEM, "mode": mode, "level": level}) as one:
        set_light(HUB, one.params.light, one.params.mode, one.params.level)
    with on_failure():
        set_light.override(name="reset")(HUB, "all", "warm", 50)


@dag(schedule=Cron("0 6 * * *", tz="America/Los_Angeles"), labels=["lights", "schedule"])
def plan_evening(minutes_before: Annotated[int, Range(0, 120)] = 30):
    """When tonight's lights should come up, and how warm the Pi is"""
    sunset_trigger(37.7749, -122.4194, minutes_before)
    pi_temperature()
