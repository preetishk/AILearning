"""Graph retriever — executes Cypher queries based on IntentResult."""
from __future__ import annotations

import logging

from src.models.facts import IntentResult
from src.storage.protocols import GraphStore

logger = logging.getLogger(__name__)


def retrieve_graph(intent: IntentResult, graph_store: GraphStore,
                   top_k: int = 10) -> list[dict]:
    """
    Execute graph queries based on the classified intent.

    Returns a list of dicts with keys:
        id, canonical_name, kind, source_ref, rel_type, direction, score
    """
    results: list[dict] = []
    entities = intent.primary_entities or []

    if not entities:
        return results

    for entity_name in entities[:3]:  # limit to top 3 entities
        try:
            if intent.question_type == "structural":
                results.extend(_structural_query(entity_name, graph_store))
            elif intent.question_type == "behavioral":
                results.extend(_behavioral_query(entity_name, graph_store))
            elif intent.question_type == "multi-hop":
                results.extend(_multihop_query(entity_name, graph_store))
            else:
                # semantic — still do a graph lookup as enrichment
                results.extend(_structural_query(entity_name, graph_store))
        except Exception as e:
            logger.warning(f"Graph query failed for '{entity_name}': {e}")

    # Deduplicate by id
    seen = set()
    unique = []
    for r in results:
        key = r.get("id") or r.get("canonical_name", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:top_k]


def _structural_query(entity_name: str, graph_store: GraphStore) -> list[dict]:
    """Find direct callers, callees, and related nodes."""
    results = []

    # What does entity call?
    callees = graph_store.query(
        "MATCH (n {canonical_name: $name})-[r]->(m) "
        "RETURN m.id AS id, m.canonical_name AS canonical_name, "
        "m.kind AS kind, m.source_ref AS source_ref, "
        "type(r) AS rel_type, 'outbound' AS direction",
        {"name": entity_name},
    )
    for row in callees:
        row["_score"] = 0.9
        row["graph_path"] = f"{entity_name} → [{row.get('rel_type')}] → {row.get('canonical_name')}"
        results.append(row)

    # What calls entity?
    callers = graph_store.query(
        "MATCH (m)-[r]->(n {canonical_name: $name}) "
        "RETURN m.id AS id, m.canonical_name AS canonical_name, "
        "m.kind AS kind, m.source_ref AS source_ref, "
        "type(r) AS rel_type, 'inbound' AS direction",
        {"name": entity_name},
    )
    for row in callers:
        row["_score"] = 0.85
        row["graph_path"] = f"{row.get('canonical_name')} → [{row.get('rel_type')}] → {entity_name}"
        results.append(row)

    return results


def _behavioral_query(entity_name: str, graph_store: GraphStore) -> list[dict]:
    """Find outcomes and resolution paths."""
    results = []

    # Find outcomes produced by this entity
    outcomes = graph_store.query(
        "MATCH (n {canonical_name: $name})-[:PRODUCES|LEADS_TO]->(o) "
        "OPTIONAL MATCH (o)-[:RESOLVED_BY]->(fix) "
        "RETURN o.id AS id, o.canonical_name AS canonical_name, "
        "o.meaning AS meaning, fix.canonical_name AS fix_name, "
        "'Outcome' AS kind, o.source_ref AS source_ref",
        {"name": entity_name},
    )
    for row in outcomes:
        row["_score"] = 0.9
        fix = row.get("fix_name")
        row["graph_path"] = (
            f"{entity_name} → [PRODUCES] → {row.get('canonical_name')}"
            + (f" → [RESOLVED_BY] → {fix}" if fix else "")
        )
        results.append(row)

    return results


def _multihop_query(entity_name: str, graph_store: GraphStore) -> list[dict]:
    """BFS impact traversal."""
    results = []
    try:
        impacted = graph_store.query(
            "MATCH p = (start {canonical_name: $name})-"
            "[:CALLS|EMITS|LEADS_TO*1..3]->(affected) "
            "RETURN affected.id AS id, affected.canonical_name AS canonical_name, "
            "affected.kind AS kind, affected.source_ref AS source_ref, "
            "length(p) AS hop_count",
            {"name": entity_name},
        )
        for row in impacted:
            row["_score"] = max(0.5, 1.0 - row.get("hop_count", 1) * 0.15)
            row["graph_path"] = f"Impact from {entity_name} ({row.get('hop_count')} hops)"
            results.append(row)
    except Exception as e:
        logger.debug(f"Multi-hop query error: {e}")
    return results
