"""
Open Knowledge Format (OKF) Data Models
Defines core data structures for OKF Concepts, FrontMatter, Validation Issues, and Bundles.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime


@dataclass
class OKFFrontMatter:
    """Represents the YAML frontmatter of an OKF Markdown file."""
    type: str  # Mandatory OKF field (e.g., 'service', 'database_table', 'metric', 'runbook')
    title: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None  # URI or external reference
    tags: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = "active"  # e.g., active, draft, deprecated
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert frontmatter to a dictionary suitable for YAML dumping."""
        data = {"type": self.type}
        if self.title:
            data["title"] = self.title
        if self.description:
            data["description"] = self.description
        if self.resource:
            data["resource"] = self.resource
        if self.tags:
            data["tags"] = self.tags
        if self.timestamp:
            data["timestamp"] = self.timestamp
        if self.author:
            data["author"] = self.author
        if self.version:
            data["version"] = self.version
        if self.status:
            data["status"] = self.status
        data.update(self.extra_fields)
        return data


@dataclass
class OKFLink:
    """Represents an intra-bundle markdown hyperlink connection between concepts."""
    title: str
    target_path: str  # Path relative to bundle root or relative to source concept
    resolved_path: Optional[str] = None  # Normalized relative path from bundle root


@dataclass
class OKFConcept:
    """Represents a single OKF unit of knowledge (a Markdown file with YAML frontmatter)."""
    file_path: Path
    relative_path: str  # Identifier in bundle (e.g. 'services/auth_service.md')
    frontmatter: OKFFrontMatter
    content: str  # Markdown body content (excluding frontmatter)
    links: List[OKFLink] = field(default_factory=list)

    @property
    def is_reserved(self) -> bool:
        """Check if file is a reserved OKF system file (index.md or log.md)."""
        filename = self.file_path.name.lower()
        return filename in ("index.md", "log.md")


@dataclass
class OKFValidationIssue:
    """Represents a schema or link validation issue found during OKF bundle audit."""
    severity: str  # 'ERROR' or 'WARNING'
    concept_path: str
    message: str
    field_name: Optional[str] = None


@dataclass
class OKFBundle:
    """Represents a full OKF Knowledge Bundle (directory tree of concepts)."""
    root_path: Path
    concepts: Dict[str, OKFConcept] = field(default_factory=dict)  # relative_path -> OKFConcept
    index_concept: Optional[OKFConcept] = None
    log_concept: Optional[OKFConcept] = None

    def get_concept(self, relative_path: str) -> Optional[OKFConcept]:
        """Get a concept by its relative path within the bundle."""
        normalized = relative_path.replace("\\", "/").strip("./")
        return self.concepts.get(normalized)

    def list_concepts_by_type(self, concept_type: str) -> List[OKFConcept]:
        """List all concepts matching a given type (e.g., 'metric', 'runbook')."""
        return [c for c in self.concepts.values() if c.frontmatter.type.lower() == concept_type.lower()]

    def list_concepts_by_tag(self, tag: str) -> List[OKFConcept]:
        """List all concepts matching a specific tag."""
        tag_lower = tag.lower()
        return [c for c in self.concepts.values() if any(t.lower() == tag_lower for t in c.frontmatter.tags)]
