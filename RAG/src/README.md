# RAG vs RAG+BM25 — Warranty Document Demo

Demonstrates why **hybrid retrieval (RAG + BM25)** outperforms **dense-only RAG** when queries contain exact keywords like SKU codes that carry no semantic meaning.

---

## Architecture

```
src/
├── data_generator.py   # Static warranty documents for 6 SKUs
├── ingest.py           # Loads docs into ChromaDB (vector store)
├── retriever.py        # RAGRetriever and HybridRetriever classes
├── llm.py              # Ollama llama3.1 LLM caller
├── main.py             # Demo runner — compares both strategies
└── requirements.txt    # Python dependencies
```

---

## Component Details

### `data_generator.py`
Contains `WARRANTY_DOCS` — a list of 6 realistic warranty documents for SKUs:

| SKU | Product |
|---|---|
| `LPT-2024-PRO` | Laptop Pro 15 (2024) |
| `PHN-X500-BLK` | Smartphone X500 Black |
| `TAB-8HD-SLVR` | Tablet 8 HD Silver |
| `HDR-NC700-WHT` | Noise Cancelling Headphones 700 White |
| `MNT-27QHD-BLK` | 27-inch QHD Monitor Black |
| `KBD-MECH-RGB` | Mechanical Keyboard RGB |

Each document contains: SKU code, warranty period, coverage, exclusions, and claim process.

---

### `ingest.py`
- Creates a **ChromaDB PersistentClient** at `./chroma_warranty_db`
- Uses ChromaDB's default embedding function (`all-MiniLM-L6-v2`, runs locally)
- Adds all 6 warranty docs with ids, content, and metadata (sku, title)
- Safe to re-run — drops and recreates the collection each time

---

### `retriever.py`
Contains two retrieval strategies:

#### `RAGRetriever` — Dense vector search only
```
Query → Embed → ChromaDB cosine similarity → Top-K docs
```

#### `HybridRetriever` — Dense + Sparse with Reciprocal Rank Fusion
```
Query → Embed  → ChromaDB (dense)  → ranked list A  ─┐
      → Tokenize → BM25 (sparse)  → ranked list B  ─┤→ RRF → Top-K docs
```

**Reciprocal Rank Fusion (RRF):**

$$score(d) = \sum_{i} \frac{1}{k + rank_i(d)}$$

where $k = 60$ (a smoothing constant). No score normalisation needed — works directly on rank positions. Final list is sorted by fused score descending.

The BM25 index is built in-memory from `WARRANTY_DOCS` at import time using `rank_bm25.BM25Okapi`.

---

### `llm.py`
- Calls **Ollama** (`http://localhost:11434`) with model `llama3.1`
- Prompt is strict: answer from provided context only; says "Not found" if context is insufficient
- This makes retrieval quality directly visible in the answer quality

---

### `main.py`
Runs three demo queries that expose the difference between strategies:

| Query | Why it matters |
|---|---|
| `"What are the exclusions for SKU KBD-MECH-RGB?"` | SKU code is a non-semantic token — BM25 exact-matches it, dense search may drift |
| `"How do I claim warranty for PHN-X500-BLK water damage?"` | Mix of exact code + semantic term — hybrid handles both |
| `"Which product has the longest warranty period?"` | Pure semantic concept — both strategies perform equally well |

For each query it prints:
1. Documents retrieved by **RAG-only** (SKU + title)
2. LLM answer from RAG-only context
3. Documents retrieved by **RAG+BM25**
4. LLM answer from RAG+BM25 context

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) running locally with `llama3.1` pulled:
  ```bash
  ollama pull llama3.1
  ollama serve          # starts on http://localhost:11434
  ```

---

## Setup & Run

```bash
# 1. Navigate to the src folder
cd RAG/src

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the demo (ingest + query + LLM comparison)
python main.py
```

To ingest only (no LLM):
```bash
python ingest.py
```

---

## Key Insight

> **BM25 is strong at exact-match recall; dense embeddings are strong at semantic similarity. Neither alone is optimal.**

SKU codes like `KBD-MECH-RGB` are opaque alphanumeric strings. An embedding model has no semantic knowledge of them, so cosine similarity between *"exclusions for KBD-MECH-RGB"* and the keyboard warranty document may be low. BM25 scores exact token overlap directly, so it reliably surfaces the right document.

Hybrid retrieval via RRF combines both signals without needing score normalisation, making it robust across both query types.
