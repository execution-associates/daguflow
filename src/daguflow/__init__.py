"""daguflow: author dagu workflows in Python, Airflow-style.

    from daguflow import dag, task, SubDAG, ForEach, Cron, env

    @dag(schedule=Cron("0 9 * * *", tz="America/Los_Angeles"), labels=["reports"])
    def morning_report(day: str = "today"):
        '''Build and send the morning report.'''
        data = fetch(day)
        send(data)

`daguflow build <module> -o dags/` writes one YAML file per DAG.
"""

from __future__ import annotations

from . import actions
from .dag import DAG, dag, on_abort, on_exit, on_failure, on_init, on_success, on_wait
from .groups import ExternalDAG, ForEach, SubDAG, call_dag
from .params import Doc, Length, Param, Pattern, Range
from .refs import ITEM, ParamRef, Ref, consts, ctx, env, raw, var
from .schedule import At, Cron, StartStop
from .schema import DAGU_VERSION
from .step import Action, Step, chain, shell, step
from .targets import ContainerTarget, SSHTarget, container
from .task import task

__version__ = "0.1.0"

__all__ = [
    "DAG", "DAGU_VERSION", "ITEM", "Action", "At", "ContainerTarget", "Cron", "Doc", "ExternalDAG",
    "ForEach", "Length", "Param", "ParamRef", "Pattern", "Range", "Ref", "SSHTarget", "StartStop",
    "Step", "SubDAG", "actions", "call_dag", "chain", "consts", "container", "ctx", "dag", "env",
    "on_abort", "on_exit", "on_failure", "on_init", "on_success", "on_wait", "raw", "shell", "step",
    "task", "var",
]
