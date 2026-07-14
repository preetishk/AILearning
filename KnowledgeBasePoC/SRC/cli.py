"""CLI entry point — kb command."""
from __future__ import annotations

import os
import sys

import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def main():
    """Hybrid Knowledge Base CLI."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="API server host")
@click.option("--port", default=8000, help="API server port")
@click.option("--reload", is_flag=True, default=False, help="Enable hot reload")
def serve(host, port, reload):
    """Start the Knowledge Base REST API server."""
    import uvicorn
    click.echo(f"Starting API server at http://{host}:{port}/docs")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@main.command()
@click.option("--port", default=3000, help="MCP server port")
def mcp(port):
    """Start the MCP server for VS Code Copilot integration."""
    import uvicorn
    click.echo(f"Starting MCP server at http://0.0.0.0:{port}/tools")
    uvicorn.run(
        "src.mcp.server:mcp_app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


@main.command()
@click.option("--input-dir", default="./input", help="Input directory with extracted JSON")
@click.option("--output-dir", default="./output", help="Output directory for registry")
@click.option("--threshold", default=0.92, help="Similarity threshold for entity resolution")
def resolve(input_dir, output_dir, threshold):
    """Run entity resolution on extracted JSON files."""
    from src.pipeline.resolver import resolve_entities
    click.echo(f"Resolving entities in {input_dir} …")
    registry = resolve_entities(input_dir, output_dir, threshold)
    click.echo(f"Done. {len(registry.entries)} canonical entities in registry.")


@main.command()
@click.option("--input-dir", default="./input", help="Input directory with extracted JSON")
@click.option("--output-dir", default="./output", help="Output directory for graph triples")
def hydrate(input_dir, output_dir):
    """Hydrate extracted facts into graph triples."""
    import json
    from pathlib import Path
    from src.pipeline.extractor import extract_layer1 as _l1
    from src.pipeline.hydrator import hydrate as _hydrate
    from src.models.facts import EntityRegistry

    click.echo(f"Hydrating from {input_dir} …")
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    registry_file = output_path / "entity_registry.json"
    registry = EntityRegistry()
    if registry_file.exists():
        registry = EntityRegistry.model_validate_json(registry_file.read_text())

    # Load facts
    layers: dict = {1: [], 2: [], 3: [], 4: [], 5: []}
    from src.models.facts import EntityFact, RuleFact, ContractFact, OperationalFact

    for file, layer_cls, layer_num in [
        ("structural.json", EntityFact, 1),
        ("behavioral.json", RuleFact, 2),
        ("contracts.json", ContractFact, 3),
        ("operational.json", OperationalFact, 4),
    ]:
        fp = input_path / file
        if fp.exists():
            data = json.loads(fp.read_text())
            layers[layer_num] = [layer_cls(**item) for item in data]

    triple = _hydrate(layers, registry)
    out_file = output_path / "graph_triples.json"
    out_file.write_text(triple.model_dump_json(indent=2))
    click.echo(f"Hydrated: {len(triple.nodes)} nodes, {len(triple.edges)} edges → {out_file}")


@main.command()
@click.option("--input-dir", default="./output", help="Directory with graph_triples.json")
@click.option("--graph", default="neo4j", help="Graph backend: neo4j | kuzu")
def import_graph(input_dir, graph):
    """Import graph triples into the graph database."""
    import json
    from pathlib import Path
    from src.models.facts import GraphTriple
    from src.pipeline.hydrator import write_to_graph
    from src.storage.protocols import get_graph_store

    triples_file = Path(input_dir) / "graph_triples.json"
    if not triples_file.exists():
        click.echo(f"Error: {triples_file} not found. Run 'kb hydrate' first.")
        return

    triple = GraphTriple.model_validate_json(triples_file.read_text())
    click.echo(f"Importing {len(triple.nodes)} nodes, {len(triple.edges)} edges to {graph} …")

    os.environ["GRAPH_BACKEND"] = graph
    graph_store = get_graph_store()
    stats = write_to_graph(triple, graph_store)
    graph_store.close()
    click.echo(f"Done. {stats['nodes_written']} nodes, {stats['edges_written']} edges written.")


@main.command()
@click.argument("question")
@click.option("--top-k", default=10, help="Number of results")
@click.option("--mode", default="both", help="Retrieval mode: both|graph|vector")
def query(question, top_k, mode):
    """Run a query against the knowledge base."""
    from src.agent.classifier import classify
    from src.agent.assembler import assemble
    from src.storage.protocols import get_graph_store, get_vector_store

    click.echo(f"\nQuestion: {question}\n")

    intent = classify(question)
    click.echo(f"Intent: {intent.question_type} | entities: {intent.primary_entities}")

    graph_results = []
    vector_results = []

    if mode in ("both", "graph"):
        try:
            from src.agent.graph_retriever import retrieve_graph
            gs = get_graph_store()
            graph_results = retrieve_graph(intent, gs, top_k)
            gs.close()
        except Exception as e:
            click.echo(f"Graph retrieval failed: {e}")

    if mode in ("both", "vector"):
        try:
            from src.agent.vector_retriever import retrieve_vector
            vs = get_vector_store()
            vector_results = retrieve_vector(question, vs, top_k)
        except Exception as e:
            click.echo(f"Vector retrieval failed: {e}")

    result = assemble(question, graph_results, vector_results, None)
    click.echo(f"\nAnswer:\n{result['answer']}")
    click.echo(f"\nConfidence: {result['overall_confidence']:.2f} | Grounded: {result['answer_grounded']}")
    click.echo(f"Lanes: {', '.join(result['retrieval_lanes_used'])}")
    if result.get("citations"):
        click.echo(f"\nCitations ({len(result['citations'])}):")
        for c in result["citations"][:3]:
            click.echo(f"  • {c.get('source_ref', '')} (score={c.get('relevance_score', 0):.2f})")


@main.command()
def schema():
    """Run one-time Neo4j schema setup."""
    import subprocess
    subprocess.run([sys.executable, "scripts/create_schema.py"])


if __name__ == "__main__":
    main()
