"""
Retrieval strategies:
  - RAGRetriever     : dense vector search only (ChromaDB)
  - HybridRetriever  : dense (ChromaDB) + sparse (BM25) merged via Reciprocal Rank Fusion
"""

import chromadb
from rank_bm25 import BM25Okapi
from data_generator import WARRANTY_DOCS

CHROMA_PATH = "./chroma_warranty_db"
COLLECTION_NAME = "warranty_docs"

TOP_K = 3   # candidates from each retriever before fusion


# --------------------------------------------------------------------------- #
#  Shared helpers
# --------------------------------------------------------------------------- #

def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(COLLECTION_NAME)


def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Merge ranked ID lists with RRF scoring."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda x: scores[x], reverse=True)


def _docs_by_ids(ids: list[str]) -> list[dict]:
    """Return WARRANTY_DOCS entries in the given id order."""
    lookup = {d["id"]: d for d in WARRANTY_DOCS}
    return [lookup[i] for i in ids if i in lookup]


# --------------------------------------------------------------------------- #
#  BM25 index (built once from WARRANTY_DOCS)
# --------------------------------------------------------------------------- #

_BM25_CORPUS = [doc["content"].lower().split() for doc in WARRANTY_DOCS]
_BM25_IDS = [doc["id"] for doc in WARRANTY_DOCS]
_BM25_INDEX = BM25Okapi(_BM25_CORPUS)


# --------------------------------------------------------------------------- #
#  RAG-only retriever (dense vector search)
# --------------------------------------------------------------------------- #

class RAGRetriever:
    def __init__(self):
        self.collection = _get_collection()

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        return [
            {"id": ids[i], "content": docs[i], "metadata": metas[i]}
            for i in range(len(ids))
        ]


# --------------------------------------------------------------------------- #
#  Hybrid retriever (dense + BM25 → RRF)
# --------------------------------------------------------------------------- #

class HybridRetriever:
    def __init__(self):
        self.collection = _get_collection()

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        # 1. Dense retrieval
        dense_results = self.collection.query(query_texts=[query], n_results=top_k)
        dense_ids = dense_results["ids"][0]

        # 2. BM25 sparse retrieval
        tokens = query.lower().split()
        bm25_scores = _BM25_INDEX.get_scores(tokens)
        bm25_ranked = sorted(
            range(len(_BM25_IDS)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )
        bm25_ids = [_BM25_IDS[i] for i in bm25_ranked[:top_k]]

        # 3. Fuse rankings
        fused_ids = _reciprocal_rank_fusion([dense_ids, bm25_ids])[:top_k]

        # 4. Fetch full doc content
        all_docs = {r["id"]: r for r in _docs_by_ids(fused_ids)}
        # Supplement with ChromaDB metadata for any that may differ
        return [
            {
                "id": doc_id,
                "content": all_docs[doc_id]["content"],
                "metadata": {
                    "sku": all_docs[doc_id]["sku"],
                    "title": all_docs[doc_id]["title"],
                },
            }
            for doc_id in fused_ids
            if doc_id in all_docs
        ]
