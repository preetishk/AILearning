"""
Unit tests for Google Open Knowledge Format (OKF) Python implementation.
"""

import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add package directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from okf.models import OKFFrontMatter
from okf.parser import OKFParser
from okf.validator import OKFValidator
from okf.graph import OKFKnowledgeGraph
from okf.assembler import OKFContextAssembler
from okf.builder import OKFBuilder


@pytest.fixture
def sample_bundle_path():
    """Returns path to the sample OKF bundle."""
    base_dir = Path(__file__).parent.parent
    return base_dir / "sample_bundle"


def test_parse_sample_bundle(sample_bundle_path):
    bundle = OKFParser.parse_bundle(sample_bundle_path)
    assert len(bundle.concepts) >= 7
    assert bundle.index_concept is not None
    assert bundle.log_concept is not None

    auth_service = bundle.get_concept("services/auth_service.md")
    assert auth_service is not None
    assert auth_service.frontmatter.type == "service"
    assert auth_service.frontmatter.title == "User Authentication Service"
    assert "auth" in auth_service.frontmatter.tags
    assert len(auth_service.links) >= 3


def test_validate_sample_bundle(sample_bundle_path):
    bundle = OKFParser.parse_bundle(sample_bundle_path)
    issues = OKFValidator.validate_bundle(bundle)
    
    # Filter for severe errors
    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 0, f"Expected 0 errors in sample bundle, found: {errors}"


def test_knowledge_graph_traversal(sample_bundle_path):
    bundle = OKFParser.parse_bundle(sample_bundle_path)
    graph = OKFKnowledgeGraph(bundle)

    # Auth service outgoing links
    outgoing = graph.get_outgoing("services/auth_service.md")
    outgoing_paths = [c.relative_path for c in outgoing]
    assert "databases/users_db.md" in outgoing_paths
    assert "metrics/auth_failure_rate.md" in outgoing_paths

    # Backlinks (who references auth_service?)
    incoming = graph.get_incoming("services/auth_service.md")
    incoming_paths = [c.relative_path for c in incoming]
    assert "runbooks/auth_outage_recovery.md" in incoming_paths or "services/payment_service.md" in incoming_paths


def test_context_assembler(sample_bundle_path):
    bundle = OKFParser.parse_bundle(sample_bundle_path)
    assembler = OKFContextAssembler(bundle)

    result = assembler.assemble_context_for_query(
        query="Incident in Auth service: high failure rate and database errors",
        max_concepts=2,
        graph_expand_depth=1
    )

    assert result["total_assembled_concepts"] > 0
    assert "BEGIN OKF CONTEXT PAYLOAD" in result["formatted_context_payload"]


def test_concept_builder_temp():
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_root = Path(tmpdir)
        
        fm = OKFFrontMatter(
            type="policy",
            title="Data Retention Policy",
            description="Defines data purge rules.",
            tags=["compliance", "privacy"]
        )
        
        concept = OKFBuilder.create_concept(
            bundle_root=bundle_root,
            relative_path="policies/data_retention.md",
            frontmatter=fm,
            body_markdown="# Data Retention Policy\n\nPurge user logs after 90 days."
        )

        assert (bundle_root / "policies/data_retention.md").exists()
        assert concept.frontmatter.type == "policy"
        assert (bundle_root / "log.md").exists()

        # Rebuild catalog index
        index_concept = OKFBuilder.rebuild_index(bundle_root)
        assert index_concept is not None
        assert "Data Retention Policy" in index_concept.content
