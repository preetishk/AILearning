"""All Pydantic fact models + EntityRegistry."""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


def make_node_id(canonical_name: str) -> str:
    """SHA-256[:16] of canonical_name. Keep casing. Strip whitespace. UTF-8."""
    return hashlib.sha256(canonical_name.strip().encode("utf-8")).hexdigest()[:16]


# ── INPUT → TRANSFORM hand-off ───────────────────────────────────────────────

class Chunk(BaseModel):
    chunk_id: str
    source_type: Literal["code", "confluence", "sharepoint", "openapi", "runbook", "database", "jira", "markdown", "url"]
    source_ref: str
    source_line_start: int = 0
    source_line_end: int = 0
    language: Literal["csharp", "cpp", "typescript", "javascript", "python", "markdown", "html", "json", "yaml", "text"] = "text"
    content: str
    estimated_tokens: int = 0


# ── Layer 1 — structural.json ─────────────────────────────────────────────────

class Relation(BaseModel):
    type: Literal[
        "calls", "implements", "inherits", "references",
        "depends_on", "part_of", "emits", "produces"
    ]
    target: str  # fully qualified canonical name of target


class EntityFact(BaseModel):
    id: str
    canonical_name: str
    aliases: list[str] = []
    kind: Literal["class", "method", "interface", "enum", "property", "constant", "function", "module"]
    source_type: str = "code"
    source_ref: str
    source_line_start: int = 0
    source_line_end: int = 0
    layer: Optional[str] = None
    tags: list[str] = []
    relations: list[Relation] = []
    confidence: Literal["high", "medium", "low"] = "high"
    summary: Optional[str] = None
    _fact_kind: str = "entity"


# ── Layer 2 — behavioral.json ─────────────────────────────────────────────────

class RuleFact(BaseModel):
    id: str
    owner_entity: str
    condition: str
    true_path: str
    false_path: str
    linked_outcome: Optional[str] = None
    linked_resolution: Optional[str] = None
    source_ref: str
    source_line: int = 0
    source_type: str = "code"
    confidence: Literal["high", "medium", "low"] = "high"
    _fact_kind: str = "rule"


# ── Layer 3 — contracts.json ──────────────────────────────────────────────────

class InputParam(BaseModel):
    name: str
    type: str
    nullable: bool = False
    description: Optional[str] = None


class OutputParam(BaseModel):
    name: str
    type: str
    nullable: bool = False
    description: Optional[str] = None


class OutcomeCode(BaseModel):
    value_name: str
    meaning: str
    recoverable: bool = True
    severity: Literal["info", "warning", "error", "critical"] = "info"


class ContractFact(BaseModel):
    id: str
    entity_name: str
    summary: Optional[str] = None
    inputs: list[InputParam] = []
    outputs: list[OutputParam] = []
    outcome_codes: list[OutcomeCode] = []
    preconditions: Optional[str] = None
    postconditions: Optional[str] = None
    source_ref: str
    source_line: int = 0
    source_type: str = "code"
    _fact_kind: str = "contract"


# ── Layer 4 — operational.json ────────────────────────────────────────────────

class Assertion(BaseModel):
    what: str
    expected: str
    check_method: str


class ContextOverride(BaseModel):
    dependency: str
    override_type: str
    return_value: str


class OperationalFact(BaseModel):
    id: str
    trace_name: str
    scenario: str
    action: str
    assertions: list[Assertion] = []
    context_overrides: list[ContextOverride] = []
    implied_behavior: str = ""
    covers_failure_path: bool = False
    source_ref: str
    source_line: int = 0
    source_type: str = "code"
    _fact_kind: str = "operational"


# ── Layer 5 — evidence.json ───────────────────────────────────────────────────

class Evidence(BaseModel):
    fact_id: str
    source_file: str
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    source_snippet: str
    confidence: Literal["high", "medium", "low"] = "high"
    extraction_date: str
    alternative_interpretations: Optional[str] = None


class EvidenceFact(BaseModel):
    fact_id: str
    evidence: Evidence


# ── Vector DB document ────────────────────────────────────────────────────────

class VectorDocMetadata(BaseModel):
    layer: int
    fact_kind: str
    source_ref: str
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    confidence: str = "high"
    graph_node_id: Optional[str] = None
    aliases: list[str] = []
    source_type: str = "code"
    extraction_date: str


class VectorDocument(BaseModel):
    id: str
    collection: Literal[
        "BehavioralRule", "EntityContract", "OutcomeRecord",
        "ObservableEvent", "OperationalTrace", "DocumentSection"
    ]
    text: str
    metadata: VectorDocMetadata


# ── Graph DB structures ───────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    properties: dict


class GraphEdge(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    relation_type: str
    properties: dict = {}
    model_config = {"populate_by_name": True}


class GraphTriple(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    skipped_edges: list[dict] = []


# ── Entity Registry ───────────────────────────────────────────────────────────

class RegistryEntry(BaseModel):
    canonical_name: str
    node_id: str
    aliases: list[str] = []
    confidence: Literal["high", "medium", "low"] = "high"
    source_refs: list[str] = []


class EntityRegistry(BaseModel):
    entries: list[RegistryEntry] = []

    def lookup(self, name: str) -> Optional[str]:
        """Return the node_id for a canonical name or alias. Returns None if not found."""
        name_lower = name.lower().strip()
        for entry in self.entries:
            if entry.canonical_name.lower() == name_lower:
                return entry.node_id
            if any(a.lower() == name_lower for a in entry.aliases):
                return entry.node_id
        return None

    def get_entry(self, name: str) -> Optional[RegistryEntry]:
        """Return the RegistryEntry for a canonical name or alias."""
        name_lower = name.lower().strip()
        for entry in self.entries:
            if entry.canonical_name.lower() == name_lower:
                return entry
            if any(a.lower() == name_lower for a in entry.aliases):
                return entry
        return None

    def add_or_merge(self, canonical_name: str, aliases: list[str] = None,
                     source_ref: str = None, confidence: str = "high") -> RegistryEntry:
        """Add a new entry or merge aliases into existing entry."""
        node_id = make_node_id(canonical_name)
        existing = None
        for entry in self.entries:
            if entry.node_id == node_id:
                existing = entry
                break
        if existing:
            if aliases:
                existing.aliases = list(set(existing.aliases + aliases))
            if source_ref and source_ref not in existing.source_refs:
                existing.source_refs.append(source_ref)
            return existing
        entry = RegistryEntry(
            canonical_name=canonical_name,
            node_id=node_id,
            aliases=aliases or [],
            confidence=confidence,
            source_refs=[source_ref] if source_ref else [],
        )
        self.entries.append(entry)
        return entry


# ── Intent + Page result (agent layer) ───────────────────────────────────────

class IntentResult(BaseModel):
    question_type: Literal["structural", "behavioral", "semantic", "multi-hop"]
    primary_entities: list[str] = []
    requires_graph: bool = True
    requires_vector: bool = True
    cypher_hint: Optional[str] = None


class PageResult(BaseModel):
    primary_page: str = ""
    child_pages: list[str] = []
    source_refs: list[str] = []
    graph_node_ids: list[str] = []
    confidence: float = 0.0
