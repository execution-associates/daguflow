from typing import Annotated, Literal

from daguflow import DAG, Doc, Param, Pattern, Range, dag, shell


def _params(d):
    return d.to_dict()["params"]


def test_plain_defaults_use_the_one_key_form():
    @dag
    def d(value=50, room="all", note: str = ""):
        shell("true", name="s")

    assert _params(d) == [{"value": 50}, {"room": "all"}, {"note": ""}]


def test_constraints_use_the_rich_form():
    @dag
    def d(level: Annotated[int, Range(0, 100), Doc("percent")] = 30,
          mode: Literal["warm", "cool"] = "warm",
          label: Annotated[str, Pattern(r"^[a-z]+$")] = "x",
          required_one: str = Param(required=True, description="must be given")):
        shell("true", name="s")

    level, mode, label, req = _params(d)
    assert level == {"name": "level", "type": "integer", "default": 30, "minimum": 0, "maximum": 100,
                     "description": "percent"}
    assert mode == {"name": "mode", "type": "string", "default": "warm", "enum": ["warm", "cool"]}
    assert label["pattern"] == "^[a-z]+$" and label["type"] == "string"
    assert req == {"name": "required_one", "required": True, "description": "must be given"}


def test_no_default_is_required():
    @dag
    def d(target: str):
        shell("true", name="s")

    assert _params(d) == [{"name": "target", "type": "string", "required": True}]


def test_a_param_called_name_is_never_one_key():
    # `- name: ""` is read by dagu as an inline definition and fails every start.
    with DAG("d", params={"name": ""}) as d:
        shell("true", name="s")
    assert _params(d) == [{"name": "name", "default": ""}]


def test_param_refs_carry_constraints():
    seen = {}

    @dag
    def d(level: Annotated[int, Range(0, 9)] = 1, free=""):
        seen["level"], seen["free"] = level, free
        shell("true", name="s")

    assert seen["level"].constraint == "number"
    assert seen["free"].constraint is None
