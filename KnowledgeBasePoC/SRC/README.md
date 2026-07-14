# Hybrid Knowledge Base

A production-grade **Graph + Vector** knowledge base that ingests source code, documentation, and wiki pages — then answers natural language questions using hybrid retrieval (Neo4j structural graph + ChromaDB semantic search).

## Architecture

```
Input (code / docs / wikis)
    │
    ▼
Pipeline ──── Walker → Chunker → Extractor (5-layer LLM) → Resolver → Hydrator
    │
    ├──► Neo4j Graph DB  (structural + behavioural knowledge graph)
    └──► ChromaDB        (6 semantic collections)
         │
         ▼
    Agent ──── Classifier → Graph Retriever + Vector Retriever + PagIndex → Assembler
         │
         ▼
    REST API  (FastAPI)    http://localhost:8000/docs
    MCP Server             http://localhost:3000/tools
```

## Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | |
| Neo4j | 5.x | Pre-installed, running at `bolt://localhost:7687` |
| ChromaDB | 0.5 | Installed via pip; uses HTTP or local persist |
| OpenAI | API key required | Set `OPENAI_API_KEY` |

## Quick Start

### 1 — Install dependencies

```bash
cd KnowledgeBasePoC/SRC
pip install -e ".[dev]"
```

### 2 — Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   NEO4J_URI=bolt://localhost:7687
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=your-password
```

### 3 — Set up Neo4j schema (once)

```bash
python scripts/create_schema.py
# or
kb schema
```

### 4 — Start the API server

```bash
kb serve --reload
# → http://localhost:8000/docs
```

### 5 — Ingest a codebase

```bash
# Via REST API
curl -X POST http://localhost:8000/api/ingest/repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo", "branch": "main"}'

# Check job status
curl http://localhost:8000/api/ingest/jobs/{job_id}
```

### 6 — Query

```bash
# Via CLI
kb query "What calls authenticate_user?"

# Via REST API
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the authentication rules?", "top_k": 10}'
```

## CLI Commands

```bash
kb serve        # Start REST API (default port 8000)
kb mcp          # Start MCP server (default port 3000)
kb query        # Run a one-shot query
kb resolve      # Run entity resolution on extracted JSON
kb hydrate      # Convert facts to graph triples
kb import-graph # Import triples into Neo4j
kb schema       # Create Neo4j schema (once)
```

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/ingest/file` | Upload file(s) |
| POST | `/api/ingest/repo` | Clone & ingest Git repo |
| POST | `/api/ingest/url` | Fetch & ingest URL |
| GET | `/api/ingest/jobs` | List ingest jobs |
| GET | `/api/ingest/jobs/{id}` | Job status |
| DELETE | `/api/ingest/jobs/{id}` | Cancel job |
| POST | `/api/query` | Hybrid RAG query |
| POST | `/api/graph/analyze` | Graph traversal query |
| GET | `/api/entities` | Browse entities |
| GET | `/api/entities/{id}` | Entity detail |
| POST | `/api/entities/{id}/summarize` | Regenerate LLM summary |
| GET | `/api/stats` | System statistics |
| GET | `/api/health` | Health check |

## MCP Tools (VS Code Copilot)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "kb": {
      "type": "http",
      "url": "http://localhost:3000"
    }
  }
}
```

| Tool | Description |
|------|-------------|
| `kb_query` | Natural language hybrid query |
| `kb_graph_query` | Graph traversal (impact, deps, neighbours) |
| `kb_find_entity` | Look up an entity by name |
| `kb_neighbors` | N-hop neighbourhood |
| `kb_impact_analysis` | Downstream change impact |
| `kb_stats` | System health stats |

## Project Structure

```
SRC/
├── cli.py                      # CLI entry point
├── pyproject.toml              # Python dependencies
├── .env.example                # Environment variable template
├── scripts/
│   └── create_schema.py        # One-time Neo4j schema setup
├── src/
│   ├── models/
│   │   └── facts.py            # All Pydantic models
│   ├── storage/
│   │   ├── protocols.py        # VectorStore + GraphStore protocols
│   │   ├── neo4j_store.py      # Neo4j implementation (primary)
│   │   ├── chroma_store.py     # ChromaDB implementation
│   │   ├── kuzu_store.py       # Kùzu embedded alternative
│   │   └── git_store.py        # Wiki Git repository
│   ├── pipeline/
│   │   ├── walker.py           # Source file walker
│   │   ├── chunker.py          # AST-aware chunker (tree-sitter)
│   │   ├── extractor.py        # 5-layer LLM extraction
│   │   ├── resolver.py         # Entity resolution + deduplication
│   │   ├── hydrator.py         # Facts → graph triples
│   │   └── job_manager.py      # Ingest job orchestrator
│   ├── adapters/
│   │   ├── git_ingester.py     # Git repo cloner
│   │   ├── file_ingester.py    # File upload + URL fetch
│   │   └── wiki_to_json.py     # OpenKB wiki → Chunks
│   ├── agent/
│   │   ├── classifier.py       # Intent classification
│   │   ├── graph_retriever.py  # Cypher-based graph retrieval
│   │   ├── vector_retriever.py # ANN vector retrieval
│   │   ├── pagindex.py         # Wiki concept tree retrieval
│   │   └── assembler.py        # Merge + rerank + generate answer
│   ├── api/
│   │   ├── main.py             # FastAPI app + middleware
│   │   ├── schemas.py          # API request/response models
│   │   └── routes/
│   │       ├── ingest.py       # Ingest endpoints
│   │       ├── query.py        # Query endpoints
│   │       ├── stats.py        # Stats + health endpoints
│   │       └── entities.py     # Entity browser endpoints
│   └── mcp/
│       └── server.py           # MCP tool server
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── test_chunker.py
    ├── test_extractor.py
    ├── test_resolver.py
    └── test_query.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | required | Neo4j password |
| `VECTOR_BACKEND` | `chroma` | `chroma` or `kuzu` |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8001` | ChromaDB port |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | Local ChromaDB path |
| `EMBEDDING_MODEL` | `text-embedding-3-large` | Embedding model |
| `LLM_MODEL` | `gpt-4o` | LLM model |
| `RAW_DOCS_DIR` | `./raw_docs` | Cloned/downloaded sources |
| `WIKI_DIR` | `./wiki` | Wiki repository |
| `API_PORT` | `8000` | REST API port |
| `CORS_ORIGINS` | `http://localhost:5173` | CORS allowed origins |
