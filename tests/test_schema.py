"""dagu's schema is GPL-3.0-or-later: daguflow fetches it, pinned by sha256, and never ships it."""

from __future__ import annotations

from pathlib import Path

import pytest

from daguflow import schema


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """A cold cache and a local copy of the real schema standing in for GitHub."""
    real = schema.cache_path().read_bytes() if schema.cache_path().exists() else schema.fetch().read_bytes()
    upstream = tmp_path / "upstream.json"
    upstream.write_bytes(real)
    monkeypatch.setattr(schema, "SOURCE", upstream.as_uri())
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.delenv("DAGUFLOW_SCHEMA", raising=False)
    schema.load.cache_clear()
    yield upstream, real
    schema.load.cache_clear()


def test_the_package_ships_no_schema():
    assert not list(Path(schema.__file__).parent.glob("*.json"))


def test_the_first_load_downloads_checks_and_caches(isolated):
    _, real = isolated
    assert not schema.cache_path().exists()
    assert "definitions" in schema.load()
    assert schema.cache_path().read_bytes() == real


def test_a_download_that_is_not_the_pinned_schema_is_refused(isolated):
    upstream, real = isolated
    upstream.write_bytes(real.replace(b"Dagu", b"Gadu", 1))
    with pytest.raises(schema.SchemaUnavailable, match="not dagu"):
        schema.load()
    assert not schema.cache_path().exists()


def test_a_damaged_cache_is_fetched_again(isolated):
    _, real = isolated
    schema.cache_path().parent.mkdir(parents=True)
    schema.cache_path().write_text("{}")
    schema.load()
    assert schema.cache_path().read_bytes() == real


def test_offline_with_no_cache_says_how_to_fix_it(isolated, monkeypatch):
    monkeypatch.setattr(schema, "SOURCE", "http://127.0.0.1:9/dag.schema.json")
    with pytest.raises(schema.SchemaUnavailable, match="daguflow schema fetch"):
        schema.load()


def test_daguflow_schema_points_at_a_copy_and_it_is_checked_too(isolated, tmp_path, monkeypatch):
    _, real = isolated
    copy = tmp_path / "copy.json"
    copy.write_bytes(real)
    monkeypatch.setenv("DAGUFLOW_SCHEMA", str(copy))
    monkeypatch.setattr(schema, "SOURCE", "http://127.0.0.1:9/never")
    assert "definitions" in schema.load()
    schema.load.cache_clear()
    copy.write_text("{}")
    with pytest.raises(schema.SchemaUnavailable):
        schema.load()
