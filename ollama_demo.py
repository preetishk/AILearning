"""
OKF + Ollama (Llama3.1) Demo
Use Case: AI Incident Investigation Assistant

Demonstrates the full OKF pipeline end-to-end:
  1. Parse the OKF knowledge bundle (sample_bundle/)
  2. Assemble graph-aware context for a user query
  3. Send the structured context to local Ollama Llama3.1
  4. Receive a grounded, knowledge-backed answer

Run:
    python ollama_demo.py
    python ollama_demo.py "Payment service is returning 503 errors"

Requirements (in addition to existing):
    pip install requests
"""

import sys
import json
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from okf import OKFParser, OKFContextAssembler

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "llama3.1"
BUNDLE_PATH = Path(__file__).parent / "sample_bundle"

SYSTEM_PROMPT = """\
You are an expert Site Reliability Engineer (SRE) and incident responder.
You are given structured knowledge from an OKF (Open Knowledge Format) bundle \
that describes the system architecture, services, databases, metrics, runbooks, and policies.
Use ONLY the provided knowledge to answer the user's question.
Be concise, actionable, and cite the specific OKF concepts you relied on (by their Title or Path).
If the answer cannot be found in the provided knowledge, say so clearly.\
"""

# ── Ollama call ───────────────────────────────────────────────────────────────

def call_ollama(prompt: str, stream: bool = True) -> str:
    """Send a prompt to local Ollama and return the full response text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": stream,
        "options": {"temperature": 0.2}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=stream, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot reach Ollama at http://localhost:11434")
        print("        Make sure Ollama is running:  ollama serve")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] Ollama returned an error: {e}")
        sys.exit(1)

    full_text = []
    if stream:
        print("\n[Llama3.1 Response]\n" + "-" * 50)
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                print(token, end="", flush=True)
                full_text.append(token)
                if chunk.get("done"):
                    break
        print("\n" + "-" * 50)
    else:
        full_text.append(response.json().get("response", ""))

    return "".join(full_text)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(query: str):
    print("=" * 60)
    print("  OKF + OLLAMA  —  AI Incident Investigation Assistant")
    print("=" * 60)

    # Step 1: Parse bundle
    print(f"\n[1] Parsing OKF bundle: {BUNDLE_PATH.name}/")
    bundle = OKFParser.parse_bundle(BUNDLE_PATH)
    print(f"    Loaded {len(bundle.concepts)} knowledge concepts.")

    # Step 2: Assemble graph-aware context
    print(f"\n[2] Assembling context for query:\n    \"{query}\"")
    assembler = OKFContextAssembler(bundle)
    result = assembler.assemble_context_for_query(
        query=query,
        max_concepts=3,       # top-3 matching seed concepts
        graph_expand_depth=1  # also pull in their direct linked neighbours
    )

    print(f"    Seed concepts matched : {result['seed_concepts']}")
    print(f"    Total assembled       : {result['total_assembled_concepts']} concepts")
    print(f"    Context paths         : {result['concept_paths']}")

    # Step 3: Build the final prompt
    okf_context = result["formatted_context_payload"]
    final_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{okf_context}\n\n"
        f"User Question: {query}\n\n"
        f"Answer:"
    )

    # Step 4: Call Ollama
    print(f"\n[3] Sending to Ollama ({MODEL}) ...")
    call_ollama(final_prompt, stream=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Accept query from CLI arg or use default incident scenario
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = "User login is failing with 500 errors. How do I investigate and recover the Auth Service?"

    run(user_query)
