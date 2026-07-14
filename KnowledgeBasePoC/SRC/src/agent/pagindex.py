"""PageIndex tree reasoning engine — navigates the compiled wiki concept tree."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from src.models.facts import PageResult

logger = logging.getLogger(__name__)


def retrieve_pagindex(question: str, wiki_dir: Optional[str] = None) -> PageResult:
    """
    Navigate the wiki concept tree to find the best matching page.

    Strategy:
        1. List all concept pages
        2. Embed question + page titles/summaries
        3. Return the best-matching page's full content

    Args:
        question: Natural language question.
        wiki_dir: Path to wiki directory. Defaults to WIKI_DIR env var.

    Returns:
        PageResult with the best-matching page content.
    """
    wiki_path = Path(wiki_dir or os.getenv("WIKI_DIR", "./wiki"))
    concepts_dir = wiki_path / "concepts"

    if not concepts_dir.exists():
        return PageResult()

    pages = list(concepts_dir.glob("*.md"))
    if not pages:
        return PageResult()

    try:
        return _cosine_match(question, pages)
    except Exception as e:
        logger.warning(f"PageIndex retrieval failed: {e}")
        return PageResult()


def _cosine_match(question: str, pages: list[Path]) -> PageResult:
    """Find best matching page using cosine similarity."""
    import numpy as np

    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

    # Build corpus: page title + first 200 chars of content
    page_texts = []
    for page in pages:
        try:
            content = page.read_text(encoding="utf-8")
            # Extract title from frontmatter or filename
            title = page.stem
            if content.startswith("---"):
                import yaml
                end = content.find("\n---", 3)
                if end > 0:
                    try:
                        fm = yaml.safe_load(content[3:end]) or {}
                        title = fm.get("title", title)
                    except Exception:
                        pass
            page_texts.append(f"{title}. {content[:200]}")
        except Exception:
            page_texts.append(page.stem)

    # Embed question + all pages
    all_texts = [question] + page_texts
    embeddings = _embed_batch(all_texts, model_name)

    if not embeddings or len(embeddings) < 2:
        return PageResult()

    query_vec = np.array(embeddings[0])
    page_vecs = np.array(embeddings[1:])

    # Cosine similarity
    norms = np.linalg.norm(page_vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    page_vecs_norm = page_vecs / norms
    query_norm = query_vec / (np.linalg.norm(query_vec) or 1)
    scores = page_vecs_norm @ query_norm

    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    best_page = pages[best_idx]

    if best_score < 0.3:
        return PageResult()

    try:
        content = best_page.read_text(encoding="utf-8")
    except Exception:
        return PageResult()

    # Extract graph_node_ids from frontmatter
    graph_node_ids: list[str] = []
    source_refs: list[str] = []
    if content.startswith("---"):
        import yaml
        end = content.find("\n---", 3)
        if end > 0:
            try:
                fm = yaml.safe_load(content[3:end]) or {}
                graph_node_ids = fm.get("graph_node_ids", [])
                source_refs = fm.get("source_refs", [])
            except Exception:
                pass

    # Collect secondary pages (score > 0.5)
    child_pages = []
    for i, score in enumerate(scores):
        if i != best_idx and float(score) > 0.5:
            try:
                child_pages.append(pages[i].stem)
            except Exception:
                pass

    return PageResult(
        primary_page=content,
        child_pages=child_pages[:3],
        source_refs=source_refs,
        graph_node_ids=graph_node_ids,
        confidence=best_score,
    )


def _embed_batch(texts: list[str], model_name: str) -> list[list[float]]:
    """Embed a batch of texts."""
    try:
        if "text-embedding" in model_name:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(model=model_name, input=texts)
            return [item.embedding for item in response.data]
        else:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            return [v.tolist() for v in model.encode(texts)]
    except Exception as e:
        logger.warning(f"Batch embedding failed: {e}")
        return []
