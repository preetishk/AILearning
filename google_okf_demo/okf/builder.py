"""
Open Knowledge Format (OKF) Builder
Programmatically creates, edits, and manages OKF Concepts, index.md catalog, and log.md audit entries.
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from .models import OKFFrontMatter, OKFConcept, OKFBundle
from .parser import OKFParser


class OKFBuilder:
    """Builder for programmatically managing OKF bundles."""

    @classmethod
    def create_concept(
        cls,
        bundle_root: Path,
        relative_path: str,
        frontmatter: OKFFrontMatter,
        body_markdown: str,
        update_log: bool = True
    ) -> OKFConcept:
        """Creates a new OKF Concept file within the bundle with valid frontmatter."""
        target_file = bundle_root / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Set default timestamp if missing
        if not frontmatter.timestamp:
            frontmatter.timestamp = datetime.now().isoformat()

        # Format YAML frontmatter
        yaml_str = yaml.dump(
            frontmatter.to_dict(),
            sort_keys=False,
            allow_unicode=True
        ).strip()

        file_content = f"---\n{yaml_str}\n---\n\n{body_markdown.strip()}\n"
        target_file.write_text(file_content, encoding="utf-8")

        concept = OKFParser.parse_file(target_file, bundle_root)

        if update_log:
            cls.append_log_entry(
                bundle_root,
                action="CREATE",
                concept_path=relative_path,
                details=f"Created concept '{frontmatter.title or relative_path}' of type '{frontmatter.type}'"
            )

        return concept

    @classmethod
    def append_log_entry(cls, bundle_root: Path, action: str, concept_path: str, details: str):
        """Appends a change audit record to the reserved log.md file."""
        log_file = bundle_root / "log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Header if log.md doesn't exist
        if not log_file.exists():
            log_content = "---\ntype: log\ntitle: OKF Change Audit Log\n---\n\n# OKF Audit Log\n\n| Timestamp | Action | Concept Path | Details |\n|---|---|---|---|\n"
            log_file.write_text(log_content, encoding="utf-8")

        entry_line = f"| {timestamp} | {action} | `{concept_path}` | {details} |\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry_line)

    @classmethod
    def rebuild_index(cls, bundle_root: Path) -> OKFConcept:
        """Scans the bundle and regenerates the reserved index.md catalog file."""
        bundle = OKFParser.parse_bundle(bundle_root)
        index_file = bundle_root / "index.md"

        frontmatter = {
            "type": "index",
            "title": "Open Knowledge Format Catalog",
            "description": "Auto-generated central index of all OKF knowledge units in this bundle.",
            "timestamp": datetime.now().isoformat()
        }

        yaml_str = yaml.dump(frontmatter, sort_keys=False).strip()

        lines = [f"---\n{yaml_str}\n---", "", "# Open Knowledge Format Catalog", ""]
        lines.append(f"Total Knowledge Units: **{len(bundle.concepts)}**\n")

        # Group concepts by type
        by_type = {}
        for rel_path, concept in bundle.concepts.items():
            if concept.is_reserved:
                continue
            ctype = concept.frontmatter.type
            if ctype not in by_type:
                by_type[ctype] = []
            by_type[ctype].append(concept)

        for ctype, concept_list in sorted(by_type.items()):
            lines.append(f"## Type: `{ctype}`")
            for c in sorted(concept_list, key=lambda x: x.relative_path):
                title = c.frontmatter.title or c.relative_path
                desc = f" - {c.frontmatter.description}" if c.frontmatter.description else ""
                lines.append(f"- [{title}](./{c.relative_path}){desc}")
            lines.append("")

        index_file.write_text("\n".join(lines), encoding="utf-8")
        return OKFParser.parse_file(index_file, bundle_root)
