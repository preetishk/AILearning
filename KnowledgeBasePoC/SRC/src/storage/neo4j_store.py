"""Neo4j graph store implementation."""
from __future__ import annotations

import os
from typing import Optional

from neo4j import GraphDatabase, Driver
from tenacity import retry, stop_after_attempt, wait_exponential


class Neo4jStore:
    """Implements GraphStore protocol using Neo4j Bolt driver."""

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self._driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

    # ── Node operations ──────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    def upsert_node(self, label: str, node_id: str, properties: dict) -> None:
        """MERGE a node by id, setting all properties."""
        props = {k: v for k, v in properties.items() if v is not None}
        cypher = (
            f"MERGE (n:{label} {{id: $id}}) "
            "SET n += $props"
        )
        with self._driver.session() as session:
            session.run(cypher, id=node_id, props=props)

    # ── Edge operations ──────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    def upsert_edge(self, from_id: str, to_id: str,
                    relation_type: str, properties: dict = None) -> None:
        """MERGE a typed directed edge between two nodes."""
        props = properties or {}
        cypher = (
            "MATCH (a {id: $from_id}), (b {id: $to_id}) "
            f"MERGE (a)-[r:{relation_type}]->(b) "
            "SET r += $props"
        )
        with self._driver.session() as session:
            session.run(cypher, from_id=from_id, to_id=to_id, props=props)

    # ── Query ────────────────────────────────────────────────────────────────

    def query(self, cypher: str, params: dict = None) -> list[dict]:
        """Run a raw Cypher query. Returns list of record dicts."""
        params = params or {}
        with self._driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    # ── Stats ────────────────────────────────────────────────────────────────

    def node_count(self) -> int:
        result = self.query("MATCH (n) RETURN count(n) AS cnt")
        return result[0]["cnt"] if result else 0

    def edge_count(self) -> int:
        result = self.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
        return result[0]["cnt"] if result else 0

    # ── Schema setup ─────────────────────────────────────────────────────────

    def create_schema(self) -> None:
        """Create uniqueness constraints and indexes. Safe to call multiple times."""
        with self._driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_id IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT outcome_id IF NOT EXISTS "
                "FOR (o:Outcome) REQUIRE o.id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT event_id IF NOT EXISTS "
                "FOR (e:Event) REQUIRE e.id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT rule_id IF NOT EXISTS "
                "FOR (r:Rule) REQUIRE r.id IS UNIQUE"
            )
            session.run(
                "CREATE INDEX entity_name IF NOT EXISTS "
                "FOR (e:Entity) ON (e.canonical_name)"
            )
            try:
                session.run(
                    "CREATE FULLTEXT INDEX entity_aliases IF NOT EXISTS "
                    "FOR (e:Entity) ON EACH [e.canonical_name, e.aliases]"
                )
            except Exception:
                pass  # fulltext index may not be supported in all editions

    # ── Stale marking ────────────────────────────────────────────────────────

    def mark_stale(self, source_ref: str) -> None:
        """Mark all nodes with the given source_ref as stale."""
        self.query(
            "MATCH (n {source_ref: $source_ref}) SET n.stale = true",
            {"source_ref": source_ref},
        )

    def delete_by_source(self, source_ref: str) -> None:
        """Delete all nodes from a specific source."""
        self.query(
            "MATCH (n {source_ref: $source_ref}) DETACH DELETE n",
            {"source_ref": source_ref},
        )

    # ── Path analysis ────────────────────────────────────────────────────────

    def find_shortest_path(self, from_name: str, to_name: str) -> list[dict]:
        cypher = (
            "MATCH (a {canonical_name: $from_name}), (b {canonical_name: $to_name}), "
            "p = shortestPath((a)-[*1..6]->(b)) "
            "RETURN [node in nodes(p) | node.canonical_name] AS node_names, "
            "[rel in relationships(p) | type(rel)] AS rel_types, "
            "length(p) AS path_length "
            "LIMIT 1"
        )
        return self.query(cypher, {"from_name": from_name, "to_name": to_name})

    def find_all_paths(self, from_name: str, to_name: str, max_depth: int = 4) -> list[dict]:
        cypher = (
            f"MATCH (a {{canonical_name: $from_name}}), (b {{canonical_name: $to_name}}), "
            f"p = (a)-[*1..{max_depth}]->(b) "
            "RETURN [node in nodes(p) | node.canonical_name] AS node_names, "
            "[rel in relationships(p) | type(rel)] AS rel_types, "
            "length(p) AS path_length "
            "ORDER BY path_length LIMIT 20"
        )
        return self.query(cypher, {"from_name": from_name, "to_name": to_name})

    def find_impact(self, from_name: str, max_depth: int = 3) -> list[dict]:
        cypher = (
            "MATCH (start {canonical_name: $from_name})-"
            f"[:CALLS|EMITS|LEADS_TO*1..{max_depth}]->(affected) "
            "RETURN DISTINCT affected.canonical_name AS name, "
            "affected.kind AS kind, affected.source_ref AS source_ref "
            "ORDER BY name"
        )
        return self.query(cypher, {"from_name": from_name})

    def find_reverse_deps(self, from_name: str, max_depth: int = 3) -> list[dict]:
        cypher = (
            f"MATCH (caller)-[:CALLS|DEPENDS_ON*1..{max_depth}]->"
            "(target {canonical_name: $from_name}) "
            "RETURN DISTINCT caller.canonical_name AS name, "
            "caller.kind AS kind, caller.source_ref AS source_ref "
            "ORDER BY name"
        )
        return self.query(cypher, {"from_name": from_name})

    def get_entity_neighbors(self, canonical_name: str, depth: int = 2) -> list[dict]:
        cypher = (
            f"MATCH (n {{canonical_name: $name}})-[r*1..{depth}]-(neighbor) "
            "RETURN DISTINCT neighbor.canonical_name AS name, "
            "neighbor.kind AS kind, neighbor.source_ref AS source_ref, "
            "neighbor.id AS id"
        )
        return self.query(cypher, {"name": canonical_name})

    def get_entity_relationships(self, node_id: str) -> list[dict]:
        cypher = (
            "MATCH (n {id: $id})-[r]-(m) "
            "RETURN type(r) AS rel_type, m.canonical_name AS target, "
            "m.kind AS target_kind, "
            "CASE WHEN startNode(r).id = $id THEN 'outbound' ELSE 'inbound' END AS direction"
        )
        return self.query(cypher, {"id": node_id})

    def list_entities(self, skip: int = 0, limit: int = 50,
                      kind_filter: str = None, source_type_filter: str = None) -> list[dict]:
        where_clauses = ["n.stale IS NULL OR n.stale = false"]
        if kind_filter:
            where_clauses.append("n.kind = $kind")
        if source_type_filter:
            where_clauses.append("n.source_type = $source_type")
        where = " AND ".join(where_clauses)
        cypher = (
            f"MATCH (n:Entity) WHERE {where} "
            "RETURN n.id AS id, n.canonical_name AS canonical_name, "
            "n.kind AS kind, n.source_ref AS source_ref, "
            "n.confidence AS confidence, n.summary AS summary, "
            "n.aliases AS aliases, n.source_type AS source_type "
            "ORDER BY n.canonical_name SKIP $skip LIMIT $limit"
        )
        params = {"skip": skip, "limit": limit}
        if kind_filter:
            params["kind"] = kind_filter
        if source_type_filter:
            params["source_type"] = source_type_filter
        return self.query(cypher, params)

    def get_entity_by_id(self, node_id: str) -> Optional[dict]:
        result = self.query(
            "MATCH (n {id: $id}) RETURN n", {"id": node_id}
        )
        if result:
            node = result[0].get("n", {})
            return dict(node) if node else None
        return None

    def close(self) -> None:
        self._driver.close()
