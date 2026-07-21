"""
Google Open Knowledge Format (OKF) Python Showcase Application
"Hello World" demonstration showcasing OKF parsing, validation, Knowledge Graph traversal,
AI Context Assembly, and programmatic concept building.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add package path
sys.path.insert(0, str(Path(__file__).parent))

from okf import (
    OKFParser,
    OKFValidator,
    OKFKnowledgeGraph,
    OKFContextAssembler,
    OKFBuilder,
    OKFFrontMatter
)


def print_banner():
    print("=" * 70)
    print("      GOOGLE OPEN KNOWLEDGE FORMAT (OKF) - PYTHON SHOWCASE APP      ")
    print("=" * 70)
    print("Standardized Knowledge Representation for AI Agents & Humans (v0.1 Spec)\n")


def demo_1_inspect_bundle(bundle_path: Path):
    print("\n--- DEMO 1: PARSING & INSPECTING OKF BUNDLE ---")
    bundle = OKFParser.parse_bundle(bundle_path)
    print(f"Bundle Root: {bundle.root_path}")
    print(f"Total Knowledge Units Found: {len(bundle.concepts)}")
    print(f"Reserved Index File present: {'YES' if bundle.index_concept else 'NO'}")
    print(f"Reserved Log File present:   {'YES' if bundle.log_concept else 'NO'}\n")

    print("Parsed OKF Concepts by Type:")
    by_type = {}
    for path, concept in bundle.concepts.items():
        if concept.is_reserved:
            continue
        t = concept.frontmatter.type
        by_type.setdefault(t, []).append(concept)

    for ctype, concepts in sorted(by_type.items()):
        print(f"  📁 Type: [{ctype.upper()}] ({len(concepts)} unit(s))")
        for c in concepts:
            tags = f" | Tags: {', '.join(c.frontmatter.tags)}" if c.frontmatter.tags else ""
            res = f" | Resource: {c.frontmatter.resource}" if c.frontmatter.resource else ""
            print(f"     - {c.relative_path}{tags}{res}")


def demo_2_validate_bundle(bundle_path: Path):
    print("\n--- DEMO 2: OKF SPECIFICATION COMPLIANCE AUDITOR ---")
    bundle = OKFParser.parse_bundle(bundle_path)
    issues = OKFValidator.validate_bundle(bundle)

    if not issues:
        print("✅ OKF Bundle is 100% compliant with OKF v0.1 specification! No issues detected.")
    else:
        print(f"Audited Bundle. Found {len(issues)} validation report item(s):")
        for issue in issues:
            symbol = "❌ [ERROR]" if issue.severity == "ERROR" else "⚠️ [WARNING]"
            print(f"  {symbol} ({issue.concept_path}): {issue.message}")


demo_3_knowledge_graph = None  # placeholder

def demo_3_knowledge_graph(bundle_path: Path):
    print("\n--- DEMO 3: KNOWLEDGE GRAPH & RELATIONSHIP TRAVERSAL ---")
    bundle = OKFParser.parse_bundle(bundle_path)
    graph = OKFKnowledgeGraph(bundle)

    stats = graph.get_graph_stats()
    print(f"Graph Metrics: {stats['total_concepts']} concepts, {stats['total_relationships']} directional links.")
    print("Top Referenced Concept Hubs (In-degree):")
    for path, count in stats['top_referenced_concepts']:
        print(f"  - `{path}` linked by {count} other concept(s)")

    sample_concept = "services/auth_service.md"
    print(f"\nAnalyzing Knowledge Graph for: `{sample_concept}`")
    
    outgoing = graph.get_outgoing(sample_concept)
    print("  ➡️  Outgoing Links (Depends On):")
    for target in outgoing:
        print(f"      -> [{target.frontmatter.type.upper()}] {target.relative_path}")

    incoming = graph.get_incoming(sample_concept)
    print("  ⬅️  Incoming Backlinks (Referenced By):")
    for source in incoming:
        print(f"      <- [{source.frontmatter.type.upper()}] {source.relative_path}")

    path = graph.find_path("runbooks/auth_outage_recovery.md", "databases/users_db.md")
    if path:
        print(f"\n  🔍 Graph Traversal Path from Runbook to Database:")
        print("      " + " -> ".join(f"`{p}`" for p in path))


def demo_4_ai_context_assembler(bundle_path: Path):
    print("\n--- DEMO 4: AI AGENT CONTEXT ASSEMBLER ---")
    print("Simulating an AI Agent assembling optimal context for an incident query...\n")

    bundle = OKFParser.parse_bundle(bundle_path)
    assembler = OKFContextAssembler(bundle)

    query = "User login failing with 500 error in Auth Service"
    print(f"User Query: '{query}'")

    result = assembler.assemble_context_for_query(
        query=query,
        max_concepts=2,
        graph_expand_depth=1
    )

    print(f"\nSeed Concepts Matched: {result['seed_concepts']}")
    print(f"Total Concepts Assembled (Seeds + Graph Expansion): {result['total_assembled_concepts']}")
    print(f"Assembled Concept Paths: {result['concept_paths']}")

    print("\n--- GENERATED LLM CONTEXT PAYLOAD ---")
    print(result['formatted_context_payload'])


def demo_5_programmatic_builder(bundle_path: Path):
    print("\n--- DEMO 5: PROGRAMMATIC CONCEPT CREATION & CATALOG UPDATE ---")
    print("Creating a new OKF concept file dynamically...")

    new_fm = OKFFrontMatter(
        type="policy",
        title="Password Security Policy",
        description="Enforces complexity and Argon2 hashing requirements.",
        resource="https://compliance.internal/policies/sec-01",
        tags=["security", "compliance", "passwords"],
        author="secops@example.com",
        status="active"
    )

    body = """# Password Security Policy

This policy governs password requirements across all authentication endpoints.

## Related Components

- Implementation details in [User Authentication Service](../services/auth_service.md).
- Stored credentials structure in [Users Database Table](../databases/users_db.md).
"""

    rel_path = "policies/password_policy.md"
    concept = OKFBuilder.create_concept(
        bundle_root=bundle_path,
        relative_path=rel_path,
        frontmatter=new_fm,
        body_markdown=body,
        update_log=True
    )
    print(f"✅ Created new OKF Concept: `{rel_path}` (type: {concept.frontmatter.type})")
    print("✅ Appended change record to `log.md`")

    index = OKFBuilder.rebuild_index(bundle_path)
    print("✅ Rebuilt root catalog `index.md` with new concept included.")


def run_all_demos():
    print_banner()
    bundle_path = Path(__file__).parent / "sample_bundle"
    
    demo_1_inspect_bundle(bundle_path)
    demo_2_validate_bundle(bundle_path)
    demo_3_knowledge_graph(bundle_path)
    demo_4_ai_context_assembler(bundle_path)
    demo_5_programmatic_builder(bundle_path)
    
    print("\n" + "=" * 70)
    print("       ALL OKF CAPABILITY DEMONSTRATIONS COMPLETED SUCCESSFULLY!    ")
    print("=" * 70)


if __name__ == "__main__":
    run_all_demos()
