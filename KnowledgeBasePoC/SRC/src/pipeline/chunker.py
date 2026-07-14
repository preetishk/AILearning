"""Chunker — splits source files into Chunk objects respecting token budgets."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Optional

from src.models.facts import Chunk
from src.pipeline.walker import infer_language


def _count_tokens(text: str) -> int:
    """Estimate token count using tiktoken if available, else word-based estimate."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


def _make_chunk_id(source_ref: str, start_line: int) -> str:
    raw = f"{source_ref}:{start_line}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _split_by_lines(content: str, max_tokens: int, source_ref: str,
                    source_type: str, language: str) -> list[Chunk]:
    """Fallback: split by line count when tree-sitter is not available."""
    lines = content.splitlines()
    chunks: list[Chunk] = []
    current_lines: list[str] = []
    current_start = 0
    current_tokens = 0

    for i, line in enumerate(lines):
        line_tokens = max(1, len(line) // 4)
        if current_tokens + line_tokens > max_tokens and current_lines:
            text = "\n".join(current_lines)
            chunks.append(Chunk(
                chunk_id=_make_chunk_id(source_ref, current_start),
                source_type=source_type,
                source_ref=source_ref,
                source_line_start=current_start,
                source_line_end=current_start + len(current_lines) - 1,
                language=language,
                content=text,
                estimated_tokens=current_tokens,
            ))
            current_lines = [line]
            current_start = i
            current_tokens = line_tokens
        else:
            current_lines.append(line)
            current_tokens += line_tokens

    if current_lines:
        text = "\n".join(current_lines)
        chunks.append(Chunk(
            chunk_id=_make_chunk_id(source_ref, current_start),
            source_type=source_type,
            source_ref=source_ref,
            source_line_start=current_start,
            source_line_end=current_start + len(current_lines) - 1,
            language=language,
            content=text,
            estimated_tokens=current_tokens,
        ))
    return chunks


def _split_by_headings(content: str, source_ref: str,
                        language: str, max_tokens: int) -> list[Chunk]:
    """Split Markdown at ## headings."""
    sections = re.split(r'^(##[^#].*?)$', content, flags=re.MULTILINE)
    chunks: list[Chunk] = []
    line_offset = 0
    current_title = ""
    current_body = ""

    for part in sections:
        if part.startswith("##"):
            if current_body.strip():
                text = (current_title + "\n" + current_body).strip()
                chunks.append(Chunk(
                    chunk_id=_make_chunk_id(source_ref, line_offset),
                    source_type="markdown",
                    source_ref=source_ref,
                    source_line_start=line_offset,
                    source_line_end=line_offset + current_body.count("\n"),
                    language=language,
                    content=text,
                    estimated_tokens=_count_tokens(text),
                ))
            current_title = part
            current_body = ""
            line_offset += part.count("\n") + 1
        else:
            current_body += part
            line_offset += part.count("\n")

    if current_body.strip():
        text = (current_title + "\n" + current_body).strip()
        chunks.append(Chunk(
            chunk_id=_make_chunk_id(source_ref, line_offset),
            source_type="markdown",
            source_ref=source_ref,
            source_line_start=line_offset,
            source_line_end=line_offset + current_body.count("\n"),
            language=language,
            content=text,
            estimated_tokens=_count_tokens(text),
        ))

    return chunks if chunks else _split_by_lines(content, max_tokens, source_ref, "markdown", language)


def _chunk_with_treesitter(content: str, language: str, max_tokens: int,
                            source_ref: str, source_type: str) -> Optional[list[Chunk]]:
    """Use tree-sitter to split at AST node boundaries."""
    try:
        from tree_sitter_languages import get_language, get_parser

        ts_lang_map = {
            "csharp": "c_sharp",
            "cpp": "cpp",
            "typescript": "typescript",
            "javascript": "javascript",
            "python": "python",
        }
        ts_lang_name = ts_lang_map.get(language)
        if not ts_lang_name:
            return None

        lang = get_language(ts_lang_name)
        parser = get_parser(ts_lang_name)

        tree = parser.parse(content.encode("utf-8"))
        root = tree.root_node

        NODE_TYPES = {
            "c_sharp": {"class_declaration", "method_declaration", "interface_declaration",
                        "enum_declaration", "constructor_declaration"},
            "cpp": {"class_specifier", "function_definition", "struct_specifier"},
            "typescript": {"class_declaration", "method_definition", "function_declaration",
                           "arrow_function", "interface_declaration"},
            "javascript": {"class_declaration", "method_definition", "function_declaration",
                           "arrow_function"},
            "python": {"class_definition", "function_definition"},
        }
        target_types = NODE_TYPES.get(ts_lang_name, set())

        chunks: list[Chunk] = []
        lines = content.splitlines()

        def extract_nodes(node):
            if node.type in target_types:
                start_line = node.start_point[0]
                end_line = node.end_point[0]
                text = "\n".join(lines[start_line:end_line + 1])
                tokens = _count_tokens(text)
                if tokens <= max_tokens:
                    chunks.append(Chunk(
                        chunk_id=_make_chunk_id(source_ref, start_line),
                        source_type=source_type,
                        source_ref=source_ref,
                        source_line_start=start_line,
                        source_line_end=end_line,
                        language=language,
                        content=text,
                        estimated_tokens=tokens,
                    ))
                    return  # don't recurse into already-captured node
            for child in node.children:
                extract_nodes(child)

        extract_nodes(root)

        if not chunks:
            return None
        return chunks

    except Exception:
        return None


def chunk_file(path: Path, language: str = None, max_tokens: int = 1500,
               source_type: str = None) -> list[Chunk]:
    """
    Split a file into Chunk objects.

    Strategy:
        - Code files (.cs, .cpp, .ts, .js, .py): tree-sitter AST nodes, fallback to line split
        - Markdown files: split at ## headings
        - JSON/YAML: emit as single chunk (schemas are small)
        - Other: line-based split
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return []

    if not content.strip():
        return []

    language = language or infer_language(path)
    source_ref = str(path).replace("\\", "/")
    detected_source_type = source_type or _detect_source_type(path)

    # Schema files — single chunk
    if path.suffix.lower() in {".json", ".yaml", ".yml"}:
        return [Chunk(
            chunk_id=_make_chunk_id(source_ref, 0),
            source_type="openapi",
            source_ref=source_ref,
            source_line_start=0,
            source_line_end=content.count("\n"),
            language=language,
            content=content,
            estimated_tokens=_count_tokens(content),
        )]

    # Markdown — split at headings
    if language == "markdown":
        return _split_by_headings(content, source_ref, language, max_tokens)

    # Code — try tree-sitter first
    if language in {"csharp", "cpp", "typescript", "javascript", "python"}:
        chunks = _chunk_with_treesitter(content, language, max_tokens, source_ref, detected_source_type)
        if chunks:
            return chunks

    # Fallback — line-based split
    return _split_by_lines(content, max_tokens, source_ref, detected_source_type, language)


def _detect_source_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".cs", ".cpp", ".h", ".ts", ".js", ".py"}:
        return "code"
    if ext in {".md", ".txt"}:
        return "markdown"
    if ext in {".json", ".yaml", ".yml"}:
        return "openapi"
    return "code"
