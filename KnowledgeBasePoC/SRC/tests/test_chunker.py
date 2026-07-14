"""Tests for the file walker and chunker."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.pipeline.walker import walk_dir, infer_language
from src.pipeline.chunker import chunk_file


# ── walker tests ──────────────────────────────────────────────────────────────

def test_infer_language():
    assert infer_language(Path("foo.py")) == "python"
    assert infer_language(Path("bar.ts")) == "typescript"
    assert infer_language(Path("baz.cs")) == "csharp"
    assert infer_language(Path("unknown.xyz")) is None


def test_walk_dir_collects_py(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.md").write_text("# doc")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.py").write_text("# should be excluded")

    files = list(walk_dir(tmp_path))
    paths = [f.path for f in files]
    assert any("a.py" in str(p) for p in paths)
    assert any("b.md" in str(p) for p in paths)
    assert not any("node_modules" in str(p) for p in paths)


# ── chunker tests ─────────────────────────────────────────────────────────────

def test_chunk_file_python(tmp_path):
    code = textwrap.dedent("""\
        def foo():
            return 1

        def bar():
            return 2
    """)
    fp = tmp_path / "sample.py"
    fp.write_text(code)

    chunks = chunk_file(fp, max_tokens=256)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.source_ref.endswith("sample.py")
        assert c.language == "python"
        assert c.text.strip()
        assert c.token_count > 0


def test_chunk_file_markdown(tmp_path):
    md = textwrap.dedent("""\
        # Title

        Intro paragraph.

        ## Section A

        Content A.

        ## Section B

        Content B.
    """)
    fp = tmp_path / "doc.md"
    fp.write_text(md)

    chunks = chunk_file(fp, max_tokens=256)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.source_type in ("markdown", "documentation", "text")


def test_chunk_respects_token_limit(tmp_path):
    # Create a very long file
    lines = [f"# line {i}" for i in range(500)]
    fp = tmp_path / "big.md"
    fp.write_text("\n".join(lines))

    chunks = chunk_file(fp, max_tokens=128)
    for c in chunks:
        assert c.token_count <= 128 * 1.1  # allow 10% overflow


def test_chunk_empty_file(tmp_path):
    fp = tmp_path / "empty.py"
    fp.write_text("")
    chunks = chunk_file(fp, max_tokens=512)
    assert chunks == [] or all(c.text.strip() == "" for c in chunks)
