"""Pydantic API request/response schemas."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel


# ── Ingest requests ───────────────────────────────────────────────────────────

class IngestRepoRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    path_filter: str = ""
    language: str = "auto"
    max_tokens: int = 1500
    force: bool = False
    layers: list[int] = [1, 2, 3, 4, 5]


class IngestUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    max_tokens: int = 1500


# ── Job status ────────────────────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    job_id: str
    source_label: str
    source_type: Literal["file", "repo", "url"]
    status: Literal["queued", "running", "done", "failed"]
    progress_pct: float = 0.0
    current_step: str = ""
    facts_extracted: int = 0
    nodes_written: int = 0
    vectors_written: int = 0
    files_total: int = 0
    files_changed: int = 0
    files_skipped: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: list[JobStatusResponse]


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    retrieval_mode: Literal["both", "graph", "vector"] = "both"
    top_k: int = 10
    filter_layer: Optional[int] = None
    filter_source_type: Optional[str] = None


class CitationItem(BaseModel):
    fact_id: str
    source_ref: str
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    snippet: str = ""
    relevance_score: float = 0.0
    confidence: str = "medium"
    graph_path: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    question_type: str = "semantic"
    overall_confidence: float = 0.0
    answer_grounded: bool = False
    citations: list[CitationItem] = []
    graph_paths: list[str] = []
    retrieval_lanes_used: list[str] = []


# ── Stats ─────────────────────────────────────────────────────────────────────

class CollectionCount(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    graph_node_count: int = 0
    graph_edge_count: int = 0
    vector_doc_count: int = 0
    entity_registry_size: int = 0
    collection_counts: list[CollectionCount] = []
    total_sources_ingested: int = 0
    last_ingest_at: Optional[str] = None


# ── Entity browser ────────────────────────────────────────────────────────────

class EntityRow(BaseModel):
    id: str
    canonical_name: str
    kind: str = ""
    source_ref: str = ""
    source_type: str = ""
    confidence: str = "high"
    summary: Optional[str] = None
    aliases: list[str] = []


class EntityListResponse(BaseModel):
    entities: list[EntityRow]
    total: int
    skip: int
    limit: int


class RelationshipItem(BaseModel):
    rel_type: str
    target: str
    target_kind: str = ""
    direction: str = "outbound"


class EntityDetailResponse(BaseModel):
    id: str
    canonical_name: str
    kind: str = ""
    source_ref: str = ""
    source_line_start: Optional[int] = None
    source_line_end: Optional[int] = None
    source_type: str = ""
    confidence: str = "high"
    summary: Optional[str] = None
    aliases: list[str] = []
    relationships: list[RelationshipItem] = []


# ── Graph analysis ────────────────────────────────────────────────────────────

class GraphAnalysisRequest(BaseModel):
    source_entity: str
    target_entity: Optional[str] = None
    analysis_type: Literal["shortest_path", "all_paths", "impact", "reverse_deps"] = "impact"
    max_depth: int = 3


class PathStep(BaseModel):
    node_name: str
    rel_type: Optional[str] = None
    source_ref: Optional[str] = None


class GraphAnalysisResponse(BaseModel):
    analysis_type: str
    source_entity: str
    target_entity: Optional[str] = None
    paths: list[list[PathStep]] = []
    nodes: list[dict] = []
    summary: str = ""
