"""Query route — hybrid graph + vector retrieval."""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    QueryRequest, QueryResponse, CitationItem,
    GraphAnalysisRequest, GraphAnalysisResponse, PathStep,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_kb(body: QueryRequest):
    """Run a natural language question against the knowledge base."""
    from src.agent.classifier import classify
    from src.agent.assembler import assemble
    from src.storage.protocols import get_graph_store, get_vector_store

    intent = classify(body.question)

    graph_results: list[dict] = []
    vector_results: list[dict] = []
    page_result = None

    # Graph retrieval
    if body.retrieval_mode in ("both", "graph") and intent.requires_graph:
        try:
            from src.agent.graph_retriever import retrieve_graph
            graph_store = get_graph_store()
            graph_results = retrieve_graph(intent, graph_store, top_k=body.top_k)
            graph_store.close()
        except Exception as e:
            logger.warning(f"Graph retrieval failed: {e}")

    # Vector retrieval
    if body.retrieval_mode in ("both", "vector") and intent.requires_vector:
        try:
            from src.agent.vector_retriever import retrieve_vector
            vector_store = get_vector_store()
            vector_results = retrieve_vector(
                body.question,
                vector_store,
                top_k=body.top_k,
                filter_layer=body.filter_layer,
                filter_source_type=body.filter_source_type,
            )
        except Exception as e:
            logger.warning(f"Vector retrieval failed: {e}")

    # PageIndex retrieval (for overview/semantic questions)
    if intent.question_type in ("semantic",) and body.retrieval_mode in ("both", "vector"):
        try:
            from src.agent.pagindex import retrieve_pagindex
            page_result = retrieve_pagindex(body.question)
        except Exception as e:
            logger.debug(f"PageIndex retrieval failed: {e}")

    # Assemble answer
    raw = assemble(body.question, graph_results, vector_results, page_result)
    raw["question_type"] = intent.question_type

    return QueryResponse(
        answer=raw["answer"],
        question_type=raw["question_type"],
        overall_confidence=raw["overall_confidence"],
        answer_grounded=raw["answer_grounded"],
        citations=[CitationItem(**c) for c in raw.get("citations", [])],
        graph_paths=raw.get("graph_paths", []),
        retrieval_lanes_used=raw.get("retrieval_lanes_used", []),
    )


@router.post("/graph/analyze", response_model=GraphAnalysisResponse)
async def analyze_graph(body: GraphAnalysisRequest):
    """Perform graph path / impact / dependency analysis."""
    from src.storage.protocols import get_graph_store

    try:
        graph_store = get_graph_store()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Graph DB unavailable: {e}")

    try:
        if body.analysis_type == "shortest_path":
            raw_results = graph_store.find_shortest_path(
                body.source_entity, body.target_entity or ""
            )
            paths = _format_path_results(raw_results)
            summary = f"Shortest path from {body.source_entity} to {body.target_entity}"

        elif body.analysis_type == "all_paths":
            raw_results = graph_store.find_all_paths(
                body.source_entity, body.target_entity or "", body.max_depth
            )
            paths = _format_path_results(raw_results)
            summary = f"All paths from {body.source_entity} to {body.target_entity}"

        elif body.analysis_type == "impact":
            raw_nodes = graph_store.find_impact(body.source_entity, body.max_depth)
            paths = []
            summary = f"Impact analysis: {len(raw_nodes)} entities affected by {body.source_entity}"
            graph_store.close()
            return GraphAnalysisResponse(
                analysis_type=body.analysis_type,
                source_entity=body.source_entity,
                nodes=raw_nodes,
                summary=summary,
            )

        elif body.analysis_type == "reverse_deps":
            raw_nodes = graph_store.find_reverse_deps(body.source_entity, body.max_depth)
            paths = []
            summary = f"Reverse dependencies: {len(raw_nodes)} entities depend on {body.source_entity}"
            graph_store.close()
            return GraphAnalysisResponse(
                analysis_type=body.analysis_type,
                source_entity=body.source_entity,
                nodes=raw_nodes,
                summary=summary,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis_type: {body.analysis_type}")

        graph_store.close()
        return GraphAnalysisResponse(
            analysis_type=body.analysis_type,
            source_entity=body.source_entity,
            target_entity=body.target_entity,
            paths=paths,
            summary=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        graph_store.close()
        raise HTTPException(status_code=500, detail=str(e))


def _format_path_results(raw: list[dict]) -> list[list[PathStep]]:
    paths = []
    for row in raw:
        node_names = row.get("node_names", [])
        rel_types = row.get("rel_types", [])
        steps = []
        for i, name in enumerate(node_names):
            rel = rel_types[i] if i < len(rel_types) else None
            steps.append(PathStep(node_name=str(name), rel_type=rel))
        if steps:
            paths.append(steps)
    return paths
