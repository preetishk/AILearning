"""Tests for the query pipeline (classifier + retrieval + assembly)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest


def _mock_intent(question_type="structural", entities=None):
    from src.models.facts import IntentResult
    return IntentResult(
        question_type=question_type,
        primary_entities=entities or ["AuthService"],
        sub_questions=[],
        raw_question="Who calls authenticate_user?",
    )


def test_classifier_heuristic_structural():
    from src.agent.classifier import _heuristic_classify
    result = _heuristic_classify("What calls authenticate_user?")
    assert result.question_type in ("structural", "multi_hop", "semantic", "behavioral")


def test_classifier_heuristic_behavioral():
    from src.agent.classifier import _heuristic_classify
    result = _heuristic_classify("What happens if the token is expired?")
    assert result.question_type in ("behavioral", "semantic", "structural", "multi_hop")


def test_vector_retriever_calls_store(mock_vector_store):
    from src.agent.vector_retriever import retrieve_vector
    results = retrieve_vector("authenticate user", mock_vector_store, top_k=5)
    assert isinstance(results, list)


def test_graph_retriever_structural(mock_graph_store):
    intent = _mock_intent("structural", ["AuthService"])
    from src.agent.graph_retriever import retrieve_graph
    results = retrieve_graph(intent, mock_graph_store, top_k=5)
    assert isinstance(results, list)


def test_assemble_produces_answer(mock_graph_store, mock_vector_store):
    from src.agent.assembler import assemble

    graph_results = [
        {"entity": "AuthService", "kind": "class", "source_ref": "src/auth.py",
         "summary": "Handles authentication", "score": 0.9}
    ]
    vector_results = [
        {"id": "v1", "text": "AuthService validates JWT tokens.",
         "score": 0.88, "metadata": {"source_ref": "src/auth.py"}}
    ]

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "AuthService is a class that handles user authentication using JWT tokens."
    )

    with patch("src.agent.assembler._client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        result = assemble("What does AuthService do?", graph_results, vector_results, None)

    assert "answer" in result
    assert len(result["answer"]) > 0
    assert "overall_confidence" in result
    assert "retrieval_lanes_used" in result


def test_assemble_no_results_graceful():
    from src.agent.assembler import assemble

    with patch("src.agent.assembler._client") as mock_client:
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="No information found."))]
        )
        result = assemble("Unknown entity?", [], [], None)

    assert "answer" in result
    assert result["overall_confidence"] <= 1.0
