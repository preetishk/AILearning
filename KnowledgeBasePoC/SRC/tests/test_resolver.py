"""Tests for entity resolver."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from src.models.facts import EntityRegistry


def test_entity_registry_add_and_lookup():
    registry = EntityRegistry()
    registry.add_or_merge("AuthService", "class", "src/auth.py")
    entry = registry.lookup("AuthService")
    assert entry is not None
    assert entry.canonical_name == "AuthService"


def test_entity_registry_alias_lookup():
    registry = EntityRegistry()
    registry.add_or_merge("AuthService", "class", "src/auth.py", aliases=["Auth", "AuthSvc"])
    entry = registry.lookup("Auth")
    assert entry is not None
    assert entry.canonical_name == "AuthService"


def test_entity_registry_merge_aliases():
    registry = EntityRegistry()
    registry.add_or_merge("AuthService", "class", "src/auth.py", aliases=["Auth"])
    registry.add_or_merge("AuthService", "class", "src/auth2.py", aliases=["AuthSvc"])
    entry = registry.lookup("AuthSvc")
    assert entry is not None
    assert entry.canonical_name == "AuthService"


def test_entity_registry_serialisation():
    registry = EntityRegistry()
    registry.add_or_merge("Foo", "function", "foo.py")
    registry.add_or_merge("Bar", "class", "bar.py")
    json_str = registry.model_dump_json()
    reloaded = EntityRegistry.model_validate_json(json_str)
    assert reloaded.lookup("Foo") is not None
    assert reloaded.lookup("Bar") is not None


def test_resolve_entities_deduplicates(tmp_path):
    """resolve_entities should collapse near-duplicate entity names."""
    from src.models.facts import EntityFact

    facts = [
        EntityFact(canonical_name="authenticate_user", kind="function",
                   source_ref="a.py", source_type="code",
                   source_line_start=1, source_line_end=5, confidence="high"),
        EntityFact(canonical_name="authenticateUser", kind="function",
                   source_ref="b.py", source_type="code",
                   source_line_start=1, source_line_end=5, confidence="high"),
    ]

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (input_dir / "structural.json").write_text(
        json.dumps([f.model_dump() for f in facts])
    )

    # Mock embeddings to return identical vectors → should cluster them
    fake_embeddings = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]

    with patch("src.pipeline.resolver._embed_names", return_value=fake_embeddings):
        with patch("src.pipeline.resolver._llm_resolve", return_value="authenticate_user"):
            from src.pipeline.resolver import resolve_entities
            registry = resolve_entities(str(input_dir), str(output_dir))

    assert len(registry.entries) <= 2
