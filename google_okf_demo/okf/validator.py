"""
Open Knowledge Format (OKF) Validator
Validates OKF Bundles and Concepts against the OKF v0.1 specification rules.
"""

from typing import List
from .models import OKFBundle, OKFConcept, OKFValidationIssue


class OKFValidator:
    """Audit and validate an OKF bundle for schema correctness and graph integrity."""

    @classmethod
    def validate_bundle(cls, bundle: OKFBundle) -> List[OKFValidationIssue]:
        """Runs full suite of OKF specification checks on a bundle."""
        issues: List[OKFValidationIssue] = []

        # Check reserved files
        if not bundle.index_concept:
            issues.append(OKFValidationIssue(
                severity="WARNING",
                concept_path="bundle_root",
                message="Missing reserved 'index.md' in root directory. OKF recommends index.md for catalog browsing."
            ))

        if not bundle.log_concept:
            issues.append(OKFValidationIssue(
                severity="WARNING",
                concept_path="bundle_root",
                message="Missing reserved 'log.md' in root directory. OKF recommends log.md for change tracking."
            ))

        # Check each concept in the bundle
        for rel_path, concept in bundle.concepts.items():
            cls._validate_concept(concept, bundle, issues)

        return issues

    @classmethod
    def _validate_concept(cls, concept: OKFConcept, bundle: OKFBundle, issues: List[OKFValidationIssue]):
        """Validates individual concept against OKF frontmatter and link rules."""
        fm = concept.frontmatter

        # Rule 1: Mandatory field 'type' must be present and non-empty
        if not fm.type or fm.type == "unknown":
            issues.append(OKFValidationIssue(
                severity="ERROR",
                concept_path=concept.relative_path,
                message="Missing mandatory OKF field 'type' in frontmatter.",
                field_name="type"
            ))

        # Rule 2: Title and description recommended for non-reserved concepts
        if not concept.is_reserved:
            if not fm.title:
                issues.append(OKFValidationIssue(
                    severity="WARNING",
                    concept_path=concept.relative_path,
                    message="Missing optional but recommended field 'title'.",
                    field_name="title"
                ))
            if not fm.description:
                issues.append(OKFValidationIssue(
                    severity="WARNING",
                    concept_path=concept.relative_path,
                    message="Missing optional but recommended field 'description'.",
                    field_name="description"
                ))

        # Rule 3: Validate links (dangling reference detection)
        for link in concept.links:
            if link.resolved_path:
                if link.resolved_path not in bundle.concepts:
                    issues.append(OKFValidationIssue(
                        severity="ERROR",
                        concept_path=concept.relative_path,
                        message=f"Dangling link to '{link.target_path}' (resolved: '{link.resolved_path}'). Concept does not exist."
                    ))

        # Rule 4: Validate status field if specified
        valid_statuses = {"active", "draft", "deprecated"}
        if fm.status and fm.status.lower() not in valid_statuses:
            issues.append(OKFValidationIssue(
                severity="WARNING",
                concept_path=concept.relative_path,
                message=f"Unrecognized status '{fm.status}'. Expected one of {valid_statuses}.",
                field_name="status"
            ))
