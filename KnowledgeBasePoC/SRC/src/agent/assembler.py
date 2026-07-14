"""Answer assembler — merges graph + vector + pagindex results and generates a grounded answer."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from src.models.facts import IntentResult, PageResult

logger = logging.getLogger(__name__)

CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.4}


def rerank(results: list[dict], query_vector: list[float]) -> list[dict]:
    """
    Score and rank merged results.

    Scoring formula:
        score = base_similarity * confidence_weight * source_boost

    Returns top 20 sorted by score descending.
    """
    import numpy as np

    query_vec = np.array(query_vector) if query_vector else None

    for r in results:
        base = r.get("score", r.get("_score", 0.5))
        confidence = r.get("metadata", {}).get("confidence") or r.get("confidence", "medium")
        conf_weight = CONFIDENCE_WEIGHT.get(confidence, 0.7)
        # Graph results get a source boost
        source_boost = 1.1 if r.get("graph_path") else 1.0
        r["_score"] = base * conf_weight * source_boost

    return sorted(results, key=lambda x: x.get("_score", 0), reverse=True)[:20]


def compute_overall_confidence(results: list[dict]) -> float:
    """Mean score of top-5 results, clamped to [0, 1]."""
    top = sorted(results, key=lambda x: x.get("_score", 0), reverse=True)[:5]
    if not top:
        return 0.0
    return min(1.0, sum(r.get("_score", 0) for r in top) / len(top))


ASSEMBLER_SYSTEM = (
    "You are a code knowledge base assistant. "
    "Answer questions using ONLY the provided facts. "
    "Do not infer or add information not present in the facts. Cite every claim.\n\n"
    "If the facts are insufficient, say: "
    "'I don't have enough evidence to answer this confidently. "
    "The closest facts I found are: [list them].'"
)

ASSEMBLER_USER = """Question: {question}

Facts (ranked by relevance):
{facts_text}

Instructions:
- Answer in 2-5 sentences.
- After the answer, list: "Sources used:" with one bullet per cited fact showing source_ref, line numbers, and confidence.
- If a fact has a graph_path, include it as: "Graph path: A→B→C"
"""


def assemble(
    question: str,
    graph_results: list[dict],
    vector_results: list[dict],
    page_result: Optional[PageResult],
    query_vector: Optional[list[float]] = None,
) -> dict:
    """
    Merge, rank, and synthesise results into a QueryResponse dict.

    Returns a dict matching the QueryResponse Pydantic model schema.
    """
    # Merge all results
    all_results: list[dict] = []

    for r in graph_results:
        r.setdefault("_score", r.get("score", 0.8))
        r["_source"] = "graph"
    all_results.extend(graph_results)

    for r in vector_results:
        r.setdefault("_score", r.get("score", 0.5))
        r["_source"] = "vector"
    all_results.extend(vector_results)

    if page_result and page_result.primary_page:
        all_results.append({
            "_score": page_result.confidence,
            "_source": "pagindex",
            "text": page_result.primary_page[:2000],
            "metadata": {"source_type": "wiki", "confidence": "medium"},
        })

    # Rerank
    ranked = rerank(all_results, query_vector or [])
    overall_confidence = compute_overall_confidence(ranked)

    # Build citations
    citations = []
    for r in ranked[:10]:
        meta = r.get("metadata", {})
        citation = {
            "fact_id": r.get("id", ""),
            "source_ref": meta.get("source_ref") or r.get("source_ref", ""),
            "source_line_start": meta.get("source_line_start"),
            "source_line_end": meta.get("source_line_end"),
            "snippet": (r.get("text") or "")[:300],
            "relevance_score": round(r.get("_score", 0), 3),
            "confidence": meta.get("confidence", "medium"),
            "graph_path": r.get("graph_path"),
        }
        citations.append(citation)

    # Determine which retrieval lanes were used
    lanes = []
    if graph_results:
        lanes.append("graph")
    if vector_results:
        lanes.append("vector")
    if page_result and page_result.primary_page:
        lanes.append("pagindex")

    # Generate answer
    answer = _generate_answer(question, ranked[:10])
    grounded = overall_confidence >= 0.3 and bool(citations)

    return {
        "answer": answer,
        "question_type": "semantic",  # overridden by caller
        "overall_confidence": round(overall_confidence, 3),
        "answer_grounded": grounded,
        "citations": citations,
        "graph_paths": [r.get("graph_path") for r in ranked if r.get("graph_path")],
        "retrieval_lanes_used": lanes,
    }


def _generate_answer(question: str, facts: list[dict]) -> str:
    """Call LLM to synthesise an answer from ranked facts."""
    if not facts:
        return "No relevant facts found in the knowledge base for this question."

    facts_text = "\n\n".join(
        f"[{i+1}] (score={r.get('_score', 0):.2f}, source={r.get('source_ref', r.get('metadata', {}).get('source_ref', 'unknown'))})\n{r.get('text', r.get('canonical_name', ''))[:500]}"
        for i, r in enumerate(facts[:8])
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o")
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": ASSEMBLER_SYSTEM},
                {"role": "user", "content": ASSEMBLER_USER.format(
                    question=question,
                    facts_text=facts_text,
                )},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Answer generation failed: {e}")
        # Fallback: return top fact as answer
        top = facts[0]
        return top.get("text", top.get("canonical_name", "Unable to generate answer."))[:500]
