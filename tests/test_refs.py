import pytest

from daguflow import ITEM, ParamRef, Ref, ctx, env, var


def test_render_forms():
    effect = ParamRef("effect")
    assert f"--name {effect}" == "--name ${effect}"
    assert f"--name {effect:q}" == '--name "${effect}"'
    assert f"--value {effect:bare}" == "--value $effect"
    assert str(effect.scoped) == "${params.effect}"


def test_namespaces():
    assert str(env.PI_USER) == "${env.PI_USER}"
    assert str(ctx.run.id) == "${context.run.id}"
    assert str(var("HOME_PI_USER")) == "${HOME_PI_USER}"
    assert str(ITEM.light) == "${ITEM.light}"


def test_paths():
    r = Ref("CATALOG")
    assert str(r["effects"]) == "${CATALOG.effects}"
    assert str(r["outputs"][0].NAME) == "${CATALOG.outputs[0].NAME}"


def test_bare_needs_identifier():
    with pytest.raises(ValueError):
        format(Ref("A.b"), "bare")


def test_unknown_format_spec():
    with pytest.raises(ValueError):
        format(Ref("x"), "z")


def test_refs_refuse_python_branching():
    with pytest.raises(TypeError, match="preconditions"):
        if ParamRef("mode"):
            pass
