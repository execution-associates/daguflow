import pytest

from daguflow import DAG, ITEM, ForEach, SubDAG, call_dag, dag, shell


def test_subdag_becomes_a_local_document_and_a_call_step():
    with DAG("parent", env={"A": "1"}) as d:
        start = shell("echo start", name="start")
        with SubDAG("child", params={"who": "x"}, env={"B": "2"}, retries=1) as child:
            shell(f"echo {child.params.who}", name="inner")
        start >> child
    entry, local = d.documents()
    call = entry["steps"][1]
    assert call["action"] == "dag.run" and call["with"] == {"dag": "child", "params": {"who": "x"}}
    assert call["depends"] == "start" and call["retry_policy"]["limit"] == 1
    assert local["name"] == "child"
    assert local["params"] == [{"who": ""}]
    assert local["env"] == [{"B": "2"}]
    assert local["steps"] == [{"name": "inner", "run": "echo ${who}"}]


def test_parallel_fan_out_and_outputs():
    with DAG("p") as d:
        listing = shell("echo '[1,2]'", name="list")
        with SubDAG("each", items=listing.output, max_concurrent=3, params={"n": ITEM},
                    output="EACH") as each:
            shell("echo ${n}", name="say")
        shell(f"echo {each.outputs}", name="after")
    entry, _ = d.documents()
    call = entry["steps"][1]
    assert call["parallel"] == {"items": "${LIST}", "max_concurrent": 3}
    assert call["with"]["params"] == {"n": "${ITEM}"}
    assert call["depends"] == "list"
    assert entry["steps"][2] == {"name": "after", "depends": "each", "run": "echo ${EACH.outputs}"}


def test_enqueue_and_queue():
    with DAG("q") as d:
        with SubDAG("bg", enqueue=True, queue="slow"):
            shell("sleep 1", name="z")
    call = d.documents()[0]["steps"][0]
    assert call["action"] == "dag.enqueue" and call["with"]["queue"] == "slow"
    with DAG("q2"):
        with pytest.raises(TypeError):
            SubDAG("bad", queue="x")


def test_nested_subdags_flatten_into_one_file():
    @dag
    def outer_dag():
        with SubDAG("outer") as outer:
            with SubDAG("inner"):
                shell("echo in", name="i")
            shell("echo out", name="o")

    names = [doc.get("name") for doc in outer_dag.documents()]
    assert names == [None, "outer", "inner"]
    assert outer_dag.to_yaml().count("\n---\n") == 2


def test_local_names_must_be_unique_per_file():
    with DAG("u") as d:
        with SubDAG("x"):
            shell("a", name="a")
        with SubDAG("x", step_name="x2"):
            shell("b", name="b")
    with pytest.raises(ValueError, match="repeat"):
        d.documents()


def test_empty_blocks_fail():
    with DAG("e"):
        with pytest.raises(ValueError, match="no steps"):
            with SubDAG("empty"):
                pass


def test_subdag_outside_a_dag_fails():
    with pytest.raises(RuntimeError):
        SubDAG("x")


def test_call_dag():
    with DAG("c") as d:
        call_dag("other", params={"x": 1}, output="OTHER")
        call_dag("dir/thing.yaml", items=["a", "b"])
    steps = d.to_dict()["steps"]
    assert steps[0] == {"name": "other", "action": "dag.run", "with": {"dag": "other", "params": {"x": 1}},
                        "output": "OTHER"}
    assert steps[1]["name"] == "dir-thing" and steps[1]["parallel"] == ["a", "b"]


def test_foreach_inline_body():
    with DAG("f") as d:
        src = shell("echo '[\"a\"]'", name="src")
        with ForEach(src.output, as_="room", max_concurrent=2, collect={"seen": "${foreach.room}"}) as loop:
            first = shell(f"echo {loop.item} {loop.index}", name="first", output="FIRST")
            shell("echo ${FIRST}", name="second")
        assert first.container is loop.body
    step = d.to_dict()["steps"][1]
    assert step["depends"] == "src"
    assert step["foreach"]["items"] == "${SRC}" and step["foreach"]["as"] == "room"
    assert step["foreach"]["steps"][0]["run"] == "echo ${foreach.room} ${foreach.index}"
    assert step["foreach"]["steps"][1]["depends"] == "first"
    assert list(step["foreach"]) == ["items", "as", "max_concurrent", "steps", "collect"]
