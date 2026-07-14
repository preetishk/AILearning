"""Entity browser routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    EntityListResponse, EntityDetailResponse, EntityRow, RelationshipItem,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=EntityListResponse)
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    kind: str = Query(None),
    source_type: str = Query(None),
    search: str = Query(None),
):
    """Return paginated list of entities from the graph DB."""
    try:
        from src.storage.protocols import get_graph_store
        graph_store = get_graph_store()

        entities = graph_store.list_entities(
            skip=skip,
            limit=limit,
            kind_filter=kind,
            source_type_filter=source_type,
        )
        graph_store.close()

        rows = []
        for e in entities:
            name = e.get("canonical_name", "")
            if search and search.lower() not in name.lower():
                continue
            rows.append(EntityRow(
                id=e.get("id", ""),
                canonical_name=name,
                kind=e.get("kind", ""),
                source_ref=e.get("source_ref", ""),
                source_type=e.get("source_type", ""),
                confidence=e.get("confidence", "high"),
                summary=e.get("summary"),
                aliases=e.get("aliases") or [],
            ))

        return EntityListResponse(
            entities=rows,
            total=len(rows),
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.warning(f"Entity list failed: {e}")
        return EntityListResponse(entities=[], total=0, skip=skip, limit=limit)


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(entity_id: str):
    """Get entity detail including relationships."""
    try:
        from src.storage.protocols import get_graph_store
        graph_store = get_graph_store()

        node = graph_store.get_entity_by_id(entity_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        relationships_raw = graph_store.get_entity_relationships(entity_id)
        graph_store.close()

        relationships = [
            RelationshipItem(
                rel_type=r.get("rel_type", ""),
                target=r.get("target", ""),
                target_kind=r.get("target_kind", ""),
                direction=r.get("direction", "outbound"),
            )
            for r in relationships_raw
        ]

        return EntityDetailResponse(
            id=entity_id,
            canonical_name=node.get("canonical_name", ""),
            kind=node.get("kind", ""),
            source_ref=node.get("source_ref", ""),
            source_line_start=node.get("source_line_start"),
            source_line_end=node.get("source_line_end"),
            source_type=node.get("source_type", ""),
            confidence=node.get("confidence", "high"),
            summary=node.get("summary"),
            aliases=node.get("aliases") or [],
            relationships=relationships,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{entity_id}/summarize")
async def regenerate_summary(entity_id: str):
    """Regenerate the LLM summary for a single entity."""
    try:
        from src.storage.protocols import get_graph_store
        from openai import OpenAI
        import os

        graph_store = get_graph_store()
        node = graph_store.get_entity_by_id(entity_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o")

        name = node.get("canonical_name", entity_id)
        kind = node.get("kind", "entity")
        source_ref = node.get("source_ref", "")

        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": (
                    f"Write a one-paragraph summary of the {kind} named '{name}' "
                    f"from source file '{source_ref}'. Be factual and concise."
                ),
            }],
        )
        summary = response.choices[0].message.content.strip()
        graph_store.upsert_node("Entity", entity_id, {"summary": summary})
        graph_store.close()

        return {"entity_id": entity_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
