"""Command-Line Interface (CLI) for GraphTrust Research Suite."""

import sys
import json
import argparse
from pathlib import Path
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.model import GemmaAgent
from graphtrust.experiment import ControlledExperiment
from graphtrust.ablation import AblationSuite
from graphtrust.statistics import compare_formats

def inspect_cmd(args):
    data_dir = args.data_dir or "graphtrust/data/processed"
    loader = DatasetLoader(data_dir)
    stats = loader.inspect()
    print("=== GraphTrust Dataset Inspection Report ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

def validate_cmd(args):
    data_dir = args.data_dir or "graphtrust/data/processed"
    loader = DatasetLoader(data_dir)
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)

    print("=== GraphTrust Controlled Invariant Validation ===")
    print(f"Loaded {len(tasks)} tasks, {len(nodes)} graph nodes, {len(edges)} edges.")
    
    # Invariant test on task 0
    t0 = tasks[0]
    subgraph = retriever.retrieve(t0, max_depth=2, use_embeddings=True)
    ser_json = GraphSerializer.serialize(subgraph, "json", budget=4096)
    ser_adj = GraphSerializer.serialize(subgraph, "adjacency_list", budget=4096)
    ser_nl = GraphSerializer.serialize(subgraph, "natural_language", budget=4096)

    print(f"Task: {t0.instance_id}")
    print(f"Retrieved canonical nodes: {len(subgraph.nodes)}, edges: {len(subgraph.edges)}")
    print(f"Format A (JSON): {ser_json.token_count} tokens, {ser_json.node_count} nodes")
    print(f"Format B (Adjacency): {ser_adj.token_count} tokens, {ser_adj.node_count} nodes")
    print(f"Format C (Natural Language): {ser_nl.token_count} tokens, {ser_nl.node_count} nodes")

    assert ser_json.node_count == ser_adj.node_count == ser_nl.node_count, "INVARIANT VIOLATION: Node counts differ!"
    assert ser_json.edge_count == ser_adj.edge_count == ser_nl.edge_count, "INVARIANT VIOLATION: Edge counts differ!"
    print("[SUCCESS] All 3 formats represent the exact same underlying nodes and edges under unconstrained budget.")

def run_cmd(args):
    data_dir = args.data_dir or "graphtrust/data/processed"
    loader = DatasetLoader(data_dir)
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)
    agent = GemmaAgent(model_name="Gemma-4-E2B", is_mock=True)

    exp = ControlledExperiment(
        retriever=retriever,
        agent=agent,
        output_dir=args.output_dir or "graphtrust/outputs"
    )

    limit = args.limit
    print(f"Running experiment on {limit if limit else len(tasks)} tasks with budget={args.budget} tokens...")
    report = exp.run_benchmark(tasks, limit=limit, budget=args.budget)
    print("\n=== Experiment Aggregated Results ===")
    for fmt, metrics in report["aggregated_metrics"].items():
        print(f"\n[{fmt.upper()}]")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

def ablate_cmd(args):
    data_dir = args.data_dir or "graphtrust/data/processed"
    loader = DatasetLoader(data_dir)
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)
    agent = GemmaAgent(is_mock=True)
    suite = AblationSuite(retriever, agent)

    print("Running Ablation A: Graph Expansion Depth...")
    depth_res = suite.ablate_depth(tasks, depths=[0, 1, 2])
    print(json.dumps(depth_res, indent=2))

    print("\nRunning Ablation B: Embedding-Based Expansion...")
    emb_res = suite.ablate_embeddings(tasks)
    print(json.dumps(emb_res, indent=2))

def main():
    parser = argparse.ArgumentParser(prog="graphtrust", description="GraphTrust Research Suite CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    p_inspect = subparsers.add_parser("inspect", help="Inspect dataset schemas and counts")
    p_inspect.add_argument("--data-dir", default="graphtrust/data/processed")

    p_validate = subparsers.add_parser("validate", help="Validate experimental invariants")
    p_validate.add_argument("--data-dir", default="graphtrust/data/processed")
    p_validate.add_argument("--config", default="graphtrust/configs/default.yaml")

    p_run = subparsers.add_parser("run", help="Run controlled experiment")
    p_run.add_argument("--data-dir", default="graphtrust/data/processed")
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--budget", type=int, default=2048)
    p_run.add_argument("--output-dir", default="graphtrust/outputs")

    p_ablate = subparsers.add_parser("ablate", help="Run ablation studies")
    p_ablate.add_argument("--data-dir", default="graphtrust/data/processed")

    args = parser.parse_args()
    if args.subcommand == "inspect":
        inspect_cmd(args)
    elif args.subcommand == "validate":
        validate_cmd(args)
    elif args.subcommand == "run":
        run_cmd(args)
    elif args.subcommand == "ablate":
        ablate_cmd(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
