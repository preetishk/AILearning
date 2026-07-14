import chromadb  # Our vector toy box library
from chromadb.utils import embedding_functions  # Word-to-math helper

# Step 1: Set up the DB (same as before)
client = chromadb.Client()
collection = client.create_collection(name="dino_story")

# Step 2: Chunk a longer story (to have more matches)
full_story = "Dinosaurs roamed Earth. T-Rex was fierce. It had big jaws. With sharp teeth. It hunted prey. Brachiosaurus was tall. It ate leaves. From high trees. It was gentle."
chunks = [  # Numbered chunks
    "Dinosaurs roamed Earth.",    # 0
    "T-Rex was fierce.",          # 1
    "It had big jaws.",           # 2
    "With sharp teeth.",          # 3
    "It hunted prey.",            # 4
    "Brachiosaurus was tall.",    # 5
    "It ate leaves.",             # 6
    "From high trees.",           # 7
    "It was gentle."              # 8
]

# Metadata with links and doc groups (assume two "docs": T-Rex and Brachio)
metadatas = [
    {"chunk_id": 0, "next_chunk": 1, "doc_id": "intro"},
    {"chunk_id": 1, "next_chunk": 2, "doc_id": "t_rex"},
    {"chunk_id": 2, "next_chunk": 3, "doc_id": "t_rex"},
    {"chunk_id": 3, "next_chunk": 4, "doc_id": "t_rex"},
    {"chunk_id": 4, "next_chunk": 5, "doc_id": "t_rex"},
    {"chunk_id": 5, "next_chunk": 6, "doc_id": "brachio"},
    {"chunk_id": 6, "next_chunk": 7, "doc_id": "brachio"},
    {"chunk_id": 7, "next_chunk": 8, "doc_id": "brachio"},
    {"chunk_id": 8, "next_chunk": -1, "doc_id": "brachio"}  # Using -1 instead of None
]

# Step 3: Store with embeddings
ef = embedding_functions.DefaultEmbeddingFunction()
embeddings = [ef([chunk])[0] for chunk in chunks]
collection.add(
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)

# Step 4: Search with K=3 (top 3 matches)
query = "trees" #"sharp teeth or tall dino"  # Something that might hit multiple
results = collection.query(
    query_texts=[query],
    n_results=3  # K=3!
)
matched_chunks = results['documents'][0]  # List of 3 chunks
matched_ids = results['ids'][0]  # e.g., ['chunk_3', 'chunk_5', 'chunk_2']
matched_metadatas = results['metadatas'][0]

print("Initial Top 3 Matches:")
for chunk in matched_chunks:
    print(chunk)  # Shows incomplete bits

# Step 5: Smart Retrieval for EACH of the K=3 matches!
full_contexts = []  # List to hold expanded for each
for i in range(len(matched_chunks)):
    match_id = int(matched_ids[i].split('_')[1])  # Get number, e.g., 3
    meta = matched_metadatas[i]
    doc_id = meta['doc_id']  # To keep within same doc
    
    # Grab previous (if exists) and next (via metadata)
    extra_chunks = []
    # Previous: Check if prev exists and same doc
    prev_id = match_id - 1
    if prev_id >= 0:
        prev_result = collection.get(ids=[f"chunk_{prev_id}"])
        if prev_result['metadatas'][0]['doc_id'] == doc_id:
            extra_chunks.append(prev_result['documents'][0])
    
    # Current match
    extra_chunks.append(matched_chunks[i])
    
    # Next: Use metadata from the current chunk
    next_id = meta.get('next_chunk')
    if next_id is not None and next_id != -1:  # Check for -1 which represents "no next chunk"
        next_result = collection.get(ids=[f"chunk_{next_id}"])
        # For chunk 0 (intro), always include the next chunk regardless of doc_id
        if match_id == 0 or next_result['metadatas'][0]['doc_id'] == doc_id:
            extra_chunks.append(next_result['documents'][0])
    
    # Merge for this match and add to list
    full_context = ' '.join(extra_chunks)
    full_contexts.append(full_context)

# Step 6: Output all expanded contexts (with dedup if needed)
print("\nFull Contexts After Smart Retrieval for K=3:")
for ctx in full_contexts:
    print(ctx)  # e.g., "It had big jaws. With sharp teeth. It hunted prey." for one match