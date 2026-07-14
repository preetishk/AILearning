"""Hydrator — converts extracted facts into graph-import-ready node/edge triples."""
from __future__ import annotations

import logging
from typing import Optional

from src.models.facts import (
    EntityFact, RuleFact, ContractFact, GraphNode, GraphEdge, GraphTriple,
    EntityRegistry, make_node_id,
)
from src.storage.protocols import GraphStore

logger = logging.getLogger(__name__)


def _entity_to_node(entity: EntityFact) -> GraphNode:
    return GraphNode(
        id=entity.id,
        label="Entity",
        properties={
            "canonical_name": entity.canonical_name,
            "aliases": entity.aliases,
            "kind": entity.kind,
            "source_type": entity.source_type,
            "source_ref": entity.source_ref,
            "source_line_start": entity.source_line_start,
            "source_line_end": entity.source_line_end,
            "layer": entity.layer,
            "tags": entity.tags,
            "confidence": entity.confidence,
            "summary": entity.summary,
        },
    )


def _rule_to_node(rule: RuleFact) -> GraphNode:
    return GraphNode(
        id=rule.id,
        label="Rule",
        properties={
            "condition": rule.condition,
            "true_path": rule.true_path,
            "false_path": rule.false_path,
            "linked_outcome": rule.linked_outcome,
            "source_ref": rule.source_ref,
            "confidence": rule.confidence,
        },
    )


def _outcome_to_node(code_id: str, value_name: str, meaning: str,
                     recoverable: bool, severity: str) -> GraphNode:
    return GraphNode(
        id=code_id,
        label="Outcome",
        properties={
            "canonical_name": value_name,
            "meaning": meaning,
            "recoverable": recoverable,
            "severity": severity,
        },
    )


def hydrate(
    facts: dict[int, list],
    registry: EntityRegistry,
) -> GraphTriple:
    """
    Convert all extracted facts into GraphTriple (nodes + edges + skipped).

    Args:
        facts: dict from extract_all_layers() — {layer: [fact_objects]}
        registry: EntityRegistry for canonical name resolution
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    skipped: list[dict] = []
    seen_node_ids: set[str] = set()

    def add_node(node: GraphNode):
        if node.id not in seen_node_ids:
            nodes.append(node)
            seen_node_ids.add(node.id)

    # ── Layer 1: Entity nodes + structural edges ─────────────────────────────
    for entity in facts.get(1, []):
        node = _entity_to_node(entity)
        add_node(node)

        # Register in registry if not present
        registry.add_or_merge(
            entity.canonical_name,
            aliases=entity.aliases,
            source_ref=entity.source_ref,
            confidence=entity.confidence,
        )

        # Structural edges
        for rel in entity.relations:
            target_id = registry.lookup(rel.target)
            if target_id:
                edges.append(GraphEdge(**{
                    "from": entity.id,
                    "to": target_id,
                    "relation_type": rel.type.upper(),
                    "properties": {"source_ref": entity.source_ref},
                }))
            else:
                skipped.append({
                    "from": entity.id,
                    "to_unresolved": rel.target,
                    "relation_type": rel.type,
                    "reason": "target not in registry",
                })

    # IS_ALIAS_OF edges
    for entry in registry.entries:
        for alias in entry.aliases:
            alias_id = make_node_id(alias)
            edges.append(GraphEdge(**{
                "from": alias_id,
                "to": entry.node_id,
                "relation_type": "IS_ALIAS_OF",
                "properties": {},
            }))

    # ── Layer 2: Rule nodes + CONTAINS / LEADS_TO edges ──────────────────────
    for rule in facts.get(2, []):
        rule_node = _rule_to_node(rule)
        add_node(rule_node)

        # CONTAINS edge: owner_entity → rule
        owner_id = registry.lookup(rule.owner_entity)
        if owner_id:
            edges.append(GraphEdge(**{
                "from": owner_id,
                "to": rule.id,
                "relation_type": "CONTAINS",
                "properties": {},
            }))
        else:
            skipped.append({"from": rule.owner_entity, "to": rule.id,
                            "reason": "owner not in registry"})

        # LEADS_TO edge: rule → outcome
        if rule.linked_outcome:
            outcome_id = make_node_id(rule.linked_outcome)
            outcome_node = GraphNode(
                id=outcome_id,
                label="Outcome",
                properties={"canonical_name": rule.linked_outcome},
            )
            add_node(outcome_node)
            edges.append(GraphEdge(**{
                "from": rule.id,
                "to": outcome_id,
                "relation_type": "LEADS_TO",
                "properties": {},
            }))

        # RESOLVED_BY edge
        if rule.linked_resolution:
            resolution_id = registry.lookup(rule.linked_resolution)
            if rule.linked_outcome and resolution_id:
                outcome_id = make_node_id(rule.linked_outcome)
                edges.append(GraphEdge(**{
                    "from": outcome_id,
                    "to": resolution_id,
                    "relation_type": "RESOLVED_BY",
                    "properties": {},
                }))

    # ── Layer 3: Outcome + Event nodes, contract edges ────────────────────────
    for contract in facts.get(3, []):
        entity_id = registry.lookup(contract.entity_name)
        for oc in contract.outcome_codes:
            oc_id = make_node_id(oc.value_name)
            oc_node = _outcome_to_node(oc_id, oc.value_name, oc.meaning,
                                        oc.recoverable, oc.severity)
            add_node(oc_node)
            if entity_id:
                edges.append(GraphEdge(**{
                    "from": entity_id,
                    "to": oc_id,
                    "relation_type": "PRODUCES",
                    "properties": {},
                }))

    return GraphTriple(nodes=nodes, edges=edges, skipped_edges=skipped)


def write_to_graph(triple: GraphTriple, graph_store: GraphStore) -> dict[str, int]:
    """Write all nodes and edges from a GraphTriple to the graph store."""
    nodes_written = 0
    edges_written = 0
    edges_skipped = len(triple.skipped_edges)

    for node in triple.nodes:
        try:
            graph_store.upsert_node(node.label, node.id, node.properties)
            nodes_written += 1
        except Exception as e:
            logger.warning(f"Failed to write node {node.id}: {e}")

    for edge in triple.edges:
        try:
            from_id = edge.from_id
            to_id = edge.to_id
            graph_store.upsert_edge(from_id, to_id, edge.relation_type, edge.properties)
            edges_written += 1
        except Exception as e:
            logger.debug(f"Failed to write edge {edge.from_id}→{edge.to_id}: {e}")

    logger.info(f"Graph: {nodes_written} nodes, {edges_written} edges, {edges_skipped} skipped")
    return {"nodes_written": nodes_written, "edges_written": edges_written,
            "edges_skipped": edges_skipped}
