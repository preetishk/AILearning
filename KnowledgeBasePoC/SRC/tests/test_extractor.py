"""Tests for the LLM extraction pipeline."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from src.models.facts import Chunk


@pytest.fixture
def py_chunk():
    return Chunk(
        chunk_id="c1",
        source_ref="src/auth.py",
        source_type="code",
        language="python",
        start_line=1,
        end_line=20,
        text=(
            "class AuthService:\n"
            "    def authenticate(self, token: str) -> bool:\n"
            "        if not token:\n"
            "            raise ValueError('token required')\n"
            "        return self._validate(token)\n"
        ),
        token_count=40,
    )


def _mock_openai_response(content: str):
    """Build a minimal mock that looks like an OpenAI response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_extract_layer1_returns_entity_facts(py_chunk):
    entities_payload = json.dumps([{
        "canonical_name": "AuthService",
        "kind": "class",
        "source_ref": "src/auth.py",
        "source_line_start": 1,
        "source_line_end": 20,
        "source_type": "code",
        "summary": "Authentication service",
        "aliases": [],
        "confidence": "high",
    }])
    mock_resp = _mock_openai_response(f"```json\n{entities_payload}\n```")

    with patch("src.pipeline.extractor._client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        from src.pipeline.extractor import extract_layer1
        facts = extract_layer1(py_chunk)

    assert len(facts) == 1
    assert facts[0].canonical_name == "AuthService"
    assert facts[0].kind == "class"


def test_extract_layer2_returns_rule_facts(py_chunk):
    rules_payload = json.dumps([{
        "rule_id": "R001",
        "description": "Token must not be empty",
        "trigger": "authenticate called with empty token",
        "outcome": "ValueError raised",
        "source_ref": "src/auth.py",
        "source_type": "code",
        "confidence": "high",
    }])
    mock_resp = _mock_openai_response(f"```json\n{rules_payload}\n```")

    with patch("src.pipeline.extractor._client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        from src.pipeline.extractor import extract_layer2
        facts = extract_layer2(py_chunk)

    assert len(facts) == 1
    assert "Token" in facts[0].description


def test_extract_all_layers_aggregates(py_chunk):
    empty_list = json.dumps([])
    mock_resp = _mock_openai_response(f"```json\n{empty_list}\n```")

    with patch("src.pipeline.extractor._client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        from src.pipeline.extractor import extract_all_layers
        result = extract_all_layers(py_chunk)

    # Should have keys for all 5 layers
    assert "layer1" in result
    assert "layer2" in result
    assert "layer3" in result
    assert "layer4" in result
    assert "layer5" in result


def test_extract_handles_malformed_json(py_chunk):
    mock_resp = _mock_openai_response("not json at all")

    with patch("src.pipeline.extractor._client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        from src.pipeline.extractor import extract_layer1
        facts = extract_layer1(py_chunk)

    # Should gracefully return empty list, not raise
    assert facts == []


def test_route_to_collection():
    from src.pipeline.extractor import route_to_collection
    from src.models.facts import EntityFact, RuleFact, ContractFact, OperationalFact

    ef = EntityFact(canonical_name="X", kind="class", source_ref="x.py", source_type="code",
                    source_line_start=1, source_line_end=1, confidence="high")
    rf = RuleFact(rule_id="R1", description="d", trigger="t", outcome="o",
                  source_ref="x.py", source_type="code", confidence="high")

    assert route_to_collection(ef) in ("EntityContract", "BehavioralRule", "DocumentSection")
    assert route_to_collection(rf) in ("BehavioralRule", "EntityContract", "DocumentSection")
