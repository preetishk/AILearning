"""
Ingest warranty documents into ChromaDB (persistent, local).
Run this once before querying.
"""

import chromadb
from data_generator import WARRANTY_DOCS

CHROMA_PATH = "./chroma_warranty_db"
COLLECTION_NAME = "warranty_docs"


def ingest():
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection to allow re-runs
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        # Default embedding function: all-MiniLM-L6-v2 (local, no API key needed)
        metadata={"hnsw:space": "cosine"},
    )

    ids = [doc["id"] for doc in WARRANTY_DOCS]
    documents = [doc["content"] for doc in WARRANTY_DOCS]
    metadatas = [{"sku": doc["sku"], "title": doc["title"]} for doc in WARRANTY_DOCS]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Ingested {len(ids)} warranty documents into ChromaDB.")
    return collection


if __name__ == "__main__":
    ingest()
