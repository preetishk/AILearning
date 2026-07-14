# Smart Retrieval with Text Chunking

This Python script demonstrates how to implement a smart retrieval system that:
1. Reads text from a file
2. Automatically chunks it into sentences
3. Stores text in a vector database (ChromaDB)
4. Performs semantic search on the text
5. Intelligently expands search results for better context

## Requirements

```
pip install chromadb
```

## How to Use

1. **Basic usage**:
   ```
   python sentense_chunk_smart_retreival.py
   ```
   This will use the default `sample_text.txt` file in the current directory.

2. **Use a custom text file**:
   ```
   python sentense_chunk_smart_retreival.py --file path/to/your/text_file.txt
   ```

3. When prompted, enter your search query or press Enter to use the default query.

## How It Works

### Text Processing
- The script reads text from a file
- Splits text into sentences using regex patterns
- Each sentence becomes a "chunk" for retrieval

### Smart Document Organization
- Chunks are automatically grouped into "documents" based on content
- Metadata tracks relationships between chunks
- This allows for context-aware retrieval

### Smart Retrieval
- When you search, the system returns the top K matching chunks
- For each match, it retrieves surrounding context (previous and next sentences)
- The system respects document boundaries to provide coherent contexts
- Special handling for introductory text ensures proper flow

### Features
- File-based input instead of hardcoded text
- Automatic sentence chunking
- Dynamic document organization based on content
- Smart retrieval with context expansion
- Command-line arguments for flexibility
- Interactive search queries

## Example

Given a text about dinosaurs, if you search for "trees", you'll get not just the sentence with "trees", but also surrounding context that maintains the coherence of the text.

## Customization

You can customize the script by:
- Modifying the document grouping logic in `generate_metadata()`
- Adjusting the regex pattern in `simple_sentence_tokenize()` for different languages
- Changing the number of results returned with the `k` parameter in `perform_search()`
