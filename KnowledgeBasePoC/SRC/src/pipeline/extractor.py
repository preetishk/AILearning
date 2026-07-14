"""LLM extraction — runs 5-layer extraction prompts on chunks."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from src.models.facts import (
    Chunk, EntityFact, RuleFact, ContractFact, OperationalFact,
    EvidenceFact, Evidence, make_node_id,
)

logger = logging.getLogger(__name__)

VECTOR_COLLECTIONS = [
    "BehavioralRule", "EntityContract", "OutcomeRecord",
    "ObservableEvent", "OperationalTrace", "DocumentSection"
]


def _get_llm_client():
    """Return OpenAI client configured from env."""
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _llm_extract(system_prompt: str, user_prompt: str, model: str = None) -> Any:
    """Call the LLM and return parsed JSON. Returns empty list on error."""
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    try:
        client = _get_llm_client()
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        # The LLM might return {"results": [...]} or directly [...]
        if isinstance(parsed, list):
            return parsed
        for key in ("results", "entities", "facts", "rules", "contracts", "operations"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        return parsed
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}")
        return []


# ── Layer 1: Structural ──────────────────────────────────────────────────────

LAYER1_SYSTEM = (
    "You are a code structure extractor. Output only valid JSON. No prose. "
    'Return a JSON object with key "results" containing an array of entity objects.'
)

LAYER1_USER = """Extract ALL entities and their relationships from the following {language} code chunk.

For each entity (class, method, interface, enum, property, constant), output:
{{
  "id": "<SHA-256[:16] of fully qualified name>",
  "canonical_name": "<fully qualified name — namespace.class.method>",
  "aliases": [],
  "kind": "<class|method|interface|enum|property|constant|function|module>",
  "source_type": "code",
  "source_ref": "{source_ref}",
  "source_line_start": {start_line},
  "source_line_end": {end_line},
  "tags": [],
  "relations": [{{"type": "<calls|implements|inherits|references|depends_on|part_of|emits|produces>", "target": "<target name>"}}],
  "confidence": "high"
}}

Rules:
- Temperature: 0.0 — extract only what is explicitly present.
- Do NOT create entities for primitive types.
- Output: a JSON object with key "results" containing entity objects array.

Source file: {source_ref}
Lines: {start_line}–{end_line}
Language: {language}

```{language}
{content}
```"""


def extract_layer1(chunks: list[Chunk]) -> list[EntityFact]:
    facts: list[EntityFact] = []
    for chunk in chunks:
        raw = _llm_extract(
            LAYER1_SYSTEM,
            LAYER1_USER.format(
                language=chunk.language,
                source_ref=chunk.source_ref,
                start_line=chunk.source_line_start,
                end_line=chunk.source_line_end,
                content=chunk.content[:6000],
            ),
        )
        for item in (raw if isinstance(raw, list) else []):
            try:
                item.setdefault("id", make_node_id(item.get("canonical_name", "")))
                item.setdefault("source_ref", chunk.source_ref)
                facts.append(EntityFact(**item))
            except Exception as e:
                logger.debug(f"Layer 1 parse error: {e} — {item}")
    return facts


# ── Layer 2: Behavioral ──────────────────────────────────────────────────────

LAYER2_SYSTEM = (
    "You are a behavioral rule extractor. Output only valid JSON. No prose. "
    'Return a JSON object with key "results" containing an array of rule objects.'
)

LAYER2_USER = """Extract ALL decision rules from the following {language} code chunk.

For each decision point output:
{{
  "id": "<SHA-256[:16] of owner_entity + condition>",
  "owner_entity": "<fully qualified name>",
  "condition": "<verbatim condition>",
  "true_path": "<what happens — 1 sentence>",
  "false_path": "<what happens — 1 sentence>",
  "linked_outcome": "<outcome code or null>",
  "linked_resolution": "<fix action or null>",
  "source_ref": "{source_ref}",
  "source_line": {start_line},
  "source_type": "code",
  "confidence": "high"
}}

Rules: Only extract decisions that affect program flow. Output JSON object with key "results".

Source file: {source_ref}

```{language}
{content}
```"""


def extract_layer2(chunks: list[Chunk]) -> list[RuleFact]:
    facts: list[RuleFact] = []
    for chunk in chunks:
        raw = _llm_extract(
            LAYER2_SYSTEM,
            LAYER2_USER.format(
                language=chunk.language,
                source_ref=chunk.source_ref,
                start_line=chunk.source_line_start,
                content=chunk.content[:6000],
            ),
        )
        for item in (raw if isinstance(raw, list) else []):
            try:
                item.setdefault("source_ref", chunk.source_ref)
                item.setdefault("id", make_node_id(
                    item.get("owner_entity", "") + item.get("condition", "")
                ))
                facts.append(RuleFact(**item))
            except Exception as e:
                logger.debug(f"Layer 2 parse error: {e}")
    return facts


# ── Layer 3: Contracts ───────────────────────────────────────────────────────

LAYER3_SYSTEM = (
    "You are an API contract extractor. Output only valid JSON. No prose. "
    'Return a JSON object with key "results" containing an array of contract objects.'
)

LAYER3_USER = """Extract ALL API contracts and outcome codes from:

For each public method or schema output:
{{
  "id": "<SHA-256[:16] of entity_name>",
  "entity_name": "<fully qualified name>",
  "summary": "<doc comment or null>",
  "inputs": [{{"name": "", "type": "", "nullable": false}}],
  "outputs": [{{"name": "", "type": "", "nullable": false}}],
  "outcome_codes": [{{"value_name": "", "meaning": "", "recoverable": true, "severity": "info"}}],
  "source_ref": "{source_ref}",
  "source_line": {start_line},
  "source_type": "code"
}}

Output JSON object with key "results".

Source file: {source_ref}

```{language}
{content}
```"""


def extract_layer3(chunks: list[Chunk]) -> list[ContractFact]:
    facts: list[ContractFact] = []
    for chunk in chunks:
        raw = _llm_extract(
            LAYER3_SYSTEM,
            LAYER3_USER.format(
                language=chunk.language,
                source_ref=chunk.source_ref,
                start_line=chunk.source_line_start,
                content=chunk.content[:6000],
            ),
        )
        for item in (raw if isinstance(raw, list) else []):
            try:
                item.setdefault("source_ref", chunk.source_ref)
                item.setdefault("id", make_node_id(item.get("entity_name", "")))
                facts.append(ContractFact(**item))
            except Exception as e:
                logger.debug(f"Layer 3 parse error: {e}")
    return facts


# ── Layer 4: Operational ─────────────────────────────────────────────────────

LAYER4_SYSTEM = (
    "You are a test and operational trace extractor. Output only valid JSON. No prose. "
    'Return a JSON object with key "results" containing an array of operational objects.'
)

LAYER4_USER = """Extract ALL test scenarios and runbook steps from:

For each test method output:
{{
  "id": "<SHA-256[:16] of trace_name>",
  "trace_name": "<method name>",
  "scenario": "<what is tested — 1 sentence>",
  "action": "<what is called>",
  "assertions": [{{"what": "", "expected": "", "check_method": ""}}],
  "context_overrides": [],
  "implied_behavior": "<what this test proves — 1 sentence>",
  "covers_failure_path": false,
  "source_ref": "{source_ref}",
  "source_line": {start_line},
  "source_type": "code"
}}

Output JSON object with key "results".

Source file: {source_ref}

```{language}
{content}
```"""


def extract_layer4(chunks: list[Chunk]) -> list[OperationalFact]:
    facts: list[OperationalFact] = []
    for chunk in chunks:
        raw = _llm_extract(
            LAYER4_SYSTEM,
            LAYER4_USER.format(
                language=chunk.language,
                source_ref=chunk.source_ref,
                start_line=chunk.source_line_start,
                content=chunk.content[:6000],
            ),
        )
        for item in (raw if isinstance(raw, list) else []):
            try:
                item.setdefault("source_ref", chunk.source_ref)
                item.setdefault("id", make_node_id(item.get("trace_name", "")))
                facts.append(OperationalFact(**item))
            except Exception as e:
                logger.debug(f"Layer 4 parse error: {e}")
    return facts


# ── Layer 5: Evidence enrichment ─────────────────────────────────────────────

def extract_layer5(facts: list[dict], file_content: str) -> list[EvidenceFact]:
    """Add provenance metadata to extracted facts."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    evidence_facts = []
    for fact in facts:
        fact_id = fact.get("id", "")
        source_line = fact.get("source_line", fact.get("source_line_start", 0)) or 0
        evidence_facts.append(EvidenceFact(
            fact_id=fact_id,
            evidence=Evidence(
                fact_id=fact_id,
                source_file=fact.get("source_ref", ""),
                source_line_start=source_line,
                source_line_end=source_line + 5,
                source_snippet="",  # will be enriched if LLM is available
                confidence=fact.get("confidence", "high"),
                extraction_date=today,
            ),
        ))
    return evidence_facts


# ── Route fact to vector collection ──────────────────────────────────────────

def route_to_collection(fact: dict) -> str:
    """Map a fact dict to the appropriate vector DB collection name."""
    kind = fact.get("_fact_kind") or fact.get("fact_kind", "")
    if kind == "rule":
        outcome = fact.get("linked_outcome")
        if outcome:
            return "OutcomeRecord"
        return "BehavioralRule"
    if kind == "contract":
        outcomes = fact.get("outcome_codes", [])
        if outcomes:
            return "OutcomeRecord"
        return "EntityContract"
    if kind == "operational":
        return "OperationalTrace"
    if kind == "document":
        return "DocumentSection"
    return "DocumentSection"


# ── Sentence template ─────────────────────────────────────────────────────────

def fact_to_sentence(fact: dict) -> str:
    """Convert a structured fact dict to a plain-text sentence for embedding."""
    kind = fact.get("_fact_kind") or fact.get("fact_kind", "")

    if kind == "entity":
        name = fact.get("canonical_name", "")
        fkind = fact.get("kind", "entity")
        src = fact.get("source_ref", "")
        summary = fact.get("summary", "")
        relations = fact.get("relations", [])
        rel_text = ""
        if relations:
            rel_text = " Relationships: " + "; ".join(
                f"{r.get('type', '')} {r.get('target', '')}" for r in relations[:5]
            )
        return f"{fkind} {name} defined in {src}. {summary}{rel_text}".strip()

    if kind == "rule":
        owner = fact.get("owner_entity", "")
        cond = fact.get("condition", "")
        true_path = fact.get("true_path", "")
        false_path = fact.get("false_path", "")
        outcome = fact.get("linked_outcome", "")
        text = f"Decision rule in {owner}: when {cond}, then {true_path}"
        if false_path:
            text += f", otherwise {false_path}"
        if outcome:
            text += f". Outcome: {outcome}"
        return text

    if kind == "contract":
        name = fact.get("entity_name", "")
        summary = fact.get("summary", "")
        inputs = fact.get("inputs", [])
        outputs = fact.get("outputs", [])
        outcomes = fact.get("outcome_codes", [])
        inp_text = ", ".join(f"{p.get('name')}:{p.get('type')}" for p in inputs[:5])
        out_text = ", ".join(f"{p.get('name')}:{p.get('type')}" for p in outputs[:3])
        outcome_text = ", ".join(o.get("value_name", "") for o in outcomes[:5])
        return (
            f"API contract for {name}. {summary} "
            f"Inputs: {inp_text}. Outputs: {out_text}. Outcomes: {outcome_text}."
        ).strip()

    if kind == "operational":
        name = fact.get("trace_name", "")
        scenario = fact.get("scenario", "")
        action = fact.get("action", "")
        implied = fact.get("implied_behavior", "")
        return f"Test {name}: {scenario}. Action: {action}. Proves: {implied}"

    return fact.get("content", fact.get("summary", str(fact)))


def build_vector_text(fact: dict, aliases: list[str] = None) -> str:
    """Build the text to embed — base sentence + alias injection."""
    base = fact_to_sentence(fact)
    if aliases:
        alias_str = ", ".join(aliases[:10])
        base += f" (also known as: {alias_str})"
    return base


# ── Main extraction entry point ───────────────────────────────────────────────

def extract_all_layers(chunks: list[Chunk]) -> dict[int, list]:
    """
    Run all 5 extraction layers on the provided chunks.
    Returns dict: {1: [EntityFact], 2: [RuleFact], 3: [ContractFact], 4: [OperationalFact], 5: [EvidenceFact]}
    """
    logger.info(f"Extracting from {len(chunks)} chunks …")

    layer1 = extract_layer1(chunks)
    logger.info(f"  Layer 1 (structural): {len(layer1)} facts")

    layer2 = extract_layer2(chunks)
    logger.info(f"  Layer 2 (behavioral): {len(layer2)} facts")

    layer3 = extract_layer3(chunks)
    logger.info(f"  Layer 3 (contracts): {len(layer3)} facts")

    layer4 = extract_layer4(chunks)
    logger.info(f"  Layer 4 (operational): {len(layer4)} facts")

    all_facts = (
        [f.model_dump() for f in layer1]
        + [f.model_dump() for f in layer2]
        + [f.model_dump() for f in layer3]
        + [f.model_dump() for f in layer4]
    )
    layer5 = extract_layer5(all_facts, "")
    logger.info(f"  Layer 5 (evidence): {len(layer5)} facts")

    return {1: layer1, 2: layer2, 3: layer3, 4: layer4, 5: layer5}
