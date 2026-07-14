"""Vector retriever — ANN search across Chroma collections."""
from __future__ import annotations

import logging
import os
from typing import Optional

from src.models.facts import VectorDocument
from src.storage.protocols import VectorStore

logger = logging.getLogger(__name__)

LAYER_TO_COLLECTIONS = {
    2: ["BehavioralRule", "OutcomeRecord"],
    3: ["EntityContract", "OutcomeRecord"],
    4: ["OperationalTrace", "DocumentSection"],
}

ALL_COLLECTIONS = [
    "BehavioralRule", "EntityContract", "OutcomeRecord",
    "ObservableEvent", "OperationalTrace", "DocumentSection",
]


def _embed_query(question: str) -> list[float]:
    """Embed the query text using the configured model."""
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    try:
        if "text-embedding" in model_name:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(model=model_name, input=[question])
            return response.data[0].embedding
        else:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            return model.encode([question])[0].tolist()
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return [0.0] * 384


def retrieve_vector(
    question: str,
    vector_store: VectorStore,
    top_k: int = 10,
    filter_layer: Optional[int] = None,
    filter_source_type: Optional[str] = None,
) -> list[dict]:
    """
    ANN search across vector collections.

    Args:
        question: Natural language query.
        vector_store: VectorStore instance.
        top_k: Number of results to return.
        filter_layer: If set, only query collections for that extraction layer.
        filter_source_type: If set, filter by source type ("code" or "document").

    Returns:
        List of result dicts with keys: id, text, metadata, score, collection.
    """
    query_vec = _embed_query(question)

    # Determine which collections to query
    if filter_layer and filter_layer in LAYER_TO_COLLECTIONS:
        collections = LAYER_TO_COLLECTIONS[filter_layer]
    else:
        collections = ALL_COLLECTIONS

    # Build metadata filter
    where = None
    if filter_source_type:
        source_type_map = {"code": "code", "document": "markdown"}
        mapped = source_type_map.get(filter_source_type, filter_source_type)
        where = {"source_type": {"$eq": mapped}}

    all_results: list[dict] = []
    for collection in collections:
        try:
            results = vector_store.query(
                collection=collection,
                query_embedding=query_vec,
                top_k=top_k,
                where=where,
            )
            for r in results:
                r["collection"] = collection
            all_results.extend(results)
        except Exception as e:
            logger.debug(f"Vector query failed for {collection}: {e}")

    # Sort by score and deduplicate
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    seen = set()
    unique = []
    for r in all_results:
        doc_id = r.get("id", "")
        if doc_id not in seen:
            seen.add(doc_id)
            unique.append(r)

    return unique[:top_k]
