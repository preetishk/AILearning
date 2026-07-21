"""
Open Knowledge Format (OKF) Parser
Parses OKF Markdown files containing YAML frontmatter and extracts metadata, content, and links.
"""

import re
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from .models import OKFFrontMatter, OKFConcept, OKFLink, OKFBundle


class OKFParser:
    """Parser for Open Knowledge Format (OKF) files and directory bundles."""

    # Regex to extract YAML frontmatter delimited by top-and-bottom ---
    FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
    
    # Regex to extract Markdown links: [Title](relative/path.md)
    MARKDOWN_LINK_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")

    @classmethod
    def parse_file(cls, file_path: Path, bundle_root: Path) -> OKFConcept:
        """Parses a single OKF Markdown file."""
        content = file_path.read_text(encoding="utf-8")
        raw_frontmatter, body_content = cls._extract_frontmatter_and_body(content)
        
        frontmatter_dict = cls._parse_yaml(raw_frontmatter)
        frontmatter = cls._build_frontmatter_model(frontmatter_dict)
        
        # Calculate normalized relative path from bundle root
        rel_path = file_path.relative_to(bundle_root).as_posix()
        
        # Extract markdown links and resolve their target paths relative to bundle root
        links = cls._extract_links(body_content, file_path, bundle_root)

        return OKFConcept(
            file_path=file_path,
            relative_path=rel_path,
            frontmatter=frontmatter,
            content=body_content,
            links=links
        )

    @classmethod
    def parse_bundle(cls, bundle_path: Path) -> OKFBundle:
        """Recursively parses an entire directory tree as an OKF Bundle."""
        bundle_path = bundle_path.resolve()
        if not bundle_path.is_dir():
            raise ValueError(f"OKF Bundle path does not exist or is not a directory: {bundle_path}")

        bundle = OKFBundle(root_path=bundle_path)

        # Walk all .md files in the bundle directory
        for md_file in bundle_path.glob("**/*.md"):
            try:
                concept = cls.parse_file(md_file, bundle_path)
                bundle.concepts[concept.relative_path] = concept
                
                # Check for reserved OKF files
                filename = md_file.name.lower()
                if filename == "index.md" and md_file.parent == bundle_path:
                    bundle.index_concept = concept
                elif filename == "log.md" and md_file.parent == bundle_path:
                    bundle.log_concept = concept
            except Exception as e:
                # Log error or store broken concept fallback
                print(f"[OKFParser Warning] Failed to parse {md_file}: {e}")

        return bundle

    @classmethod
    def _extract_frontmatter_and_body(cls, text: str) -> Tuple[str, str]:
        """Separates YAML frontmatter from Markdown body text."""
        match = cls.FRONTMATTER_REGEX.match(text)
        if match:
            return match.group(1), match.group(2)
        return "", text

    @classmethod
    def _parse_yaml(cls, raw_yaml: str) -> Dict[str, Any]:
        """Parses YAML text safely."""
        if not raw_yaml.strip():
            return {}
        try:
            parsed = yaml.safe_load(raw_yaml)
            return parsed if isinstance(parsed, dict) else {}
        except yaml.YAMLError:
            return {}

    @classmethod
    def _build_frontmatter_model(cls, data: Dict[str, Any]) -> OKFFrontMatter:
        """Constructs an OKFFrontMatter model from parsed YAML dictionary."""
        # Extract known OKF spec fields
        concept_type = str(data.get("type", "unknown"))
        title = data.get("title")
        description = data.get("description")
        resource = data.get("resource")
        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        timestamp = str(data.get("timestamp")) if data.get("timestamp") is not None else None
        author = data.get("author")
        version = str(data.get("version")) if data.get("version") is not None else None
        status = data.get("status", "active")

        # Capture extra fields for extensible metadata
        known_keys = {"type", "title", "description", "resource", "tags", "timestamp", "author", "version", "status"}
        extra = {k: v for k, v in data.items() if k not in known_keys}

        return OKFFrontMatter(
            type=concept_type,
            title=title,
            description=description,
            resource=resource,
            tags=list(tags),
            timestamp=timestamp,
            author=author,
            version=version,
            status=status,
            extra_fields=extra
        )

    @classmethod
    def _extract_links(cls, content: str, current_file: Path, bundle_root: Path) -> List[OKFLink]:
        """Finds markdown links [Title](relative_target.md) and resolves target paths."""
        links = []
        for match in cls.MARKDOWN_LINK_REGEX.finditer(content):
            link_title = match.group(1)
            target_href = match.group(2)
            
            # Resolve relative link target path against current file parent
            target_path_obj = (current_file.parent / target_href).resolve()
            
            resolved_rel_path = None
            try:
                resolved_rel_path = target_path_obj.relative_to(bundle_root.resolve()).as_posix()
            except ValueError:
                # Link points outside bundle root
                resolved_rel_path = target_href

            links.append(OKFLink(
                title=link_title,
                target_path=target_href,
                resolved_path=resolved_rel_path
            ))
        return links
