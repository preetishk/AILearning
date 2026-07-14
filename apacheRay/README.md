# Apache Ray — Distributed Computing PoC

Experiments with [Apache Ray](https://ray.io) for parallel and distributed Python execution, combined with a SCIP-based code graph analysis toolchain and LLM-powered graph enrichment.

---

## Folder Structure

```
apacheRay/
├── src/
│   ├── rayExample.py           # Ray vs sequential retrieval benchmark
│   ├── rayFibonacci.py         # Ray vs local Fibonacci performance comparison
│   ├── dashboard.py            # Launch Ray with dashboard enabled
│   ├── enrich_graph.py         # LLM-enriched code knowledge graph (Ollama)
│   ├── build_readable_scip.py  # Parse SCIP index → human-readable JSON
│   ├── resolve_locals.py       # Resolve `local N` SCIP symbols to real names
│   ├── ast_names.py            # tree-sitter demo: extract identifiers from AST
│   ├── scip.proto              # SCIP protobuf schema
│   ├── scip_pb2.py             # Generated protobuf bindings
│   └── view_scip.ipynb         # Notebook: explore SCIP index interactively
├── Output/                     # Script output files (git-ignored)
└── graph-output/               # Generated graph JSON files (git-ignored)
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | |
| [Apache Ray](https://docs.ray.io/en/latest/ray-overview/installation.html) | `pip install ray` |
| [Ollama](https://ollama.com) | Required only for `enrich_graph.py` |
| tree-sitter | Required only for `ast_names.py` |

---

## Setup

```bash
pip install ray
pip install protobuf tree-sitter tree-sitter-python
```

---

## Running the Examples

### Basic Ray parallel retrieval
```bash
python src/rayExample.py
```
Compares sequential vs Ray-parallelised item retrieval with timing output.

### Fibonacci benchmark (local vs distributed)
```bash
python src/rayFibonacci.py
```
Benchmarks local vs Ray-distributed Fibonacci across all CPU cores.

### Ray Dashboard
```bash
python src/dashboard.py
```
Starts a Ray cluster and prints the dashboard URL (`http://127.0.0.1:8265` by default).

---

## Code Graph Tools

### Build a readable SCIP index
```bash
python src/build_readable_scip.py
# outputs: src/index.scip.json
```

### Resolve local symbols to variable names
```bash
cd src
python resolve_locals.py
```

### Enrich graph with LLM descriptions
```bash
python src/enrich_graph.py \
  --graph graph-output/graphify-out/graph.json \
  --src   src \
  --out   graph-output/graphify-out/enriched_graph.json \
  --model qwen3.5:9b
```
Requires Ollama running locally at `http://localhost:11434`. Override with `--ollama-url`.

---

## Key Concepts Demonstrated

| Script | Concept |
|---|---|
| `rayExample.py` | `@ray.remote` tasks, `ray.get()`, non-blocking calls |
| `rayFibonacci.py` | CPU-bound parallelism across `os.cpu_count()` workers |
| `dashboard.py` | Cluster resource introspection |
| `enrich_graph.py` | LLM + graph = self-contained code knowledge base |
| `build_readable_scip.py` | SCIP protobuf parsing |
