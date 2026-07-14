"""
LLM helper — calls local Ollama (llama3.1) with a RAG context block.
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"


def ask_llm(question: str, context_docs: list[dict]) -> str:
    context_text = "\n\n---\n\n".join(
        f"[{d['metadata']['title']}]\n{d['content']}" for d in context_docs
    )
    prompt = (
        "You are a warranty support assistant. "
        "Use ONLY the context below to answer the question. "
        "If the answer is not in the context, say 'Not found in warranty documents.'\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        return f"[LLM error] {e}"
