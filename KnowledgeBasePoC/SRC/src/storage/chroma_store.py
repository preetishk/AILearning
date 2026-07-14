"""ChromaDB vector store implementation."""
from __future__ import annotations

import os
from typing import Optional

import chromadb
from chromadb.config import Settings


COLLECTIONS = [
    "BehavioralRule",
    "EntityContract",
    "OutcomeRecord",
    "ObservableEvent",
    "OperationalTrace",
    "DocumentSection",
]


class ChromaStore:
    """Implements VectorStore protocol using ChromaDB."""

    def __init__(self):
        host = os.getenv("CHROMA_HOST", "localhost")
        port = int(os.getenv("CHROMA_PORT", "8001"))
        output_dir = os.getenv("OUTPUT_DIR", "./output")

        # Try HTTP client first, fall back to persistent local
        try:
            self._client = chromadb.HttpClient(host=host, port=port)
            self._client.heartbeat()  # test connection
        except Exception:
            persist_path = os.path.join(output_dir, "chroma")
            os.makedirs(persist_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_path)

        self._ensure_collections()

    def _ensure_collections(self) -> None:
        for name in COLLECTIONS:
            self._client.get_or_create_collection(name)

    def _get_collection(self, name: str):
        return self._client.get_or_create_collection(name)

    # ── VectorStore protocol ─────────────────────────────────────────────────

    def upsert(self, collection: str, doc_id: str, text: str,
               embedding: list[float], metadata: dict) -> None:
        col = self._get_collection(collection)
        # Clean metadata — Chroma requires scalar values
        clean_meta = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            elif isinstance(v, list):
                clean_meta[k] = ",".join(str(x) for x in v)
            elif v is None:
                clean_meta[k] = ""
            else:
                clean_meta[k] = str(v)
        col.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[clean_meta],
        )

    def query(self, collection: str, query_embedding: list[float],
              top_k: int = 10, where: Optional[dict] = None) -> list[dict]:
        col = self._get_collection(collection)
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, max(1, self.count(collection))),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        try:
            result = col.query(**kwargs)
        except Exception:
            return []

        docs = []
        ids = result.get("ids", [[]])[0]
        texts = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for doc_id, text, meta, dist in zip(ids, texts, metadatas, distances):
            docs.append({
                "id": doc_id,
                "text": text,
                "metadata": meta,
                "distance": dist,
                "score": max(0.0, 1.0 - dist),
            })
        return docs

    def query_all_collections(self, query_embedding: list[float],
                              top_k: int = 10, where: Optional[dict] = None) -> list[dict]:
        """Query all collections and merge results sorted by score."""
        all_results = []
        for col_name in COLLECTIONS:
            results = self.query(col_name, query_embedding, top_k=top_k, where=where)
            for r in results:
                r["collection"] = col_name
            all_results.extend(results)
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:top_k]

    def delete(self, collection: str, doc_ids: list[str]) -> None:
        col = self._get_collection(collection)
        col.delete(ids=doc_ids)

    def count(self, collection: str) -> int:
        try:
            col = self._get_collection(collection)
            return col.count()
        except Exception:
            return 0

    def list_collections(self) -> list[str]:
        return COLLECTIONS

    def total_count(self) -> int:
        return sum(self.count(c) for c in COLLECTIONS)

    def collection_counts(self) -> dict[str, int]:
        return {c: self.count(c) for c in COLLECTIONS}

    def delete_by_metadata(self, collection: str, where: dict) -> None:
        """Delete documents matching metadata filter."""
        col = self._get_collection(collection)
        try:
            col.delete(where=where)
        except Exception:
            pass
