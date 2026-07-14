import chromadb
from chromadb.config import Settings
import time
import os


# use persistent local chroma with data folder
def init_chroma():
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Use PersistentClient to store data permanently
    client = chromadb.PersistentClient(path=data_dir)
    return client


# create a collection per page id


def create_page_collection(client, page_id, title=None):
    name = f"page_{page_id}"
    try:
        # Try to get existing collection first (for persistence across sessions)
        collection = client.get_collection(name=name)
        print(f"✅ Loaded existing collection: {name}")
    except Exception:
        # Create new collection if it doesn't exist
        collection = client.create_collection(name=name)
        print(f"✅ Created new collection: {name}")
    # Save or update the page title as a special document
    if title:
        try:
            collection.delete(ids=["page_title"])
        except Exception:
            pass
        collection.add(documents=[title], metadatas=[{"role": "title"}], ids=["page_title"])
    return name


def delete_page_collection(client, page_id):
    name = f"page_{page_id}"
    try:
        client.delete_collection(name)
    except Exception:
    # for PoC keep simple
        pass


def list_pages(client):
    """List all existing page collections from persistent storage, including titles if available"""
    collections = client.list_collections()
    page_collections = []
    for collection in collections:
        if collection.name.startswith('page_'):
            page_id = collection.name.replace('page_', '')
            # Try to get the title from the special document
            title = None
            try:
                coll = client.get_collection(collection.name)
                result = coll.get(ids=["page_title"], include=["documents"])
                docs = result.get("documents", [])
                if docs and docs[0]:
                    title = docs[0]
            except Exception:
                pass
            page_collections.append({
                'id': page_id,
                'name': collection.name,
                'count': collection.count(),
                'title': title
            })
    return page_collections


# Save a message as a "document". We store a timestamped id so we can retrieve in order.


def save_message(client, page_id, role, content):
    name = f"page_{page_id}"
    collection = client.get_collection(name)
    ts = int(time.time() * 1000)
    doc_id = f"{ts}_{role}"
    # We store the content as a document text; metadata holds role and timestamp
    collection.add(documents=[content], metadatas=[{'role': role, 'ts': ts}], ids=[doc_id])
    return doc_id


# Get messages ordered by timestamp (most recent last). Limit returns newest messages.


def get_page_messages(client, page_id, limit=40):
    name = f"page_{page_id}"
    collection = client.get_collection(name)
    # Chroma doesn't provide a straight 'order by ts' query; we fetch all and sort by metadata
    results = collection.get(include=['documents', 'metadatas'])  # Remove 'ids' - it's included by default
    docs = results.get('documents', [])
    metadatas = results.get('metadatas', [])
    ids = results.get('ids', [])  # IDs are included by default in newer ChromaDB versions
    messages = []
    for doc, meta, id_ in zip(docs, metadatas, ids):
        messages.append({'id': id_, 'role': meta.get('role'), 'content': doc, 'ts': meta.get('ts')})
    messages_sorted = sorted(messages, key=lambda x: x['ts'] or 0)
    return messages_sorted[-limit:]