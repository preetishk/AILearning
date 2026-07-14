"""One-time Neo4j schema setup — creates constraints and indexes."""
from __future__ import annotations

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase


def create_schema():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        constraints = [
            ("entity_id", "Entity", "id"),
            ("outcome_id", "Outcome", "id"),
            ("event_id", "Event", "id"),
            ("rule_id", "Rule", "id"),
        ]
        for constraint_name, label, prop in constraints:
            try:
                session.run(
                    f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
                )
                print(f"  ✓ Constraint {constraint_name} on {label}.{prop}")
            except Exception as e:
                print(f"  ! Constraint {constraint_name}: {e}")

        indexes = [
            ("entity_name_idx", "Entity", "canonical_name"),
            ("entity_source_idx", "Entity", "source_ref"),
            ("entity_kind_idx", "Entity", "kind"),
        ]
        for idx_name, label, prop in indexes:
            try:
                session.run(
                    f"CREATE INDEX {idx_name} IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.{prop})"
                )
                print(f"  ✓ Index {idx_name} on {label}.{prop}")
            except Exception as e:
                print(f"  ! Index {idx_name}: {e}")

        print("\nSchema setup complete.")

    driver.close()


if __name__ == "__main__":
    create_schema()
