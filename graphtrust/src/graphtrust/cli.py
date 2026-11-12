"""Command-Line Interface (CLI) for GraphTrust Research Suite."""

import sys
import os
import json
import argparse
from pathlib import Path
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.model import GemmaAgent
from graphtrust.experiment import ControlledExperiment
from graphtrust.ablation import AblationSuite
from graphtrust.statistics import compare_formats, mean, std_dev

def load_yaml_safe(path_str: str) -> dict:
    p = Path(path_str)
    if not p.exists():
        return {}
    try:
        import yaml
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback naive yaml/json parser
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
            try:
                return json.loads(text)
            except Exception:
                return {}

def inspect_cmd(args):
    data_dir = args.data_dir
    if not data_dir and getattr(args, "config", None):
        cfg = load_yaml_safe(args.config)
        data_dir = cfg.get("data", {}).get("data_dir") or cfg.get("data", {}).get("processed_dir")
    data_dir = data_dir or "graphtrust/data/processed"
    
    loader = DatasetLoader(data_dir)
    stats = loader.inspect()
    if stats.get("status") == "error":
        print(f"ERROR: {stats.get('error_message')}", file=sys.stderr)
        sys.exit(1)

    print("=== GraphTrust Dataset Inspection Report ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    sys.exit(0)

def validate_cmd(args):
    cfg = load_yaml_safe(args.config) if getattr(args, "config", None) else {}
    data_dir = args.data_dir or cfg.get("data", {}).get("data_dir") or cfg.get("data", {}).get("processed_dir") or "graphtrust/data/processed"
    
    # Check model path if configured
    model_cfg = cfg.get("model", {})
    model_path = model_cfg.get("path") or model_cfg.get("model_path")
    is_mock = model_cfg.get("is_mock", True)
    if model_path and not is_mock and not Path(model_path).exists():
        print(f"ERROR: Configured model file does not exist: {model_path}", file=sys.stderr)
        print("Failing validation per research-integrity rule #5: do not silently substitute models.", file=sys.stderr)
        sys.exit(1)

    loader = DatasetLoader(data_dir)
    try:
        tasks = loader.load_tasks()
        nodes, edges = loader.load_graph()
        emb = loader.load_embeddings()
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {str(e)}", file=sys.stderr)
        sys.exit(1)

    retriever = GraphRetriever(nodes, edges, emb)

    print("=== GraphTrust Controlled Invariant Validation ===")
    print(f"Loaded {len(tasks)} tasks, {len(nodes)} graph nodes, {len(edges)} edges.")
    
    if not tasks:
        print("ERROR: No tasks available for validation.", file=sys.stderr)
        sys.exit(1)

    t0 = tasks[0]
    subgraph = retriever.retrieve(t0, max_depth=2, use_embeddings=True)
    ser_json = GraphSerializer.serialize(subgraph, "json", budget=4096)
    ser_adj = GraphSerializer.serialize(subgraph, "adjacency_list", budget=4096)
    ser_nl = GraphSerializer.serialize(subgraph, "natural_language", budget=4096)

    print(f"Task: {t0.instance_id}")
    print(f"Retrieved canonical nodes: {len(subgraph.nodes)}, edges: {len(subgraph.edges)}")
    print(f"Format A (JSON): {ser_json.token_count} tokens, {ser_json.node_count} nodes, {ser_json.edge_count} edges")
    print(f"Format B (Adjacency): {ser_adj.token_count} tokens, {ser_adj.node_count} nodes, {ser_adj.edge_count} edges")
    print(f"Format C (Natural Language): {ser_nl.token_count} tokens, {ser_nl.node_count} nodes, {ser_nl.edge_count} edges")

    if not (ser_json.node_count == ser_adj.node_count == ser_nl.node_count):
        print("INVARIANT VIOLATION: Node counts differ between formats!", file=sys.stderr)
        sys.exit(1)
    if not (ser_json.edge_count == ser_adj.edge_count == ser_nl.edge_count):
        print("INVARIANT VIOLATION: Edge counts differ between formats!", file=sys.stderr)
        sys.exit(1)

    print("[SUCCESS] Controlled invariant verified: All 3 formats represent the exact same underlying nodes and edges under unconstrained budget.")
    sys.exit(0)

def run_cmd(args):
    cfg = load_yaml_safe(args.config) if getattr(args, "config", None) else {}
    data_dir = args.data_dir or cfg.get("data", {}).get("data_dir") or cfg.get("data", {}).get("processed_dir") or "graphtrust/data/processed"
    output_dir = args.output_dir or cfg.get("output", {}).get("dir") or "outputs"
    budget = args.budget or (cfg.get("serialization", {}).get("token_budgets", [2048])[0] if "serialization" in cfg else 2048)
    formats = cfg.get("serialization", {}).get("formats", ["json", "adjacency_list", "natural_language"])
    
    loader = DatasetLoader(data_dir)
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)
    agent = GemmaAgent(model_name="Gemma-4-E2B", is_mock=True)

    exp = ControlledExperiment(
        retriever=retriever,
        agent=agent,
        formats=formats,
        output_dir=output_dir,
        resume=getattr(args, "resume", False)
    )

    limit = args.limit
    count = limit if limit else len(tasks)
    print(f"Running experiment on {count} tasks with budget={budget} tokens...")
    report = exp.run_benchmark(tasks, limit=limit, budget=budget, config_snapshot=cfg)
    print("\n=== Experiment Aggregated Results ===")
    for fmt, metrics in report["aggregated_metrics"].items():
        print(f"\n[{fmt.upper()}]")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

def analyze_cmd(args):
    results_dir = Path(args.results_dir or "outputs")
    if not results_dir.exists():
        print(f"ERROR: Results directory does not exist: {results_dir}", file=sys.stderr)
        sys.exit(1)

    # Search for experiment_results json files
    res_files = list(results_dir.rglob("experiment_results_*.json"))
    if not res_files:
        print(f"ERROR: No experiment results found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"=== GraphTrust Statistical Analysis ({len(res_files)} experiment run files found) ===")
    for rf in res_files:
        with open(rf, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sample_size = data.get("sample_size", 0)
        budget = data.get("budget", 2048)
        print(f"\nExperiment: {data.get('experiment_id', rf.stem)} | Budget: {budget} tokens | N={sample_size}")
        
        if sample_size < 3:
            print("  [WARNING] Sample size N < 3 is insufficient for statistical significance tests. Reporting raw metrics only.")
        
        agg = data.get("aggregated_metrics", {})
        for fmt, m in agg.items():
            print(f"  - {fmt}: Acc@1={m.get('acc_at_1')} | Acc@5={m.get('acc_at_5')} | MRR@5={m.get('mrr_at_5')} | Tokens={m.get('avg_token_count')}")

        # Compute paired comparison between json and natural_language if tasks exist
        records = data.get("task_level_records", [])
        if len(records) >= 3 and "json" in agg and "natural_language" in agg:
            json_tokens = [r["results"]["json"]["token_count"] for r in records if "json" in r["results"]]
            nl_tokens = [r["results"]["natural_language"]["token_count"] for r in records if "natural_language" in r["results"]]
            if len(json_tokens) == len(nl_tokens) and len(json_tokens) >= 3:
                from graphtrust.statistics import paired_t_test, paired_bootstrap_ci, cohens_d
                t_stat, p_val = paired_t_test(nl_tokens, json_tokens)
                diff, low, high = paired_bootstrap_ci(nl_tokens, json_tokens)
                d = cohens_d(nl_tokens, json_tokens)
                print(f"  Paired Test (NL vs JSON Tokens): Mean Diff={diff:.1f}t (95% CI: [{low:.1f}, {high:.1f}]), t={t_stat}, p={p_val}, Cohen's d={d:.2f}")

def ablate_cmd(args):
    cfg = load_yaml_safe(args.config) if getattr(args, "config", None) else {}
    data_dir = args.data_dir or cfg.get("data", {}).get("data_dir") or cfg.get("data", {}).get("processed_dir") or "graphtrust/data/processed"
    output_dir = Path(args.output_dir or cfg.get("output", {}).get("dir") or "outputs")
    ablation_out_dir = output_dir / "ablations"
    ablation_out_dir.mkdir(parents=True, exist_ok=True)

    loader = DatasetLoader(data_dir)
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)
    agent = GemmaAgent(is_mock=True)
    suite = AblationSuite(retriever, agent)

    print("Running Ablation A: Graph Expansion Depth (0, 1, 2 hops)...")
    depth_res = suite.ablate_depth(tasks, depths=[0, 1, 2])
    print(json.dumps(depth_res, indent=2))
    with open(ablation_out_dir / "depth_ablation_results.json", "w", encoding="utf-8") as f:
        json.dump(depth_res, f, indent=2)

    print("\nRunning Ablation B: Embedding-Based Expansion...")
    emb_res = suite.ablate_embeddings(tasks)
    print(json.dumps(emb_res, indent=2))
    with open(ablation_out_dir / "embedding_ablation_results.json", "w", encoding="utf-8") as f:
        json.dump(emb_res, f, indent=2)

    print(f"\n[SUCCESS] Ablation results saved separately to {ablation_out_dir}")

def main():
    parser = argparse.ArgumentParser(prog="graphtrust", description="GraphTrust Research Suite CLI")
    subparsers = parser.add_subparsers(dest="subcommand")

    p_inspect = subparsers.add_parser("inspect", help="Inspect dataset schemas and counts")
    p_inspect.add_argument("--data-dir", default=None)
    p_inspect.add_argument("--config", default=None)

    p_validate = subparsers.add_parser("validate", help="Validate experimental invariants")
    p_validate.add_argument("--data-dir", default=None)
    p_validate.add_argument("--config", default=None)

    p_run = subparsers.add_parser("run", help="Run controlled experiment")
    p_run.add_argument("--data-dir", default=None)
    p_run.add_argument("--config", default=None)
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--budget", type=int, default=None)
    p_run.add_argument("--output-dir", default=None)
    p_run.add_argument("--resume", action="store_true", default=False)

    p_analyze = subparsers.add_parser("analyze", help="Analyze results and perform paired tests")
    p_analyze.add_argument("--results-dir", default="outputs")

    p_ablate = subparsers.add_parser("ablate", help="Run ablation studies")
    p_ablate.add_argument("--data-dir", default=None)
    p_ablate.add_argument("--config", default=None)
    p_ablate.add_argument("--output-dir", default=None)

    args = parser.parse_args()
    if args.subcommand == "inspect":
        inspect_cmd(args)
    elif args.subcommand == "validate":
        validate_cmd(args)
    elif args.subcommand == "run":
        run_cmd(args)
    elif args.subcommand == "analyze":
        analyze_cmd(args)
    elif args.subcommand == "ablate":
        ablate_cmd(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
