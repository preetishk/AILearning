"""Job manager — tracks ingestion job state and orchestrates the full pipeline."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class IngestJob:
    job_id: str
    source_label: str
    source_type: Literal["file", "repo", "url"]
    status: Literal["queued", "running", "done", "failed"] = "queued"
    progress_pct: float = 0.0
    current_step: str = "Queued"
    facts_extracted: int = 0
    nodes_written: int = 0
    vectors_written: int = 0
    files_total: int = 0
    files_changed: int = 0
    files_skipped: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    max_tokens: int = 1500
    language: str = "auto"
    branch: str = "main"
    path_filter: str = ""
    force: bool = False


# Module-level registry: job_id → IngestJob
_jobs: dict[str, IngestJob] = {}
_lock = asyncio.Lock()


class JobManager:
    """Manages the lifecycle of ingestion jobs."""

    @staticmethod
    async def submit(source_label: str, source_type: str, **kwargs) -> IngestJob:
        job = IngestJob(
            job_id=str(uuid.uuid4()),
            source_label=source_label,
            source_type=source_type,
            **{k: v for k, v in kwargs.items() if hasattr(IngestJob, k)},
        )
        _jobs[job.job_id] = job
        return job

    @staticmethod
    def get(job_id: str) -> Optional[IngestJob]:
        return _jobs.get(job_id)

    @staticmethod
    def list_all() -> list[IngestJob]:
        return sorted(_jobs.values(), key=lambda j: j.started_at or "", reverse=True)

    @staticmethod
    def cancel(job_id: str) -> bool:
        job = _jobs.get(job_id)
        if job and job.status in ("queued", "running"):
            job.status = "failed"
            job.error = "Cancelled by user"
            return True
        return False

    @staticmethod
    def _update(job: IngestJob, step: str, pct: float, **counters):
        job.current_step = step
        job.progress_pct = pct
        for k, v in counters.items():
            if hasattr(job, k):
                setattr(job, k, v)


async def run_ingest_job(job: IngestJob, source_path: Path) -> None:
    """
    Run the full 6-step ingestion pipeline for a job.
    Updates job state in-place as steps complete.
    """
    job.status = "running"
    job.started_at = datetime.now(timezone.utc).isoformat()

    raw_docs_dir = Path(os.getenv("RAW_DOCS_DIR", "./raw_docs"))
    input_dir = Path(os.getenv("INPUT_DIR", "./input"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Step 1: Scan & Chunk ─────────────────────────────────────────────
        JobManager._update(job, "Step 1/6 — Scanning & chunking files", 5.0)
        from src.pipeline.walker import walk_dir, infer_language, ALL_SUPPORTED
        from src.pipeline.chunker import chunk_file

        all_files = walk_dir(
            str(source_path),
            exts=ALL_SUPPORTED,
            path_filter=job.path_filter or None,
        )

        if not job.force:
            # Incremental: compute file hashes and skip unchanged
            hash_file = output_dir / f"{_slug(job.source_label)}_hashes.json"
            old_hashes: dict[str, str] = {}
            if hash_file.exists():
                old_hashes = json.loads(hash_file.read_text())

            changed_files = []
            skipped = 0
            new_hashes: dict[str, str] = {}
            for fp in all_files:
                fhash = _file_hash(fp)
                new_hashes[str(fp)] = fhash
                if old_hashes.get(str(fp)) == fhash:
                    skipped += 1
                else:
                    changed_files.append(fp)
            hash_file.write_text(json.dumps(new_hashes), encoding="utf-8")
            job.files_total = len(all_files)
            job.files_skipped = skipped
            job.files_changed = len(changed_files)
            all_files = changed_files
        else:
            job.files_total = len(all_files)
            job.files_changed = len(all_files)

        logger.info(f"Files to process: {len(all_files)}")

        all_chunks = []
        for fp in all_files:
            lang = infer_language(fp) if job.language == "auto" else job.language
            try:
                chunks = chunk_file(fp, language=lang, max_tokens=job.max_tokens)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to chunk {fp}: {e}")

        JobManager._update(job, f"Step 1/6 — Chunked {len(all_chunks)} chunks", 15.0)

        # ── Step 2: Extract Facts (LLM) ──────────────────────────────────────
        JobManager._update(job, "Step 2/6 — Extracting facts (Layer 1)", 20.0)
        from src.pipeline.extractor import extract_all_layers

        layers = extract_all_layers(all_chunks)
        total_facts = sum(len(v) for v in layers.values())
        job.facts_extracted = total_facts

        # Persist extracted facts
        _save_json(input_dir / "structural.json", [f.model_dump() for f in layers[1]])
        _save_json(input_dir / "behavioral.json", [f.model_dump() for f in layers[2]])
        _save_json(input_dir / "contracts.json", [f.model_dump() for f in layers[3]])
        _save_json(input_dir / "operational.json", [f.model_dump() for f in layers[4]])
        _save_json(input_dir / "evidence.json", [f.model_dump() for f in layers[5]])

        JobManager._update(job, f"Step 2/6 — Extracted {total_facts} facts", 40.0,
                           facts_extracted=total_facts)

        # ── Step 3: Provenance enrichment ────────────────────────────────────
        JobManager._update(job, "Step 3/6 — Provenance enrichment", 50.0)
        # Evidence already generated in layer 5 during extraction

        # ── Step 4: Entity Resolution ────────────────────────────────────────
        JobManager._update(job, "Step 4/6 — Entity resolution", 60.0)
        from src.pipeline.resolver import resolve_entities
        registry = resolve_entities(str(input_dir), str(output_dir))
        JobManager._update(job, f"Step 4/6 — Registry: {len(registry.entries)} entities", 65.0)

        # ── Step 5: Graph DB Insert ──────────────────────────────────────────
        JobManager._update(job, "Step 5/6 — Writing to graph database", 70.0)
        from src.pipeline.hydrator import hydrate, write_to_graph
        from src.storage.protocols import get_graph_store
        try:
            graph_store = get_graph_store()
            triple = hydrate(layers, registry)
            stats = write_to_graph(triple, graph_store)
            job.nodes_written = stats["nodes_written"]
            graph_store.close()
        except Exception as e:
            logger.warning(f"Graph DB write failed (continuing): {e}")

        JobManager._update(job, f"Step 5/6 — Graph: {job.nodes_written} nodes", 80.0,
                           nodes_written=job.nodes_written)

        # ── Step 6: Vector DB Embed & Insert ─────────────────────────────────
        JobManager._update(job, "Step 6/6 — Embedding and inserting into vector DB", 85.0)
        from src.storage.protocols import get_vector_store
        from src.pipeline.extractor import route_to_collection, build_vector_text

        try:
            vector_store = get_vector_store()
            embed_model = _load_embed_model()
            vectors_written = 0

            # Layer 2: behavioral
            for rule in layers[2]:
                d = rule.model_dump()
                d["_fact_kind"] = "rule"
                text = build_vector_text(d)
                node_id = registry.lookup(d.get("owner_entity", ""))
                collection = route_to_collection(d)
                vec = _embed(text, embed_model)
                vector_store.upsert(
                    collection=collection,
                    doc_id=f"vec-{rule.id}",
                    text=text,
                    embedding=vec,
                    metadata={
                        "layer": 2,
                        "fact_kind": "rule",
                        "source_ref": rule.source_ref,
                        "graph_node_id": node_id or "",
                        "confidence": rule.confidence,
                        "source_type": rule.source_type,
                        "extraction_date": datetime.now(timezone.utc).date().isoformat(),
                    },
                )
                vectors_written += 1

            # Layer 3: contracts
            for contract in layers[3]:
                d = contract.model_dump()
                d["_fact_kind"] = "contract"
                text = build_vector_text(d)
                collection = route_to_collection(d)
                vec = _embed(text, embed_model)
                vector_store.upsert(
                    collection=collection,
                    doc_id=f"vec-{contract.id}",
                    text=text,
                    embedding=vec,
                    metadata={
                        "layer": 3,
                        "fact_kind": "contract",
                        "source_ref": contract.source_ref,
                        "confidence": "high",
                        "source_type": contract.source_type,
                        "extraction_date": datetime.now(timezone.utc).date().isoformat(),
                    },
                )
                vectors_written += 1

            # Layer 4: operational
            for op in layers[4]:
                d = op.model_dump()
                d["_fact_kind"] = "operational"
                text = build_vector_text(d)
                vec = _embed(text, embed_model)
                vector_store.upsert(
                    collection="OperationalTrace",
                    doc_id=f"vec-{op.id}",
                    text=text,
                    embedding=vec,
                    metadata={
                        "layer": 4,
                        "fact_kind": "operational",
                        "source_ref": op.source_ref,
                        "confidence": "high",
                        "source_type": op.source_type,
                        "extraction_date": datetime.now(timezone.utc).date().isoformat(),
                    },
                )
                vectors_written += 1

            job.vectors_written = vectors_written

        except Exception as e:
            logger.warning(f"Vector DB write failed (continuing): {e}")

        JobManager._update(job, f"Step 6/6 — Vectors: {job.vectors_written} docs", 100.0,
                           vectors_written=job.vectors_written)

        job.status = "done"
        job.completed_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"Job {job.job_id} completed: {job.facts_extracted} facts, "
                    f"{job.nodes_written} nodes, {job.vectors_written} vectors")

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.completed_at = datetime.now(timezone.utc).isoformat()
        logger.error(f"Job {job.job_id} failed: {e}", exc_info=True)


def _slug(label: str) -> str:
    return label.replace("/", "_").replace("\\", "_").replace(":", "")[:40]


def _file_hash(path: Path) -> str:
    try:
        data = path.read_bytes()
        return hashlib.md5(data).hexdigest()
    except Exception:
        return ""


def _save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _load_embed_model():
    """Load the configured embedding model object."""
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    if "text-embedding" in model_name:
        return {"provider": "openai", "model": model_name}
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except Exception:
        return {"provider": "openai", "model": model_name}


def _embed(text: str, model) -> list[float]:
    """Embed a single text using the loaded model."""
    try:
        if isinstance(model, dict) and model.get("provider") == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(model=model["model"], input=[text])
            return response.data[0].embedding
        else:
            vec = model.encode([text])[0]
            return vec.tolist()
    except Exception:
        return [0.0] * 384
