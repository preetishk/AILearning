# Hybrid Knowledge Base UI — Design Spec

**Created:** 2026-06-09
**Status:** Draft
**Companion document:** `knowledge_base_hybrid_requirement.md` (backend pipeline, API, DB contracts)

---

## Problem

The Hybrid Knowledge Base pipeline ingests source files, Git repos, and URLs, then runs
a multi-stage extraction process (chunking → LLM extraction → entity resolution →
graph DB insert → vector DB embed). There is currently no way to observe this
process as it runs. Users must check logs manually, have no visibility into which stage
is active, and cannot tell whether a job is progressing or stuck.

Additionally, all input is CLI-only. Users cannot add new knowledge sources, run
queries, or see database statistics without dropping into a terminal.

---

## Goals

1. Replace all CLI interaction with a browser-based UI.
2. Show real-time pipeline stage progress after a source is submitted.
3. Let users submit sources: Git repo URL, file upload, web URL, image, video transcript, API spec.
4. Let users query the knowledge base with hybrid graph + vector retrieval and see cited results.
5. Show always-visible database health metrics (graph node count, vector doc counts).
6. Let users browse extracted entities, relationships, and community clusters.
7. Support path analysis, impact analysis, and dependency traversal through a UI.
8. Track knowledge versions by branch, tag, or commit SHA.
9. Expose the knowledge base to AI agents via MCP, REST, and GraphQL.

---

## Non-Goals (out of scope)

- Authentication or multi-user access control — single-user local tool only.
- Light/dark theme toggle — dark theme only.
- Real-time streaming of LLM tokens to the UI.
- Editing raw facts post-ingest (re-ingest to update).
- Scheduled automatic re-ingestion (user-triggered only).

---

## Coverage Matrix

This table maps the 20 capabilities from the product brief to the FRs in this spec.

| # | Capability | FR | Status |
|---|---|---|---|
| 1 | Multi-source ingestion (code, docs, PDF, Word, HTML) | FR-1, FR-2, FR-3 | ✅ MVP |
| 1a | Multi-source ingestion (images, videos, API specs) | FR-9 | ⏳ Post-MVP (FR-9.1/9.2); FR-9.3 API specs: MVP candidate |
| 2 | Metadata extraction and display | FR-10 | ✅ MVP |
| 3 | Structural entity extraction (classes, functions, sections) | FR-11 entity browser | ✅ MVP |
| 4 | Relationship extraction display | FR-11.3 detail panel | ✅ MVP |
| 5 | Knowledge graph construction and persistence | FR-11, FR-12 | ✅ MVP (FR-11); ⏳ Post-MVP (FR-12 visual) |
| 6 | Semantic embedding generation (Qdrant, Pinecone, Chroma, Weaviate) | Tech Stack — Vector DB | ✅ MVP |
| 7 | Incremental updates | FR-6 | ✅ MVP |
| 8 | Versioning and snapshot support (branch/tag/commit) | FR-13 | ✅ MVP (FR-13.1/13.2); ⏳ Post-MVP (FR-13.3–13.5 multi-version coexistence) |
| 9 | Hybrid retrieval (graph + vector combined) | FR-5 | ✅ MVP |
| 10 | Agent query interface via MCP | FR-19.1 | ✅ MVP |
| 11 | Path and dependency analysis | FR-14 | ✅ MVP |
| 12 | Natural language querying | FR-5, Query page | ✅ MVP |
| 13 | Semantic similarity search | FR-5.1 (vector mode) | ✅ MVP |
| 14 | Entity summarization | FR-15 | ✅ MVP |
| 15 | Provenance and traceability | FR-5.7, FR-16 | ✅ MVP |
| 16 | Knowledge traversal API | FR-14, FR-19 | ✅ MVP |
| 17 | Impact analysis | FR-14.5 | ✅ MVP |
| 18 | Community detection and clustering | FR-17 | ⏳ Post-MVP |
| 19 | Agent memory integration | FR-18 | ⏳ Post-MVP |
| 20 | Multi-agent consumption (MCP / REST) | FR-19.1, FR-19.2 | ✅ MVP |
| 20a | Multi-agent consumption (GraphQL) | FR-19.3 | ❌ Removed — REST + MCP sufficient |

---

## Functional Requirements

The following numbered requirements are the acceptance criteria for the full system (UI + backend together).
Each requirement must be implementable and testable.

### FR-1 Source Ingestion — File Upload `[MVP]`

| # | Requirement |
|---|---|
| FR-1.1 | The UI must present a drag-and-drop zone that accepts file uploads. Clicking the zone opens the OS file picker. |
| FR-1.2 | Supported file types: `.cs .cpp .h .ts .js .py .md .pdf .docx .json .yaml .yml`. Any other extension is rejected with an error message before the file is sent to the server. |
| FR-1.3 | After the user selects a file, the zone shows the filename and file size. |
| FR-1.4 | The backend stores the file in `RAW_DOCS_DIR`, then creates an `IngestJob` and returns `job_id` immediately without waiting for pipeline completion. |
| FR-1.5 | The pipeline selects the correct chunking strategy based on file extension: tree-sitter for code files, OpenKB adapter for PDF/DOCX/HTML, heading-splitter for Markdown. |

### FR-2 Source Ingestion — Git Repository `[MVP]`

| # | Requirement |
|---|---|
| FR-2.1 | The UI must present a URL input field for a Git repository HTTPS URL. |
| FR-2.2 | Optional fields: Branch (default `main`) and Path filter (e.g. `src/Libraries/`) to restrict ingestion to a subfolder. |
| FR-2.3 | Private repos are supported via token-prefixed URLs (`https://<TOKEN>@github.com/owner/repo`). The UI shows a hint explaining this format. |
| FR-2.4 | The backend clones the repo (shallow clone, `depth=1`) into `RAW_DOCS_DIR`, then starts the pipeline. If the repo was previously cloned, it fetches and hard-resets to the specified branch instead (incremental update — see FR-6). |
| FR-2.5 | Supports GitHub, GitLab, and Bitbucket HTTPS URLs. |

### FR-3 Source Ingestion — URL / Web Page `[MVP]`

| # | Requirement |
|---|---|
| FR-3.1 | The UI must present a URL input field for any HTTP/HTTPS URL (Confluence pages, docs sites, arbitrary web pages). |
| FR-3.2 | An optional Title field allows the user to label the source for display in the Jobs list. |
| FR-3.3 | The backend fetches the page content, passes it through the OpenKB URL adapter, and stores the compiled Markdown in the wiki directory before running the pipeline. |

### FR-4 Chunk Size Configuration `[MVP]`

| # | Requirement |
|---|---|
| FR-4.1 | The user must be able to set the maximum token size per chunk before submitting any source. |
| FR-4.2 | The UI exposes a "Max tokens per chunk" numeric input on all three ingest forms. Valid range: 256–4096. Default: 1500. |
| FR-4.3 | The value is sent to the backend as a `max_tokens` field on the ingest request body. |
| FR-4.4 | The backend passes `max_tokens` to `chunk_file()`. Chunks that exceed the limit after AST splitting are recursively sub-split at inner boundaries. |
| FR-4.5 | The last-used chunk size is persisted in `localStorage` so the user does not have to re-enter it on the next session. |

### FR-5 Dual-Store Query — Graph and Vector `[MVP]`

| # | Requirement |
|---|---|
| FR-5.1 | The query interface must support three retrieval modes, selectable by the user: **Graph only**, **Vector only**, **Both (default)**. |
| FR-5.2 | In "Both" mode, results from GraphRAG and Vector Search are merged on `graph_node_id` before ranking. The answer cites both sources. |
| FR-5.3 | The response displays which retrieval lanes were used (e.g. `graph + vector`, `vector only`). |
| FR-5.4 | The user can filter vector results by layer: L2 (behavioral), L3 (contract), L4 (operational), or all layers. |
| FR-5.5 | The user can filter vector results by source type: `code`, `document`, or both. |
| FR-5.6 | Graph-only queries accept Cypher-style entity names (e.g. `Namespace.Class.Method`) and return the N-hop neighbourhood. |
| FR-5.7 | Query results include, for each citation: source file path, line range, confidence level, relevance score, and a verbatim snippet. |

### FR-6 Incremental Update `[MVP]`

| # | Requirement |
|---|---|
| FR-6.1 | Re-submitting a previously ingested Git repo URL must not re-process unchanged files. The backend must compare file hashes against the last ingest run and only process changed or new files. |
| FR-6.2 | Re-submitting a file with the same name but different content must replace (not duplicate) the existing facts in both Graph DB and Vector DB. The node IDs and vector document IDs are deterministic (SHA-256 of canonical name / chunk ID), so re-running a MERGE upsert achieves this. |
| FR-6.3 | The Jobs page must show, for incremental runs, how many files were skipped (unchanged), updated, and added. |
| FR-6.4 | Deleted files are detected when re-ingesting a repo: facts whose `source_ref` no longer matches any current file are marked `stale=true` in Graph DB and flagged in the vector metadata. Stale facts are excluded from query results by default. |
| FR-6.5 | The user can trigger a full re-ingest (ignore cache) by checking a "Force full re-ingest" checkbox on the Git Repo form. |

### FR-7 Pipeline Visibility `[MVP]`

| # | Requirement |
|---|---|
| FR-7.1 | The UI must show the current pipeline stage in real time after source submission, updating at least every 2 seconds. |
| FR-7.2 | Stages shown: Scanning & Chunking → Extracting Facts → Provenance Enrichment → Entity Resolution → Graph DB Insert → Vector DB Embed & Insert. |
| FR-7.3 | Each completed stage shows a checkmark. The active stage shows a spinner. Failed stage shows a red cross. |
| FR-7.4 | Live counters update during the run: facts extracted, graph nodes written, vector documents written. |
| FR-7.5 | On failure, the error message from the pipeline is displayed verbatim in the UI. |

### FR-8 Database Health Metrics `[MVP]`

| # | Requirement |
|---|---|
| FR-8.1 | A stats bar must be visible at the bottom of every page, showing: graph node count, graph edge count, total vector document count, entity registry size, total sources ingested, last ingest timestamp. |
| FR-8.2 | Stats must update automatically every 30 seconds without a page reload. |
| FR-8.3 | A per-collection breakdown of vector document counts must be accessible (shown in the stats bar or on a hover/tooltip). |

### FR-9 Extended Source Types `[Post-MVP]` _(FR-9.1 images and FR-9.2 video transcripts add OCR/parsing infra for near-zero fact value in a code-first KB; FR-9.3 API specs are the only sub-item recommended for MVP consideration)_

| # | Requirement |
|---|---|
| FR-9.1 | Image and diagram files (`.png`, `.jpg`, `.svg`, `.drawio`) are accepted for upload. The backend extracts alt-text, filenames, and any embedded text/labels, stores them as `DocumentSection` facts. Diagrams with no extractable text are stored as provenance-only records. |
| FR-9.2 | Video transcript files (`.vtt`, `.srt`, `.txt` subtitles) are accepted for upload. The pipeline treats them as plain-text documents and chunks by timestamp boundaries. |
| FR-9.3 | API specification files (`.json` OpenAPI / `.yaml` AsyncAPI) are accepted for upload. The pipeline routes them through the direct LLM pass (no AST splitting) and extracts endpoint names, parameters, schemas, and response codes as `EntityContract` facts. |
| FR-9.4 | The ingest form's drag-and-drop zone and the supported extensions list update to reflect FR-9.1–FR-9.3 additions. |

### FR-10 Metadata Extraction and Display `[MVP]`

| # | Requirement |
|---|---|
| FR-10.1 | For every ingested source the pipeline must extract and store structured metadata: for code — language, module name, author (from git blame), last modified; for documents — title, version, author, page count; for URLs — page title, domain, fetch date. |
| FR-10.2 | The Jobs page detail view (accessible by clicking a job row) must show the metadata extracted for that source in a readable key-value list. |
| FR-10.3 | Metadata fields are searchable from the Query page via the source-type filter. |

### FR-11 Entity Browser `[MVP]`

| # | Requirement |
|---|---|
| FR-11.1 | The application must expose an **Entities** page (route `/entities`) accessible from the sidebar. |
| FR-11.2 | The page shows a searchable, paginated table of all entities in the knowledge graph: canonical name, kind (class, function, interface, etc.), source file, confidence. |
| FR-11.3 | Clicking an entity row opens a detail panel showing: canonical name, all aliases, kind, source reference with line range, summary (if available), and all direct relationships (both inbound and outbound edges with edge type and target name). |
| FR-11.4 | The entity table supports filtering by kind (class / function / interface / enum / other) and by source type (code / document). |
| FR-11.5 | A "Find similar" button on the detail panel submits a vector similarity search for that entity and displays results inline. |

### FR-12 Graph Visualization `[Post-MVP]` _(requires a graph rendering library such as `react-force-graph`; adds ~1 week of front-end work; the entity detail panel's text relationship list covers the same need for MVP)_

| # | Requirement |
|---|---|
| FR-12.1 | The Entity detail panel (FR-11.3) must include a **Graph view** toggle that renders the entity's N-hop neighbourhood as an interactive node-link diagram (default depth: 2 hops). |
| FR-12.2 | Nodes are colour-coded by kind: Entity (blue), Outcome (orange), Event (purple), Rule (yellow). |
| FR-12.3 | Edge labels display the relationship type (e.g. `CALLS`, `EMITS`). |
| FR-12.4 | Clicking a node in the graph view navigates to that entity's detail panel. |
| FR-12.5 | The user can increase the hop depth (1–4) via a slider. The graph re-fetches and re-renders on change. |
| FR-12.6 | A "Export as SVG" button downloads the current graph view. |

### FR-13 Versioning and Snapshot Support `[Post-MVP — simplified]` _(FR-13.1 branch/tag/SHA checkout and FR-13.2 Ref column are MVP-safe; FR-13.3–13.5 multi-version coexistence in the graph multiplies node counts and complicates every query — defer until there is a concrete need to query two versions simultaneously)_

| # | Requirement |
|---|---|
| FR-13.1 | When ingesting a Git repo, the user may specify a branch name, tag, or full commit SHA in the Branch field. The backend checks out exactly that ref before cloning/extracting. |
| FR-13.2 | The Jobs page must record, for each repo ingest, the branch/tag/commit SHA that was ingested. This appears as a "Ref" column in the jobs table. |
| FR-13.3 | Multiple versions of the same repo may coexist in the knowledge graph. Nodes from different versions carry a `version_ref` property (branch/tag/SHA). |
| FR-13.4 | The Query page allows the user to optionally scope a query to a specific version ref via a text input labelled "Version / branch / tag (optional)". |
| FR-13.5 | The entity browser (FR-11) shows a "Version" column and can filter by version ref. |

### FR-14 Path and Dependency Analysis `[MVP]`

| # | Requirement |
|---|---|
| FR-14.1 | The Query page must include a **Graph Analysis** sub-mode (accessible as a fourth option alongside the retrieval mode selector). |
| FR-14.2 | In Graph Analysis mode the user specifies: a **Source entity** (text input, autocompleted from known entity names), a **Target entity** (text input), and an **Analysis type** selector with options: Shortest path / All paths / Impact analysis / Reverse dependencies. |
| FR-14.3 | **Shortest path**: returns the shortest chain of relationships between source and target, displayed as `A → [CALLS] → B → [EMITS] → C`. |
| FR-14.4 | **All paths** (up to depth 4): returns every path, listed in order of length. |
| FR-14.5 | **Impact analysis**: given the source entity, returns all entities reachable downstream via `CALLS`, `EMITS`, `LEADS_TO` edges (i.e. "what breaks if I change this?"). Displayed as an indented tree. |
| FR-14.6 | **Reverse dependencies**: given the source entity, returns all entities that depend on it upstream (i.e. "what calls this?"). Displayed as an indented tree. |
| FR-14.7 | Each result in analysis mode includes the source reference and line range for every node in the path. |

### FR-15 Entity Summarization `[MVP]`

| # | Requirement |
|---|---|
| FR-15.1 | The entity detail panel (FR-11.3) must include a **Summary** section showing an LLM-generated one-paragraph description of the entity's purpose, created at ingest time. |
| FR-15.2 | Summaries are generated for all Layer-1 entities (classes, functions, interfaces) during the provenance enrichment step (pipeline step 3). |
| FR-15.3 | The summary is stored as a property on the Graph DB node and as the first sentence of the vector document text for that entity. |
| FR-15.4 | The user can request a "Regenerate summary" for a single entity from the detail panel. This calls `POST /api/entities/{id}/summarize` and refreshes the panel without re-running the full pipeline. |

### FR-16 Provenance and Traceability `[MVP]`

| # | Requirement |
|---|---|
| FR-16.1 | Every entity detail panel (FR-11.3) must show a **Provenance** section listing: source file path, start/end line, git commit SHA (if available), extraction date, confidence level. |
| FR-16.2 | Every citation card in query results (Query page) must include a "View source" link that, when clicked, opens the provenance detail for that fact. |
| FR-16.3 | The pipeline must record, for each fact, the exact LLM prompt layer that produced it (L1–L5) and the chunk ID it was extracted from. These are stored in the `evidence` metadata of the vector document. |
| FR-16.4 | The entity browser (FR-11) must provide a "Re-index this entity" button that re-runs the pipeline for the single source file containing that entity, without re-processing other files. |

### FR-17 Community Detection and Clustering `[Post-MVP]` _(requires Neo4j GDS plugin or networkx post-processing; significant memory overhead on local machines; useful insight but not needed for core query/browse workflows)_

| # | Requirement |
|---|---|
| FR-17.1 | The application must expose a **Domains** page (route `/domains`) accessible from the sidebar. |
| FR-17.2 | The backend must run a community detection algorithm (Louvain or label propagation via Neo4j GDS or networkx) over the entity graph and group entities into named domains. This runs automatically at the end of each full ingest. |
| FR-17.3 | The Domains page displays detected communities as cards: community name (auto-generated from the top 3 most-connected entities), entity count, and a "View entities →" link to the entity browser pre-filtered for that community. |
| FR-17.4 | Detected communities are stored as `Domain` nodes in the graph, connected to member entities via `BELONGS_TO` edges. |
| FR-17.5 | The entity detail panel (FR-11.3) shows which domain the entity belongs to, with a link to the Domains page. |

### FR-18 Agent Memory Integration `[Post-MVP]` _(adds a new vector collection, graph node type, and API endpoint; low value for a single-user tool where the user can simply re-ask; revisit when agents are actively writing feedback into the KB)_

| # | Requirement |
|---|---|
| FR-18.1 | The system must store agent observations and feedback as first-class knowledge objects. An observation is a tuple `{question, answer, agent_id, timestamp, feedback}`. |
| FR-18.2 | The `POST /api/memory` endpoint accepts an observation and stores it in a `AgentMemory` vector collection and as an `Observation` node in the graph. |
| FR-18.3 | The Query page must include a "Save this answer" button. Clicking it stores the question, the generated answer, and the citations as an observation (FR-18.1). |
| FR-18.4 | Past observations are retrievable via vector similarity search — if a new question is semantically close to a stored observation, the assembler includes the stored answer as an additional high-confidence citation. |
| FR-18.5 | The Jobs page includes an "Agent Memory" row type (source_type = `memory`) for jobs that indexed observations from external agents. |

### FR-19 Multi-Agent and API Exposure `[MVP — FR-19.1 and FR-19.2 only; FR-19.3 removed]` _(FR-19.1 MCP and FR-19.2 REST are already specified in the requirement doc §18 and §15; FR-19.3 GraphQL is removed — REST + MCP covers all listed agent consumers with no added library dependency; FR-19.4–19.6 apply only to the two retained interfaces)_

| # | Requirement |
|---|---|
| FR-19.1 | The system must expose an MCP (Model Context Protocol) server on a separate port (default 3000). Tools exposed: `kb_query`, `kb_graph_query`, `kb_find_entity`, `kb_neighbors`, `kb_impact_analysis`, `kb_stats`. Full schemas in requirement doc §18. |
| FR-19.2 | All API endpoints must be accessible via REST (FastAPI, port 8000). An OpenAPI schema is served at `GET /docs`. |
| FR-19.3 | A GraphQL endpoint (`POST /graphql`) is exposed for graph traversal queries. Supported queries: `entity(id)`, `neighbors(id, depth)`, `path(from, to)`, `entities(filter)`, `domains`. |
| FR-19.4 | All three interfaces (REST, MCP, GraphQL) share the same backend business logic — they are thin routing layers over `src/agent/`. |
| FR-19.5 | The application Settings page (route `/settings`) must display the MCP server URL and the REST base URL, with a copy button for each, so agents can be configured easily. |
| FR-19.6 | The system must support concurrent requests from multiple agents. The in-memory job store is read-only from the query side; no locking is needed for reads. Write operations (ingest) are serialised per `source_label` to prevent duplicate ingest races. |

---

## Tech Stack

### Frontend

| Concern | Choice | Version | Notes |
|---|---|---|---|
| UI framework | React + TypeScript | 18 / 5 | Component-based SPA |
| Build tool | Vite | 5 | Dev proxy to `/api`, builds to `ui/dist/` |
| Styling | Tailwind CSS | 3 | Dark-only utility classes |
| Server state & polling | TanStack Query | v5 | Caches responses; drives poll loop |
| Routing | React Router | v6 | Client-side SPA routing |
| Icons | lucide-react | latest | — |
| Toasts | react-hot-toast | latest | Error and success notifications |
| Serving | FastAPI static files from `ui/dist/` | — | No separate web server needed |

All TypeScript types mirror the Pydantic models in `knowledge_base_hybrid_requirement.md` §15.3.
All fetch wrappers are in `ui/src/api/client.ts` as defined in requirement §15.0.

### Backend API

| Concern | Choice | Version | Notes |
|---|---|---|---|
| Language | Python | 3.11+ | Type-annotated throughout |
| API framework | FastAPI | 0.111+ | Async, automatic OpenAPI docs at `/docs` |
| Data validation | Pydantic | v2.7+ | All request/response models |
| ASGI server | Uvicorn | 0.29+ | Single process for local; Gunicorn+Uvicorn for production |
| Background tasks | FastAPI `BackgroundTasks` | — | Runs pipeline stages without blocking the HTTP response |
| Containerisation | Docker + docker-compose | — | Full stack: API + Neo4j + ChromaDB |

### Transformation & Integration Pipeline

| Concern | Choice | Version | Notes |
|---|---|---|---|
| Language | Python | 3.11+ | Same process as the API server |
| Code chunking | tree-sitter + tree-sitter-languages | 0.22+ / 1.10+ | AST-aware splits at class/method boundaries |
| Token counting | tiktoken | 0.7+ | Enforces `max_tokens` per chunk |
| LLM extraction | OpenAI Python SDK | 1.x | `gpt-4o` default; temperature=0.0 for all extraction |
| Local LLM (optional) | Ollama | — | Drop-in for air-gapped environments |
| Git cloning | gitpython | 3.x | `clone_repo()` in `src/adapters/git_ingester.py` |
| Document pre-processing | OpenKB / VectifyAI | — | Confluence, PDF, Word → structured Markdown wiki pages |
| Entity resolution | Custom + scikit-learn | 1.4+ | Cosine similarity clustering for alias detection |

### Graph Database

| Property | Detail |
|---|---|
| **Primary choice** | **Neo4j 5.20** — full ACID, Cypher query language, Browser UI at `http://localhost:7474` |
| **Embedded alternative** | **Kùzu** — no Docker needed, same Cypher dialect, good for local dev |
| **Connection** | `bolt://localhost:7687` (local Docker) or `neo4j+s://<instance>.databases.neo4j.io` (Aura cloud) |
| **Auth** | `NEO4J_USER` + `NEO4J_PASSWORD` from `.env` |
| **Schema** | Nodes: `Entity`, `Outcome`, `Event`, `Rule`. Edges: `CALLS`, `IMPLEMENTS`, `EMITS`, `PRODUCES`, `RESOLVED_BY`, `LEADS_TO`, etc. — full list in requirement §4.3 |
| **Node ID** | `SHA-256[:16]` of `canonical_name` — stable, deterministic, used as the bridge key |
| **Write strategy** | `MERGE`-based upserts — safe to re-run the pipeline; idempotent |
| **Indexes** | Uniqueness constraint on `Entity.id`; composite index on `canonical_name + source_type` |
| **Switch** | Set `GRAPH_BACKEND=neo4j` or `GRAPH_BACKEND=kuzu` in `.env` — no code change needed |

### Vector Database

| Property | Detail |
|---|---|
| **Default choice** | **ChromaDB 0.5** — local persistent, no API key, HTTP mode via Docker |
| **Alternatives** | Weaviate 1.25, Qdrant 1.9, Pinecone (cloud) — all behind the same `VectorStore` protocol |
| **Collections** | 6 fixed collections: `BehavioralRule`, `EntityContract`, `OutcomeRecord`, `ObservableEvent`, `OperationalTrace`, `DocumentSection` |
| **Embedding model** | `text-embedding-3-large` (OpenAI, 3072d) default; `nomic-embed-text` (Ollama) for local dev |
| **Bridge field** | Every vector document carries `graph_node_id` — the SHA-256[:16] of its canonical entity name — so graph and vector results can be joined at query time |
| **Switch** | Set `VECTOR_BACKEND=chroma` / `weaviate` / `pinecone` / `qdrant` in `.env` — no code change needed |

---

## Application Structure

Seven pages reachable from a persistent left sidebar, plus a stats bar pinned to the bottom:

| Page | Route | Purpose |
|---|---|---|
| Ingest | `/ingest` (default `/`) | Submit sources, watch live progress |
| Jobs | `/jobs` | Full job history with status and progress |
| Query | `/query` | Natural language queries, graph analysis, similarity search |
| Entities | `/entities` | Browse extracted entities and their relationships |
| Domains | `/domains` | Community clusters detected from the entity graph |
| Graph Explorer | `/graph` | Visual interactive node-link graph viewer |
| Settings | `/settings` | MCP URL, REST base URL, API keys display |

---

## Page 1: Ingest

### Input modes — tab group

**Tab 1 — Git Repo (default tab)**

- Required URL field: "Repository URL". Placeholder: `https://github.com/owner/repo`.
- A hint below the field: private repos accept a token-prefixed HTTPS URL.
- Optional text field: "Branch". Default value shown: `main`.
- Optional text field: "Path filter" — restricts ingestion to a subfolder, e.g. `src/Libraries/`. Label suffix: `(optional)`.
- Numeric input: "Max tokens per chunk". Range 256–4096, default 1500. Persisted in `localStorage`.
- Checkbox: "Force full re-ingest" — unchecked by default. When unchecked, only changed/new files are processed (incremental). When checked, all files are re-processed regardless of prior run.
- Submit button: "Start Ingestion".

**Tab 2 — Upload File**

- A drag-and-drop zone. Clicking it opens the OS file picker.
- The zone shows the list of supported extensions while empty.
- Once a file is selected, the zone shows the filename and file size instead.
- Numeric input: "Max tokens per chunk". Range 256–4096, default 1500. Persisted in `localStorage`.
- Submit button: "Upload & Ingest". Disabled until a file is chosen.
- Supported extensions: `.cs .cpp .h .ts .js .py .md .pdf .docx .json .yaml .yml`

**Tab 3 — URL**

- Required URL field: "Page URL". Intended for Confluence pages, docs sites, any public web page.
- Optional text field: "Title". Used only for display in the jobs list.
- Numeric input: "Max tokens per chunk". Range 256–4096, default 1500. Persisted in `localStorage`.
- Submit button: "Ingest URL".

### Form validation

- All required fields are checked before the API is called. Empty required field → toast error, no API call.
- "Max tokens per chunk" must be an integer between 256 and 4096. Out-of-range value → toast error.
- Submit button is disabled while a request is in-flight.
- A backend error (non-2xx response) shows a toast error with the server's message.

### Live progress panel

The panel appears below the form immediately after a successful job submission.
It stays visible until the user dismisses it (a "Dismiss" button appears once the job reaches a terminal state).
"View all jobs →" link is always visible inside the panel, navigating to `/jobs`.

The panel contains, from top to bottom:

1. **Header row** — status badge + source label + source type + job ID (small, monospace) + "View all jobs →" link + "Dismiss" button (terminal state only).
2. **Overall progress bar** — horizontal bar 0–100%. Colour by status: indigo = running, green = done, red = failed, grey = queued.
3. **Step stepper** — six steps listed vertically (see Pipeline Stages below).
4. **Live counters** — shown once any counter exceeds zero: Facts extracted / Graph nodes / Vector docs.
5. **Error box** — red monospace box showing `error` field when status is `failed`.
6. **Success summary** — green box with final counter values when status is `done`.

**Polling:** the panel calls `GET /api/ingest/jobs/{job_id}` every 1.5 seconds.
Polling stops automatically when `status` is `done` or `failed`.

### Pipeline stages — stepper behaviour

Six stages, displayed in order. Each stage is in one of three visual states:

| State | Condition | Visual |
|---|---|---|
| Upcoming | Step index > active step | Grey hollow circle |
| Active | Step index = active step | Spinning indigo ring; raw `current_step` string shown in small monospace |
| Completed | Step index < active step, or `status = done` | Solid green checkmark; sub-label visible |

The connector line between two adjacent steps turns green once the upper step completes.
If the job fails, the active step turns red.

| Step | Matches `current_step` prefix | Display label | Sub-label |
|---|---|---|---|
| 1 | `Step 1` | Scanning & Chunking | Walking source files, splitting into chunks |
| 2 | `Step 2` | Extracting Facts | Running LLM prompts for layers 1–4 |
| 3 | `Step 3` | Provenance Enrichment | Attaching source location and evidence |
| 4 | `Step 4` | Entity Resolution | Deduplicating names, building alias registry |
| 5 | `Step 5` | Graph DB Insert | Writing nodes and edges to graph database |
| 6 | `Step 6` | Vector DB Embed & Insert | Embedding and upserting into vector collections |

Matching is prefix-based (`startsWith`), not exact equality — the backend step 2 string includes a variable layer number (e.g. `"Step 2/6 — Extracting layer 2 / 4"`).

### Acceptance criteria — Ingest page

- [ ] Submitting a valid Git repo URL queues a job and the progress panel appears within 1 second.
- [ ] The progress bar advances as `progress_pct` increases on subsequent polls.
- [ ] While the backend `current_step` starts with `"Step 5"`, the stepper shows steps 1–4 as completed (green checkmarks) and step 5 as active (spinning ring).
- [ ] The raw step string (e.g. `"Step 5/6 — Writing to graph database"`) is visible in small monospace under the step 5 label while it is active.
- [ ] Uploading a `.cs` file succeeds. Uploading an unsupported extension shows a toast error.
- [ ] The \"Max tokens per chunk\" value of 512 is sent as `max_tokens: 512` in the request body.
- [ ] The \"Max tokens per chunk\" value persists across page reloads (stored in `localStorage`).
- [ ] Checking \"Force full re-ingest\" sends `force: true` in the request body.
- [ ] With \"Force full re-ingest\" unchecked, re-submitting an already-ingested repo sends `force: false` and the job counters show fewer files processed than a full run.
- [ ] Dismissing a completed panel clears it without navigating away.
- [ ] The counters (facts / nodes / vectors) increase during a run without a page reload.

---

## Page 2: Jobs

### Overview

A table of all jobs, sorted newest first. Intended for reviewing past ingestions and monitoring multiple concurrent jobs.

### Table columns

| Column | Notes |
|---|---|
| Source | Truncated at ~20 chars; full value on hover |
| Type | `file` / `repo` / `url` |
| Status | Coloured badge — Queued (grey) / Running (indigo, pulsing) / Done (green) / Failed (red) |
| Progress | Mini progress bar + percentage |
| Current Step | Raw `current_step` string, truncated |
| Started | Localised date-time, or `—` if not yet started |

### Behaviour

- The page auto-polls `GET /api/ingest/jobs` every 3 seconds while any job has status `queued` or `running`. Stops once all jobs are terminal.
- Empty state: message with a link to the ingest page.
- A "+ Add source" link in the page header navigates to `/ingest`.

### Acceptance criteria — Jobs page

- [ ] A job submitted on the ingest page appears in the table without a manual page reload.
- [ ] The table stops polling automatically once all jobs are `done` or `failed`.
- [ ] A `running` job shows a pulsing indigo status badge.
- [ ] Progress bar and percentage update every ~3 seconds during a running job.

---

## Page 3: Query

### Layout

1. Single-line text input, placeholder: "Ask anything about the codebase…"
2. **Retrieval mode** selector — three options (radio buttons or segmented control):
   - **Both (default)** — GraphRAG + Vector Search, results merged on `graph_node_id`.
   - **Graph only** — Cypher-based traversal; best for structural questions ("What calls X?").
   - **Vector only** — ANN search; best for semantic questions ("Find code similar to…").
3. **Layer filter** (multi-select, visible when mode is "Vector only" or "Both"):
   - All layers (default)
   - L2 — Behavioral rules
   - L3 — Contracts & outcomes
   - L4 — Operational traces & documents
4. **Source type filter** (multi-select, visible when mode is "Vector only" or "Both"):
   - All (default)
   - Code
   - Document
5. "Top K" selector: options 5, 10, 20.
6. "Ask" button — disabled while a request is in-flight.
7. Answer panel (appears after response):
   - Answer text.
   - Overall confidence badge — colour-coded (green ≥ 75%, yellow 45–74%, red < 45%).
   - "✓ grounded" label if `answer_grounded` is true.
   - Small labels: question type (e.g. `structural`) and retrieval lanes used (e.g. `graph + vector`).
8. Citations section (appears if `citations` is non-empty):
   - Section header: "Citations (N)".
   - One card per citation showing: source file path, line range, relevance score percentage, confidence label, source snippet (monospace, clamped to 4 lines).

### Acceptance criteria — Query page

- [ ] Submitting a question in "Both" mode returns an answer that cites both graph and vector sources when both are relevant.
- [ ] Selecting "Graph only" sends `retrieval_mode: "graph"` in the request body; the response `retrieval_lanes_used` contains only `"graph"`.
- [ ] Selecting "Vector only" with layer filter set to "L2" sends `filter_layer: 2` in the request body.
- [ ] Each citation card shows a source path and line numbers.
- [ ] The "Ask" button is disabled while the request is pending.
- [ ] A network or API error shows a toast, not an unhandled crash.

---

## Stats Bar (always visible)

Pinned to the bottom of the app shell on all pages. Never navigates away.

Displays:
- Graph nodes (integer)
- Graph edges (integer)
- Vector docs (sum across all 6 collections)
- Entities (entity registry size)
- Sources (total sources ingested)
- Last ingest (ISO timestamp, right-aligned; hidden if null)

Polls `GET /api/stats` every 30 seconds.

### Acceptance criteria — Stats bar

- [ ] After a successful ingest the graph node count and vector doc count increase within 30 seconds without a page reload.
- [ ] The bar is visible on all three pages without scrolling.

---

## Polling Contract

| Step | Action |
|---|---|
| 1 | User submits → `POST /api/ingest/{file\|repo\|url}` → response contains initial `IngestJob` state with `job_id` |
| 2 | UI renders progress panel immediately from the initial response |
| 3 | UI polls `GET /api/ingest/jobs/{job_id}` every 1.5 s |
| 4 | Each response contains `status`, `progress_pct`, `current_step`, and counters |
| 5 | When `status` is `done` or `failed`, UI stops polling and shows the final state |

Progress never goes backward in the UI. If `progress_pct` somehow decreases, the bar renders `max(0, min(100, pct))`.

---

## Job Object — UI-relevant fields

Defined fully in `knowledge_base_hybrid_requirement.md` §15.3 (`JobStatusResponse`).

| Field | Type | Used for |
|---|---|---|
| `job_id` | string (UUID) | Polling key |
| `status` | `queued` / `running` / `done` / `failed` | Colours, polling gate, dismiss button |
| `source_label` | string | Shown in panel header and jobs table |
| `source_type` | `file` / `repo` / `url` | Type badge |
| `progress_pct` | float 0–100 | Progress bar width |
| `current_step` | string | Stepper prefix matching + monospace label |
| `facts_extracted` | int | Counter |
| `nodes_written` | int | Counter |
| `vectors_written` | int | Counter |
| `files_total` | int | Incremental update display |
| `files_changed` | int | Incremental update display |
| `files_skipped` | int | Incremental update display |
| `error` | string or null | Error box |
| `started_at` | ISO string or null | Jobs table |
| `completed_at` | ISO string or null | Jobs table |

## Ingest Request Fields — additions over the base spec

These fields are added to all three ingest request bodies (file, repo, URL) beyond what is defined in the requirement doc §15.2:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `max_tokens` | int (256–4096) | 1500 | Max tokens per chunk passed to `chunk_file()` |
| `force` | bool | `false` | Git repo only: `true` = full re-ingest, `false` = incremental |
| `retrieval_mode` | `"both"` / `"graph"` / `"vector"` | `"both"` | Query only: which retrieval lanes to activate |
| `filter_layer` | int or null | null | Query only: restrict vector search to a specific extraction layer |
| `filter_source_type` | `"code"` / `"document"` / null | null | Query only: restrict vector search to a source type |

---

## Open Questions

1. **Concurrent jobs** — should the ingest page stack multiple progress panels (one per submitted job), or show only the most recently submitted job with a link to `/jobs` for the rest?
2. **Cancel button** — the backend supports `DELETE /api/ingest/jobs/{job_id}`. Should the Jobs page expose this as a button on running jobs?
3. **Pagination** — the jobs table shows all jobs. If the list grows large, should it paginate or show only the last N?
4. **Cloning pre-step** — large repos take minutes to clone before step 1 starts. Should the UI show an explicit "Cloning repository…" pre-step, or is showing 0% / "Queued" acceptable during that wait?
