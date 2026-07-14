"""Protocol abstractions for Vector and Graph storage backends."""
from __future__ import annotations

import os
from typing import Protocol, runtime_checkable, Optional


@runtime_checkable
class VectorStore(Protocol):
    """Protocol that all vector store backends must implement."""

    def upsert(self, collection: str, doc_id: str, text: str,
               embedding: list[float], metadata: dict) -> None:
        """Insert or update a document in the given collection."""
        ...

    def query(self, collection: str, query_embedding: list[float],
              top_k: int = 10, where: Optional[dict] = None) -> list[dict]:
        """ANN search. Returns list of {id, text, metadata, distance}."""
        ...

    def delete(self, collection: str, doc_ids: list[str]) -> None:
        """Delete documents by ID."""
        ...

    def count(self, collection: str) -> int:
        """Return document count for a collection."""
        ...

    def list_collections(self) -> list[str]:
        """Return all collection names."""
        ...


@runtime_checkable
class GraphStore(Protocol):
    """Protocol that all graph store backends must implement."""

    def upsert_node(self, label: str, node_id: str, properties: dict) -> None:
        """MERGE a node by id, setting all properties."""
        ...

    def upsert_edge(self, from_id: str, to_id: str,
                    relation_type: str, properties: dict = None) -> None:
        """MERGE a typed directed edge between two nodes."""
        ...

    def query(self, cypher: str, params: dict = None) -> list[dict]:
        """Run a raw Cypher query. Returns list of record dicts."""
        ...

    def node_count(self) -> int:
        """Return total node count."""
        ...

    def edge_count(self) -> int:
        """Return total relationship count."""
        ...

    def close(self) -> None:
        """Release connections."""
        ...


# ── Factory functions ─────────────────────────────────────────────────────────

def get_vector_store() -> VectorStore:
    """Read VECTOR_BACKEND env var and return the appropriate VectorStore."""
    backend = os.getenv("VECTOR_BACKEND", "chroma").lower()
    if backend == "chroma":
        from src.storage.chroma_store import ChromaStore
        return ChromaStore()
    raise ValueError(f"Unknown VECTOR_BACKEND: {backend}")


def get_graph_store() -> GraphStore:
    """Read GRAPH_BACKEND env var and return the appropriate GraphStore."""
    backend = os.getenv("GRAPH_BACKEND", "neo4j").lower()
    if backend == "neo4j":
        from src.storage.neo4j_store import Neo4jStore
        return Neo4jStore()
    if backend == "kuzu":
        from src.storage.kuzu_store import KuzuStore
        return KuzuStore()
    raise ValueError(f"Unknown GRAPH_BACKEND: {backend}")
