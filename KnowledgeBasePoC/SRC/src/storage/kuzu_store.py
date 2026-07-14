"""Kùzu embedded graph store implementation (alternative to Neo4j, no Docker needed)."""
from __future__ import annotations

import os
from typing import Optional


class KuzuStore:
    """Implements GraphStore protocol using Kùzu embedded graph DB."""

    def __init__(self):
        try:
            import kuzu
            output_dir = os.getenv("OUTPUT_DIR", "./output")
            db_path = os.path.join(output_dir, "kuzu_db")
            os.makedirs(db_path, exist_ok=True)
            self._db = kuzu.Database(db_path)
            self._conn = kuzu.Connection(self._db)
            self._ensure_schema()
        except ImportError:
            raise ImportError("kuzu package is required. Install with: pip install kuzu")

    def _ensure_schema(self) -> None:
        tables = [
            "CREATE NODE TABLE IF NOT EXISTS Entity(id STRING, canonical_name STRING, "
            "kind STRING, source_type STRING, source_ref STRING, confidence STRING, "
            "aliases STRING, summary STRING, stale BOOLEAN, PRIMARY KEY(id))",
            "CREATE NODE TABLE IF NOT EXISTS Outcome(id STRING, canonical_name STRING, "
            "category STRING, meaning STRING, recoverable BOOLEAN, severity STRING, "
            "PRIMARY KEY(id))",
            "CREATE NODE TABLE IF NOT EXISTS Event(id STRING, canonical_name STRING, "
            "event_type STRING, PRIMARY KEY(id))",
            "CREATE NODE TABLE IF NOT EXISTS Rule(id STRING, condition STRING, "
            "true_path STRING, false_path STRING, PRIMARY KEY(id))",
            "CREATE REL TABLE IF NOT EXISTS CALLS(FROM Entity TO Entity)",
            "CREATE REL TABLE IF NOT EXISTS IMPLEMENTS(FROM Entity TO Entity)",
            "CREATE REL TABLE IF NOT EXISTS INHERITS(FROM Entity TO Entity)",
            "CREATE REL TABLE IF NOT EXISTS DEPENDS_ON(FROM Entity TO Entity)",
            "CREATE REL TABLE IF NOT EXISTS EMITS(FROM Entity TO Event)",
            "CREATE REL TABLE IF NOT EXISTS PRODUCES(FROM Entity TO Outcome)",
            "CREATE REL TABLE IF NOT EXISTS RESOLVED_BY(FROM Outcome TO Outcome)",
            "CREATE REL TABLE IF NOT EXISTS LEADS_TO(FROM Rule TO Outcome)",
            "CREATE REL TABLE IF NOT EXISTS CONTAINS(FROM Entity TO Rule)",
        ]
        for ddl in tables:
            try:
                self._conn.execute(ddl)
            except Exception:
                pass

    def upsert_node(self, label: str, node_id: str, properties: dict) -> None:
        props = {k: v for k, v in properties.items() if v is not None}
        # Simple merge using delete + insert pattern for Kùzu
        try:
            self._conn.execute(f"MATCH (n:{label} {{id: $id}}) DELETE n", {"id": node_id})
        except Exception:
            pass
        cols = ", ".join(props.keys())
        vals = ", ".join(f"${k}" for k in props.keys())
        try:
            self._conn.execute(f"CREATE (n:{label} {{{cols}}}) VALUES ({vals})", props)
        except Exception:
            pass

    def upsert_edge(self, from_id: str, to_id: str,
                    relation_type: str, properties: dict = None) -> None:
        try:
            self._conn.execute(
                f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
                f"CREATE (a)-[:{relation_type}]->(b)",
                {"from_id": from_id, "to_id": to_id},
            )
        except Exception:
            pass

    def query(self, cypher: str, params: dict = None) -> list[dict]:
        params = params or {}
        try:
            result = self._conn.execute(cypher, params)
            rows = []
            while result.hasNext():
                rows.append(result.getNext())
            return rows
        except Exception:
            return []

    def node_count(self) -> int:
        result = self.query("MATCH (n) RETURN count(n) AS cnt")
        return result[0].get("cnt", 0) if result else 0

    def edge_count(self) -> int:
        result = self.query("MATCH ()-[r]->() RETURN count(r) AS cnt")
        return result[0].get("cnt", 0) if result else 0

    def close(self) -> None:
        pass  # Kùzu closes automatically
