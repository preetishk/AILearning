"""Intent classifier — classifies a natural language question into a structured IntentResult."""
from __future__ import annotations

import json
import logging
import os

from src.models.facts import IntentResult

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM = (
    "You are an intent classifier for a code knowledge base assistant. "
    "Output only valid JSON. No prose. "
    'Return a JSON object with keys: question_type, primary_entities, '
    'requires_graph, requires_vector, cypher_hint.'
)

CLASSIFIER_USER = """Classify the following question:

{{
  "question_type": "<structural|behavioral|semantic|multi-hop>",
  "primary_entities": ["<extracted entity names>"],
  "requires_graph": <true|false>,
  "requires_vector": <true|false>,
  "cypher_hint": "<rough Cypher MATCH pattern if structural, or null>"
}}

Definitions:
- structural: "What calls X?", "Who implements Y?", "What inherits from Z?"
- behavioral: "What happens when X fails?", "What fixes Y?", "What does X do?"
- semantic: "Find code similar to...", "Which methods do X kind of thing?"
- multi-hop: "Trace the impact of X on Y", "How does A relate to B through the call chain?"

Question: "{question}"
"""


def classify(question: str) -> IntentResult:
    """
    Classify a natural language question into an IntentResult.
    Falls back to a semantic/vector classification if LLM is unavailable.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o")
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM},
                {"role": "user", "content": CLASSIFIER_USER.format(question=question)},
            ],
            response_format={"type": "json_object"},
        )
        raw = json.loads(response.choices[0].message.content)
        return IntentResult(**raw)
    except Exception as e:
        logger.warning(f"Classification failed ({e}), using heuristic fallback")
        return _heuristic_classify(question)


def _heuristic_classify(question: str) -> IntentResult:
    """Rule-based fallback classification when LLM is unavailable."""
    q = question.lower()

    structural_patterns = [
        "what calls", "who calls", "who implements", "what implements",
        "what inherits", "who inherits", "what extends", "callers of",
        "dependents of", "references to",
    ]
    behavioral_patterns = [
        "what happens when", "what fixes", "what does", "how does",
        "when fails", "error handling", "exception", "recovery",
        "outcome", "what causes",
    ]
    multihop_patterns = [
        "trace", "impact", "affect", "chain", "path from", "path to",
        "how does.*relate", "flow from",
    ]

    for pat in multihop_patterns:
        import re
        if re.search(pat, q):
            return IntentResult(
                question_type="multi-hop",
                requires_graph=True,
                requires_vector=True,
            )

    for pat in structural_patterns:
        if pat in q:
            return IntentResult(
                question_type="structural",
                requires_graph=True,
                requires_vector=False,
            )

    for pat in behavioral_patterns:
        if pat in q:
            return IntentResult(
                question_type="behavioral",
                requires_graph=False,
                requires_vector=True,
            )

    return IntentResult(
        question_type="semantic",
        requires_graph=False,
        requires_vector=True,
    )
