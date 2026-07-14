"""Stats and health routes."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter

from src.api.schemas import StatsResponse, CollectionCount
from src.pipeline.job_manager import JobManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Return graph node/edge counts and vector document counts per collection."""
    graph_nodes = 0
    graph_edges = 0
    vector_count = 0
    collection_counts = []

    # Graph DB stats
    try:
        from src.storage.protocols import get_graph_store
        graph_store = get_graph_store()
        graph_nodes = graph_store.node_count()
        graph_edges = graph_store.edge_count()
        graph_store.close()
    except Exception as e:
        logger.debug(f"Graph stats unavailable: {e}")

    # Vector DB stats
    try:
        from src.storage.protocols import get_vector_store
        vector_store = get_vector_store()
        col_counts = vector_store.collection_counts()
        collection_counts = [
            CollectionCount(name=name, count=count)
            for name, count in col_counts.items()
        ]
        vector_count = sum(col_counts.values())
    except Exception as e:
        logger.debug(f"Vector stats unavailable: {e}")

    # Entity registry size
    registry_size = 0
    output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
    registry_file = output_dir / "entity_registry.json"
    if registry_file.exists():
        try:
            data = json.loads(registry_file.read_text())
            registry_size = len(data.get("entries", []))
        except Exception:
            pass

    # Job stats
    all_jobs = JobManager.list_all()
    done_jobs = [j for j in all_jobs if j.status == "done"]
    last_ingest = None
    if done_jobs:
        last_ingest = max(
            (j.completed_at for j in done_jobs if j.completed_at),
            default=None,
        )

    return StatsResponse(
        graph_node_count=graph_nodes,
        graph_edge_count=graph_edges,
        vector_doc_count=vector_count,
        entity_registry_size=registry_size,
        collection_counts=collection_counts,
        total_sources_ingested=len(done_jobs),
        last_ingest_at=last_ingest,
    )


@router.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}
