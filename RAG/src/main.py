"""
Demo: RAG-only vs RAG+BM25 (Hybrid) on warranty documents.

Run:
    cd RAG/src
    python main.py

Queries are chosen to highlight where BM25 wins (exact SKU codes)
and where semantic search is sufficient.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ingest import ingest
from retriever import RAGRetriever, HybridRetriever
from llm import ask_llm

SEPARATOR = "=" * 70

# Queries designed to expose the RAG vs RAG+BM25 gap
DEMO_QUERIES = [
    # BM25 advantage: SKU code (alphanumeric token) not semantically meaningful
    {
        "label": "SKU-specific query (BM25 wins)",
        "query": "What are the exclusions for SKU KBD-MECH-RGB?",
    },
    # BM25 advantage: exact product code in user question
    {
        "label": "Exact product code in query (BM25 wins)",
        "query": "How do I claim warranty for PHN-X500-BLK water damage?",
    },
    # Semantic advantage: concept-level query without SKU codes
    {
        "label": "Semantic query (both handle well)",
        "query": "Which product has the longest warranty period?",
    },
]


def print_retrieved(label: str, docs: list[dict]):
    print(f"\n  Retrieved by {label}:")
    for i, d in enumerate(docs, 1):
        sku = d["metadata"]["sku"]
        title = d["metadata"]["title"]
        print(f"    [{i}] {sku} — {title}")


def run_demo():
    print(SEPARATOR)
    print("Ingesting warranty documents into ChromaDB...")
    ingest()

    rag = RAGRetriever()
    hybrid = HybridRetriever()

    for item in DEMO_QUERIES:
        label = item["label"]
        query = item["query"]

        print(f"\n{SEPARATOR}")
        print(f"  DEMO: {label}")
        print(f"  QUERY: {query}")
        print(SEPARATOR)

        # --- RAG only ---
        rag_docs = rag.retrieve(query)
        print_retrieved("RAG-only", rag_docs)
        rag_answer = ask_llm(query, rag_docs)
        print(f"\n  RAG-only Answer:\n  {rag_answer}")

        print()

        # --- Hybrid RAG + BM25 ---
        hybrid_docs = hybrid.retrieve(query)
        print_retrieved("RAG+BM25 (Hybrid)", hybrid_docs)
        hybrid_answer = ask_llm(query, hybrid_docs)
        print(f"\n  RAG+BM25 Answer:\n  {hybrid_answer}")

        print()

    print(SEPARATOR)
    print("Demo complete.")
    print(SEPARATOR)


if __name__ == "__main__":
    run_demo()
