"""Ingest routes — file upload, git repo, URL ingestion, job management."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from src.api.schemas import (
    IngestRepoRequest, IngestUrlRequest,
    JobListResponse, JobStatusResponse,
)
from src.pipeline.job_manager import IngestJob, JobManager, run_ingest_job

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_EXTENSIONS = {
    ".cs", ".cpp", ".h", ".ts", ".js", ".py",
    ".md", ".pdf", ".docx", ".json", ".yaml", ".yml",
}


def _job_to_response(job: IngestJob) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=job.job_id,
        source_label=job.source_label,
        source_type=job.source_type,
        status=job.status,
        progress_pct=job.progress_pct,
        current_step=job.current_step,
        facts_extracted=job.facts_extracted,
        nodes_written=job.nodes_written,
        vectors_written=job.vectors_written,
        files_total=job.files_total,
        files_changed=job.files_changed,
        files_skipped=job.files_skipped,
        error=job.error,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/file", response_model=JobStatusResponse)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    max_tokens: int = Form(1500),
    layers: str = Form("1,2,3,4,5"),
):
    """Upload a single file and start ingestion."""
    fpath = Path(file.filename or "upload")
    ext = fpath.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Save to RAW_DOCS_DIR
    from src.adapters.file_ingester import save_upload
    file_bytes = await file.read()
    try:
        dest_path = save_upload(file_bytes, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job = await JobManager.submit(
        source_label=file.filename or "upload",
        source_type="file",
        max_tokens=max_tokens,
        language=language,
    )

    async def run():
        await run_ingest_job(job, dest_path)

    background_tasks.add_task(run)
    return _job_to_response(job)


@router.post("/repo", response_model=JobStatusResponse)
async def ingest_repo(body: IngestRepoRequest, background_tasks: BackgroundTasks):
    """Provide a Git repo URL and start ingestion."""
    job = await JobManager.submit(
        source_label=body.repo_url,
        source_type="repo",
        max_tokens=body.max_tokens,
        language=body.language,
        branch=body.branch,
        path_filter=body.path_filter,
        force=body.force,
    )

    async def run():
        from src.adapters.git_ingester import clone_repo
        try:
            repo_path = clone_repo(
                body.repo_url,
                branch=body.branch,
                force=body.force,
            )
            await run_ingest_job(job, repo_path)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            from datetime import datetime, timezone
            job.completed_at = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(run)
    return _job_to_response(job)


@router.post("/url", response_model=JobStatusResponse)
async def ingest_url(body: IngestUrlRequest, background_tasks: BackgroundTasks):
    """Fetch a web page and ingest it."""
    label = body.title or body.url

    job = await JobManager.submit(
        source_label=label,
        source_type="url",
        max_tokens=body.max_tokens,
    )

    async def run():
        from src.adapters.file_ingester import fetch_url
        try:
            dest_path = fetch_url(body.url)
            await run_ingest_job(job, dest_path)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            from datetime import datetime, timezone
            job.completed_at = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(run)
    return _job_to_response(job)


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs():
    """Return all current and recent ingestion jobs."""
    jobs = JobManager.list_all()
    return JobListResponse(jobs=[_job_to_response(j) for j in jobs])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    """Get status and progress of a specific ingestion job."""
    job = JobManager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _job_to_response(job)


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    """Cancel a queued or running job."""
    cancelled = JobManager.cancel(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or already terminal")
