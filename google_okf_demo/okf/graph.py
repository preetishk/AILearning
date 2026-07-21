"""
Open Knowledge Format (OKF) Knowledge Graph Engine
Builds and traverses graph relationships between concepts in an OKF bundle.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from collections import deque
from .models import OKFBundle, OKFConcept


class OKFKnowledgeGraph:
    """Knowledge Graph engine for analyzing concept relationships and dependencies."""

    def __init__(self, bundle: OKFBundle):
        self.bundle = bundle
        # Adjacency list: relative_path -> List[target_relative_path]
        self.outgoing: Dict[str, Set[str]] = {}
        # Reverse adjacency list (backlinks): target_relative_path -> List[source_relative_path]
        self.incoming: Dict[str, Set[str]] = {}

        self._build_graph()

    def _build_graph(self):
        """Constructs forward and backward edge sets from bundle links."""
        for path in self.bundle.concepts:
            self.outgoing[path] = set()
            self.incoming[path] = set()

        for path, concept in self.bundle.concepts.items():
            for link in concept.links:
                if link.resolved_path and link.resolved_path in self.bundle.concepts:
                    target = link.resolved_path
                    self.outgoing[path].add(target)
                    if target not in self.incoming:
                        self.incoming[target] = set()
                    self.incoming[target].add(path)

    def get_outgoing(self, concept_path: str) -> List[OKFConcept]:
        """Gets all concepts directly referenced by the given concept."""
        targets = self.outgoing.get(concept_path, set())
        return [self.bundle.concepts[t] for t in targets if t in self.bundle.concepts]

    def get_incoming(self, concept_path: str) -> List[OKFConcept]:
        """Gets all concepts that reference (link to) the given concept (backlinks)."""
        sources = self.incoming.get(concept_path, set())
        return [self.bundle.concepts[s] for s in sources if s in self.bundle.concepts]

    def get_neighborhood(self, start_path: str, max_depth: int = 2) -> Set[str]:
        """Traverses graph using BFS up to max_depth to return all connected concept paths."""
        if start_path not in self.bundle.concepts:
            return set()

        visited: Set[str] = {start_path}
        queue = deque([(start_path, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Look at both outgoing and incoming neighbors
            neighbors = self.outgoing.get(current, set()).union(self.incoming.get(current, set()))
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return visited

    def find_path(self, start_path: str, target_path: str) -> Optional[List[str]]:
        """Finds shortest directional path between start and target concepts using BFS."""
        if start_path not in self.bundle.concepts or target_path not in self.bundle.concepts:
            return None

        visited = {start_path}
        queue = deque([[start_path]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == target_path:
                return path

            for neighbor in self.outgoing.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

        return None

    def get_graph_stats(self) -> Dict[str, Any]:
        """Calculates graph metrics for the OKF bundle."""
        total_nodes = len(self.bundle.concepts)
        total_edges = sum(len(edges) for edges in self.outgoing.values())
        
        # Most referenced concept (highest in-degree)
        most_linked = sorted(
            self.incoming.items(), key=lambda x: len(x[1]), reverse=True
        )
        top_hubs = [(path, len(sources)) for path, sources in most_linked[:3]]

        return {
            "total_concepts": total_nodes,
            "total_relationships": total_edges,
            "top_referenced_concepts": top_hubs
        }
