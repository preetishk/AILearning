"""
Enriches graph.json nodes with LLM-generated descriptions so the knowledge
graph is self-contained -- no source files needed after this step.

Usage:
    python src/enrich_graph.py \
        --graph graph-output/graphify-out/graph.json \
        --src   src \
        --out   graph-output/graphify-out/enriched_graph.json \
        --model qwen3.5:9b
"""
import json
import argparse
import os
import urllib.request
import urllib.error

# ── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--graph", default="graph-output/graphify-out/graph.json")
parser.add_argument("--src",   default="src")
parser.add_argument("--out",   default="graph-output/graphify-out/enriched_graph.json")
parser.add_argument("--model", default="qwen3.5:9b")
parser.add_argument("--ollama-url", default="http://localhost:11434")
args = parser.parse_args()

# ── Load graph ───────────────────────────────────────────────────────────────
with open(args.graph) as f:
    graph = json.load(f)

# ── Load source files into memory ────────────────────────────────────────────
source_cache = {}
for root, _, files in os.walk(args.src):
    for fname in files:
        if fname.endswith(".py"):
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8") as f:
                source_cache[fname] = f.readlines()

def get_source_snippet(source_file, source_location, context_lines=15):
    """Extract lines around the given location from source."""
    lines = source_cache.get(source_file)
    if not lines:
        return None
    # source_location is like "L9" or "L9-L20"
    try:
        start = int(source_location.lstrip("L").split("-")[0]) - 1
    except (ValueError, IndexError):
        return None
    end = min(start + context_lines, len(lines))
    return "".join(lines[start:end])

# ── Ollama call ───────────────────────────────────────────────────────────────
def ask_ollama(prompt, model):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{args.ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())["response"].strip()

# ── Enrich each node ──────────────────────────────────────────────────────────
print(f"Enriching {len(graph['nodes'])} nodes with {args.model}...\n")

for node in graph["nodes"]:
    if node.get("file_type") == "rationale":
        # already has text content in its label
        node["description"] = node["label"]
        print(f"  [skip-rationale] {node['id']}")
        continue

    snippet = get_source_snippet(
        node.get("source_file", ""),
        node.get("source_location", "L1")
    )

    if not snippet:
        node["description"] = node["label"]
        print(f"  [no-source] {node['id']}")
        continue

    prompt = f"""You are a code documentation assistant. Given this Python code snippet, write a concise knowledge description (3-5 sentences) that captures:
- What this code does
- Key parameters and return values (if a function)
- Any important side effects or dependencies
- The purpose/role in the larger system

Do NOT include the code itself. Write plain prose only.

Code ({node['source_file']} {node['source_location']}):
```python
{snippet}
```

Description:"""

    print(f"  [enriching] {node['id']} ...", end=" ", flush=True)
    try:
        description = ask_ollama(prompt, args.model)
        node["description"] = description
        print("done")
    except Exception as e:
        node["description"] = node["label"]
        print(f"ERROR: {e}")

# ── Save enriched graph ───────────────────────────────────────────────────────
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2)

print(f"\nSaved enriched graph to: {args.out}")

# ── Show a sample ─────────────────────────────────────────────────────────────
print("\n--- Sample node (retrieve()) ---")
for node in graph["nodes"]:
    if "retrieve" in node["id"] and "task" not in node["id"]:
        print(json.dumps({
            "id": node["id"],
            "description": node.get("description", "")
        }, indent=2))
        break
