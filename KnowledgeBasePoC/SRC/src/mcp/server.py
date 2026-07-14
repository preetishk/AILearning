"""MCP (Model Context Protocol) server — exposes knowledge base as MCP tools."""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

mcp_app = FastAPI(title="KB MCP Server", version="1.0.0")


class MCPToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]


MCP_TOOLS = [
    {
        "name": "kb_query",
        "description": "Query the knowledge base with a natural language question using hybrid graph + vector retrieval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Natural language question"},
                "retrieval_mode": {"type": "string", "enum": ["both", "graph", "vector"], "default": "both"},
                "top_k": {"type": "integer", "default": 10},
            },
            "required": ["question"],
        },
    },
    {
        "name": "kb_graph_query",
        "description": "Execute a graph traversal query (structural questions, call chains, impact analysis).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Canonical entity name"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["impact", "reverse_deps", "shortest_path", "neighbors"],
                    "default": "impact",
                },
                "depth": {"type": "integer", "default": 3},
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "kb_find_entity",
        "description": "Look up a specific entity by name and return its details, aliases, and relationships.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity canonical name or alias"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "kb_neighbors",
        "description": "Return the N-hop neighbourhood of an entity in the knowledge graph.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string"},
                "depth": {"type": "integer", "default": 2},
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "kb_impact_analysis",
        "description": "Find all entities affected downstream if a given entity changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string"},
                "max_depth": {"type": "integer", "default": 3},
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "kb_stats",
        "description": "Return knowledge base health statistics: node counts, vector doc counts, last ingest.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


@mcp_app.get("/tools")
async def list_tools():
    return {"tools": MCP_TOOLS}


@mcp_app.post("/tools/call")
async def call_tool(call: MCPToolCall):
    """Dispatch an MCP tool call."""
    try:
        if call.name == "kb_query":
            return await _kb_query(call.arguments)
        elif call.name == "kb_graph_query":
            return await _kb_graph_query(call.arguments)
        elif call.name == "kb_find_entity":
            return await _kb_find_entity(call.arguments)
        elif call.name == "kb_neighbors":
            return await _kb_neighbors(call.arguments)
        elif call.name == "kb_impact_analysis":
            return await _kb_impact(call.arguments)
        elif call.name == "kb_stats":
            return await _kb_stats()
        else:
            return {"error": f"Unknown tool: {call.name}"}
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return {"error": str(e)}


async def _kb_query(args: dict) -> dict:
    from src.agent.classifier import classify
    from src.agent.assembler import assemble
    from src.agent.vector_retriever import retrieve_vector
    from src.agent.graph_retriever import retrieve_graph
    from src.storage.protocols import get_graph_store, get_vector_store

    question = args.get("question", "")
    mode = args.get("retrieval_mode", "both")
    top_k = args.get("top_k", 10)

    intent = classify(question)
    graph_results = []
    vector_results = []

    if mode in ("both", "graph"):
        try:
            gs = get_graph_store()
            graph_results = retrieve_graph(intent, gs, top_k)
            gs.close()
        except Exception:
            pass

    if mode in ("both", "vector"):
        try:
            vs = get_vector_store()
            vector_results = retrieve_vector(question, vs, top_k)
        except Exception:
            pass

    result = assemble(question, graph_results, vector_results, None)
    return {
        "content": [{"type": "text", "text": result["answer"]}],
        "metadata": {
            "confidence": result["overall_confidence"],
            "grounded": result["answer_grounded"],
            "citations": result.get("citations", [])[:3],
        },
    }


async def _kb_graph_query(args: dict) -> dict:
    from src.storage.protocols import get_graph_store

    entity_name = args.get("entity_name", "")
    analysis_type = args.get("analysis_type", "impact")
    depth = args.get("depth", 3)

    try:
        gs = get_graph_store()
        if analysis_type == "impact":
            results = gs.find_impact(entity_name, depth)
        elif analysis_type == "reverse_deps":
            results = gs.find_reverse_deps(entity_name, depth)
        elif analysis_type == "neighbors":
            results = gs.get_entity_neighbors(entity_name, depth)
        else:
            results = gs.find_impact(entity_name, depth)
        gs.close()
        return {"content": [{"type": "text", "text": str(results)}], "results": results}
    except Exception as e:
        return {"error": str(e)}


async def _kb_find_entity(args: dict) -> dict:
    from src.storage.protocols import get_graph_store

    name = args.get("name", "")
    try:
        gs = get_graph_store()
        results = gs.query(
            "MATCH (n {canonical_name: $name}) RETURN n LIMIT 1",
            {"name": name},
        )
        if not results:
            # Try alias lookup
            results = gs.query(
                "MATCH (n) WHERE $name IN n.aliases RETURN n LIMIT 1",
                {"name": name},
            )
        gs.close()
        if results:
            node = dict(results[0].get("n", {}))
            return {"content": [{"type": "text", "text": str(node)}], "entity": node}
        return {"content": [{"type": "text", "text": f"Entity '{name}' not found."}]}
    except Exception as e:
        return {"error": str(e)}


async def _kb_neighbors(args: dict) -> dict:
    from src.storage.protocols import get_graph_store

    entity_name = args.get("entity_name", "")
    depth = args.get("depth", 2)
    try:
        gs = get_graph_store()
        results = gs.get_entity_neighbors(entity_name, depth)
        gs.close()
        return {"content": [{"type": "text", "text": str(results)}], "neighbors": results}
    except Exception as e:
        return {"error": str(e)}


async def _kb_impact(args: dict) -> dict:
    from src.storage.protocols import get_graph_store

    entity_name = args.get("entity_name", "")
    max_depth = args.get("max_depth", 3)
    try:
        gs = get_graph_store()
        results = gs.find_impact(entity_name, max_depth)
        gs.close()
        return {"content": [{"type": "text", "text": str(results)}], "impacted": results}
    except Exception as e:
        return {"error": str(e)}


async def _kb_stats() -> dict:
    from src.storage.protocols import get_graph_store, get_vector_store

    stats = {}
    try:
        gs = get_graph_store()
        stats["graph_nodes"] = gs.node_count()
        stats["graph_edges"] = gs.edge_count()
        gs.close()
    except Exception:
        pass
    try:
        vs = get_vector_store()
        stats["vector_docs"] = vs.total_count()
    except Exception:
        pass
    return {"content": [{"type": "text", "text": str(stats)}], "stats": stats}
