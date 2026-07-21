"""
Open Knowledge Format (OKF) AI Context Assembler
Assembles optimal, contextually complete LLM prompts from OKF knowledge bundles.
Solves the AI "context-assembly" problem by leveraging concept metadata and graph links.
"""

from typing import List, Set, Dict, Any, Tuple, Optional
from .models import OKFBundle, OKFConcept
from .graph import OKFKnowledgeGraph


class OKFContextAssembler:
    """Engine for building targeted, high-precision context for AI Agents from an OKF Bundle."""

    def __init__(self, bundle: OKFBundle):
        self.bundle = bundle
        self.graph = OKFKnowledgeGraph(bundle)

    def assemble_context_for_query(
        self,
        query: str,
        max_concepts: int = 5,
        graph_expand_depth: int = 1,
        filter_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Finds relevant seed concepts for query, expands them via Knowledge Graph links,
        and formats an optimized AI prompt payload.
        """
        query_terms = [q.lower() for q in query.split() if len(q) > 2]
        seed_concepts: List[Tuple[float, OKFConcept]] = []

        # Step 1: Score concepts based on YAML metadata and content keyword match
        for path, concept in self.bundle.concepts.items():
            if concept.is_reserved:
                continue

            if filter_type and concept.frontmatter.type.lower() != filter_type.lower():
                continue

            score = 0.0
            fm = concept.frontmatter
            
            # Title match (high weight)
            if fm.title and any(term in fm.title.lower() for term in query_terms):
                score += 5.0
                
            # Tags match (high weight)
            if any(term in tag.lower() for tag in fm.tags for term in query_terms):
                score += 4.0

            # Type match
            if any(term in fm.type.lower() for term in query_terms):
                score += 3.0

            # Description match
            if fm.description and any(term in fm.description.lower() for term in query_terms):
                score += 2.0

            # Body content match
            content_lower = concept.content.lower()
            for term in query_terms:
                if term in content_lower:
                    score += 1.0

            if score > 0:
                seed_concepts.append((score, concept))

        # Sort seed concepts by score descending
        seed_concepts.sort(key=lambda x: x[0], reverse=True)
        top_seeds = [c for _, c in seed_concepts[:max_concepts]]

        # Step 2: Perform Knowledge Graph Expansion (pull in linked dependency context)
        assembled_paths: Set[str] = set()
        for seed in top_seeds:
            neighborhood = self.graph.get_neighborhood(seed.relative_path, max_depth=graph_expand_depth)
            assembled_paths.update(neighborhood)

        # Retrieve concept objects for all assembled paths
        assembled_concepts = [
            self.bundle.concepts[p] for p in assembled_paths 
            if p in self.bundle.concepts and not self.bundle.concepts[p].is_reserved
        ]

        # Step 3: Render LLM Context Payload
        formatted_prompt = self._render_llm_payload(query, assembled_concepts)

        return {
            "query": query,
            "seed_concepts": [c.relative_path for c in top_seeds],
            "total_assembled_concepts": len(assembled_concepts),
            "concept_paths": [c.relative_path for c in assembled_concepts],
            "formatted_context_payload": formatted_prompt
        }

    def _render_llm_payload(self, query: str, concepts: List[OKFConcept]) -> str:
        """Formats concepts into a clean, structured context block for LLM prompts."""
        lines = []
        lines.append("=== BEGIN OKF CONTEXT PAYLOAD ===")
        lines.append(f"Query/Goal: {query}")
        lines.append(f"Included Knowledge Units: {len(concepts)}\n")

        for idx, concept in enumerate(concepts, 1):
            fm = concept.frontmatter
            lines.append(f"--- [OKF CONCEPT #{idx}] ---")
            lines.append(f"Path: {concept.relative_path}")
            lines.append(f"Type: {fm.type}")
            if fm.title:
                lines.append(f"Title: {fm.title}")
            if fm.description:
                lines.append(f"Description: {fm.description}")
            if fm.resource:
                lines.append(f"Resource: {fm.resource}")
            if fm.tags:
                lines.append(f"Tags: {', '.join(fm.tags)}")
            if fm.status:
                lines.append(f"Status: {fm.status}")

            lines.append("\n[Content]:")
            lines.append(concept.content.strip())
            lines.append("\n" + "="*40 + "\n")

        lines.append("=== END OKF CONTEXT PAYLOAD ===")
        return "\n".join(lines)
