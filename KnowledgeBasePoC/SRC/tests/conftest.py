"""pytest fixtures shared across all tests."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.models.facts import (
    Chunk, EntityFact, RuleFact, VectorDocument, EntityRegistry,
)
from src.storage.protocols import VectorStore, GraphStore


# ── Sample data fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def sample_chunk():
    return Chunk(
        chunk_id="abc123",
        source_ref="src/service.py",
        source_type="code",
        language="python",
        start_line=1,
        end_line=10,
        text="def authenticate_user(token: str) -> bool:\n    ...",
        token_count=15,
    )


@pytest.fixture
def sample_entity_fact():
    return EntityFact(
        canonical_name="authenticate_user",
        kind="function",
        source_ref="src/service.py",
        source_line_start=1,
        source_line_end=10,
        source_type="code",
        summary="Validates a user authentication token.",
        aliases=["auth_user"],
        confidence="high",
    )


@pytest.fixture
def sample_rule_fact():
    return RuleFact(
        rule_id="rule_001",
        description="User must be authenticated before accessing protected resources.",
        trigger="HTTP request to /api/*",
        outcome="401 Unauthorized if token invalid",
        source_ref="src/service.py",
        source_type="code",
        confidence="high",
    )


@pytest.fixture
def sample_entity_registry():
    registry = EntityRegistry()
    registry.add_or_merge("authenticate_user", "function", "src/service.py", ["auth_user"])
    return registry


# ── Mock store fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=VectorStore)
    store.query.return_value = [
        {
            "id": "doc1",
            "text": "authenticate_user validates JWT tokens.",
            "score": 0.92,
            "metadata": {"source_ref": "src/service.py", "collection": "EntityContract"},
        }
    ]
    store.upsert.return_value = None
    store.total_count.return_value = 42
    store.collection_counts.return_value = {"EntityContract": 10, "BehavioralRule": 8}
    return store


@pytest.fixture
def mock_graph_store():
    store = MagicMock(spec=GraphStore)
    store.query.return_value = [
        {"n": {"id": "node_1", "canonical_name": "authenticate_user", "kind": "function"}}
    ]
    store.node_count.return_value = 100
    store.edge_count.return_value = 200
    store.find_impact.return_value = [
        {"entity": "validate_token", "depth": 1, "rel": "CALLS"}
    ]
    store.list_entities.return_value = [
        {"id": "node_1", "canonical_name": "authenticate_user", "kind": "function",
         "source_ref": "src/service.py", "source_type": "code", "confidence": "high"}
    ]
    return store
