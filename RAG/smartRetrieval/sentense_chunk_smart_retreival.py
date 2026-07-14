import chromadb  # Our vector toy box library
from chromadb.utils import embedding_functions  # Word-to-math helper
import re  # For regex-based sentence splitting
import os  # For file handling
import argparse  # For command line arguments

# Simple sentence tokenizer function to avoid NLTK dependency
def simple_sentence_tokenize(text):
    """Split text into sentences using regex patterns"""
    # Basic pattern: Split on period, exclamation, or question mark followed by space
    # This is a simplified version - NLTK's sent_tokenize is more accurate for complex text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# Read text from a file and chunk it into sentences
def read_and_chunk_text(file_path):
    """Read text from a file and split it into sentence chunks."""
    if not os.path.exists(file_path):
        # Fallback to a default text if file doesn't exist
        print(f"File not found: {file_path}")
        print("Using default dinosaur text instead...")
        full_text = "Dinosaurs roamed Earth. T-Rex was fierce. It had big jaws. With sharp teeth. It hunted prey. Brachiosaurus was tall. It ate leaves. From high trees. It was gentle."
    else:
        with open(file_path, 'r', encoding='utf-8') as file:
            full_text = file.read()
    
    # Use our simple sentence tokenizer
    chunks = simple_sentence_tokenize(full_text)
    
    # Clean up any empty chunks and strip whitespace
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    
    return full_text, chunks

# Generate metadata for chunks
def generate_metadata(chunks):
    """
    Generate metadata for chunks including:
    - chunk_id: position in the list
    - next_chunk: ID of the next chunk or -1 if last
    - doc_id: derived from content (groups similar chunks)
    """
    metadatas = []
    
    # Simple document grouping logic based on content keywords
    # In a real app, you might use topic modeling or other NLP techniques
    for i, chunk in enumerate(chunks):
        # Default document ID
        doc_id = "general"
        
        # Simple rule-based document assignment (customize for your texts)
        chunk_lower = chunk.lower()
        if i == 0:
            doc_id = "intro"
        elif any(word in chunk_lower for word in ["rex", "jaws", "teeth", "hunted", "fierce"]):
            doc_id = "t_rex"
        elif any(word in chunk_lower for word in ["brachiosaurus", "tall", "leaves", "trees", "gentle"]):
            doc_id = "brachio"
        
        # Build metadata entry
        metadata = {
            "chunk_id": i,
            "next_chunk": i + 1 if i < len(chunks) - 1 else -1,
            "doc_id": doc_id
        }
        metadatas.append(metadata)
    
    return metadatas

# Perform similarity search with the given query
def perform_search(collection, search_query, k=3):
    """Perform similarity search with the given query"""
    results = collection.query(
        query_texts=[search_query],
        n_results=k  # Number of results to return
    )
    return results

# Main function to handle the text processing and search workflow
def main(file_path, search_query=None):
    """
    Main function that orchestrates the text processing and search workflow
    
    Parameters:
    - file_path: Path to the text file to process
    - search_query: Query string to search for (if None, will prompt for input)
    
    Returns:
    - List of expanded context results
    """
    # Step 1: Set up the DB
    client = chromadb.Client()
    collection = client.create_collection(name="text_chunks")
    
    # Step 2: Get the full text and chunks
    full_story, chunks = read_and_chunk_text(file_path)

    # Print information for debugging
    print(f"Loaded text with {len(chunks)} sentences")
    print(f"First few chunks: {chunks[:3]}")

    # Generate metadata based on our chunks
    metadatas = generate_metadata(chunks)

    # Step 3: Store with embeddings
    ef = embedding_functions.DefaultEmbeddingFunction()
    embeddings = [ef([chunk])[0] for chunk in chunks]
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    # Step 4: Handle search query
    if search_query is None:
        # Default query or get from user input
        default_query = "trees"
        search_query = input(f"Enter your search query (or press Enter for default '{default_query}'): ").strip() or default_query
    
    print(f"\nSearching for: '{search_query}'")

    # Get search results
    results = perform_search(collection, search_query, k=3)
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
        
    return full_contexts

# Run the script when executed directly
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process text and perform semantic search with smart retrieval.')
    parser.add_argument('--file', type=str, default="sample_text.txt", 
                        help='Path to the text file to process')
    parser.add_argument('--query', type=str, default=None,
                        help='Search query (if not provided, will prompt for input)')
    args = parser.parse_args()
    
    # Call the main function with parsed arguments
    main(args.file, args.query)