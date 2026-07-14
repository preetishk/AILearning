"""Entity resolver — deduplicates and canonicalises entity names across extraction layers."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.models.facts import EntityRegistry, RegistryEntry, make_node_id

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Level 1 normalization: strip whitespace, lowercase."""
    return name.strip().lower()


def _embed_names(names: list[str]) -> list[list[float]]:
    """Embed a list of names using the configured embedding model."""
    try:
        model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        if "openai" in model_name or "text-embedding" in model_name:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(model=model_name, input=names)
            return [item.embedding for item in response.data]
        else:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            vecs = model.encode(names)
            return [v.tolist() for v in vecs]
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return [[0.0] * 384 for _ in names]


def _cluster_by_similarity(names: list[str], threshold: float = 0.92) -> list[list[str]]:
    """Cluster similar names using cosine similarity."""
    if len(names) < 2:
        return [[n] for n in names]
    try:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        embeddings = _embed_names(names)
        if not embeddings:
            return [[n] for n in names]
        matrix = cosine_similarity(embeddings)
        n = len(names)
        visited = [False] * n
        clusters: list[list[str]] = []

        for i in range(n):
            if visited[i]:
                continue
            cluster = [names[i]]
            visited[i] = True
            for j in range(i + 1, n):
                if not visited[j] and matrix[i][j] >= threshold:
                    cluster.append(names[j])
                    visited[j] = True
            clusters.append(cluster)
        return clusters
    except Exception:
        return [[n] for n in names]


def _llm_resolve(clusters: list[list[str]]) -> list[dict]:
    """Use LLM to confirm merges within clusters that have ≥2 names."""
    multi_clusters = [c for c in clusters if len(c) > 1]
    if not multi_clusters:
        return []
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o")
        prompt = (
            "You are an entity resolution processor. Output only valid JSON. No prose.\n\n"
            "Below are groups of symbol names that may refer to the same concept.\n"
            "For each group, decide if they are aliases for the same entity.\n\n"
            'Return a JSON object with key "results" containing array where each element is:\n'
            '{"canonical_name": "<most public name>", "aliases": ["<other names>"], '
            '"confidence": "high|medium|low"}\n\n'
            f"Name groups:\n{json.dumps(multi_clusters)}"
        )
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        results = parsed.get("results", parsed) if isinstance(parsed, dict) else parsed
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning(f"LLM resolution failed: {e}")
        return []


def resolve_entities(input_dir: str, output_dir: str, threshold: float = 0.92) -> EntityRegistry:
    """
    Build an EntityRegistry from all extracted JSON files.

    Steps:
        1. Collect all canonical_name values from structural.json
        2. Level 1 normalization
        3. Embedding similarity clustering
        4. LLM confirmation for ambiguous clusters
        5. Write entity_registry.json and return EntityRegistry
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    registry = EntityRegistry()

    # Load structural.json for canonical names
    structural_file = input_path / "structural.json"
    if not structural_file.exists():
        logger.warning("structural.json not found — returning empty registry")
        return registry

    try:
        data = json.loads(structural_file.read_text(encoding="utf-8"))
    except Exception:
        return registry

    entities = data if isinstance(data, list) else data.get("entities", [])

    # Build initial registry from structural facts
    all_names = []
    name_to_fact: dict[str, dict] = {}
    for entity in entities:
        cname = entity.get("canonical_name", "")
        if cname:
            all_names.append(cname)
            name_to_fact[cname] = entity
            for alias in entity.get("aliases", []):
                if alias and alias != cname:
                    all_names.append(alias)

    all_names = list(set(all_names))
    if not all_names:
        return registry

    logger.info(f"Resolving {len(all_names)} entity names …")

    # Cluster by similarity
    clusters = _cluster_by_similarity(all_names, threshold)

    # Try LLM confirmation on multi-name clusters
    resolved = _llm_resolve(clusters)
    resolved_map: dict[str, str] = {}  # alias → canonical
    for item in resolved:
        canon = item.get("canonical_name", "")
        for alias in item.get("aliases", []):
            if alias != canon:
                resolved_map[_normalize(alias)] = canon

    # Build registry
    for cluster in clusters:
        if not cluster:
            continue
        # Prefer the longest / most qualified name as canonical
        canonical = max(cluster, key=lambda n: len(n))
        # Check if LLM overrode the canonical
        for name in cluster:
            if _normalize(name) in resolved_map:
                canonical = resolved_map[_normalize(name)]
                break

        fact = name_to_fact.get(canonical, name_to_fact.get(cluster[0], {}))
        source_ref = fact.get("source_ref", "")
        aliases = [n for n in cluster if n != canonical]
        registry.add_or_merge(canonical, aliases=aliases, source_ref=source_ref)

    # Persist registry
    registry_file = output_path / "entity_registry.json"
    registry_file.write_text(registry.model_dump_json(indent=2), encoding="utf-8")
    logger.info(f"Registry saved: {len(registry.entries)} entries → {registry_file}")

    return registry
