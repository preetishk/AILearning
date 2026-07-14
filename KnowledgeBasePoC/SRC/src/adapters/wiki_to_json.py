"""wiki_to_json adapter — converts OpenKB wiki/ pages into Chunk objects."""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from src.models.facts import Chunk

logger = logging.getLogger(__name__)


@dataclass
class SectionInfo:
    text: str
    heading: str
    start_line: int
    end_line: int


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns ({}, body) if no frontmatter."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip()
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}
    return fm, body


def _map_source_type(raw: str) -> str:
    mapping = {
        "code": "code",
        "confluence": "confluence",
        "sharepoint": "sharepoint",
        "openapi": "openapi",
        "runbook": "runbook",
        "markdown": "markdown",
        "url": "url",
        "html": "url",
    }
    return mapping.get(raw.lower(), "markdown")


def _split_at_h2(body: str) -> list[SectionInfo]:
    """Split Markdown body at ## headings."""
    lines = body.splitlines()
    sections: list[SectionInfo] = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    start_line = 0

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_lines and "".join(current_lines).strip():
                sections.append(SectionInfo(
                    text="\n".join(current_lines).strip(),
                    heading=current_heading,
                    start_line=start_line,
                    end_line=i - 1,
                ))
            current_heading = line[3:].strip()
            current_lines = []
            start_line = i
        else:
            current_lines.append(line)

    if current_lines and "".join(current_lines).strip():
        sections.append(SectionInfo(
            text="\n".join(current_lines).strip(),
            heading=current_heading,
            start_line=start_line,
            end_line=start_line + len(current_lines) - 1,
        ))

    return sections


def convert_wiki_to_chunks(wiki_dir: Path) -> list[Chunk]:
    """
    Convert all Markdown wiki pages in wiki_dir into Chunk objects.

    Pages in wiki/concepts/ and wiki/summaries/ are processed.
    YAML frontmatter is parsed to extract source metadata.
    The body is split at ## headings — each section becomes one Chunk.
    """
    chunks: list[Chunk] = []
    wiki_path = wiki_dir if isinstance(wiki_dir, Path) else Path(wiki_dir)

    patterns = [
        wiki_path / "concepts" / "*.md",
        wiki_path / "summaries" / "*.md",
    ]

    all_pages: list[Path] = []
    for pattern in patterns:
        all_pages.extend(wiki_path.glob(str(pattern.relative_to(wiki_path))))

    if not all_pages:
        logger.debug(f"No wiki pages found in {wiki_dir}")
        return chunks

    for page_path in all_pages:
        try:
            text = page_path.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(text)

            source_refs = fm.get("source_refs", [fm.get("source_ref", str(page_path))])
            if isinstance(source_refs, str):
                source_refs = [source_refs]

            source_types = fm.get("source_types", ["markdown"])
            if isinstance(source_types, str):
                source_types = [source_types]
            primary_source_type = _map_source_type(source_types[0] if source_types else "markdown")

            sections = _split_at_h2(body)
            if not sections:
                # Treat entire body as single chunk
                chunk_id = hashlib.sha256(str(page_path).encode()).hexdigest()[:16]
                if body.strip():
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        source_type=primary_source_type,
                        source_ref=source_refs[0] if source_refs else str(page_path),
                        source_line_start=0,
                        source_line_end=body.count("\n"),
                        language="markdown",
                        content=body.strip(),
                        estimated_tokens=max(1, len(body) // 4),
                    ))
                continue

            for section in sections:
                content = f"## {section.heading}\n{section.text}" if section.text else ""
                if not content.strip():
                    continue
                chunk_id = hashlib.sha256(
                    f"{page_path}:{section.start_line}".encode()
                ).hexdigest()[:16]
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    source_type=primary_source_type,
                    source_ref=source_refs[0] if source_refs else str(page_path),
                    source_line_start=section.start_line,
                    source_line_end=section.end_line,
                    language="markdown",
                    content=content,
                    estimated_tokens=max(1, len(content) // 4),
                ))
        except Exception as e:
            logger.warning(f"Failed to parse wiki page {page_path}: {e}")

    logger.info(f"Converted {len(all_pages)} wiki pages → {len(chunks)} chunks")
    return chunks
