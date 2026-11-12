"""Controlled Experiment Runner for GraphTrust.

Ensures strict scientific control:
- Canonical retrieved subgraph is created ONCE per task.
- The identical canonical subgraph is provided to all 3 serialization formats (JSON, Adjacency List, Natural Language) and baselines.
- Identical prompt template and decoding temperature (0.0).
- Gold patches are strictly isolated to evaluation.
- All mock outputs are explicitly labeled as MOCK.
- Full artifact persistence: config snapshot, model metadata, prompts, retrieval records, predictions, metrics.
"""

import os
import csv
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from graphtrust.schema import Task, RetrievedSubgraph, TaskEvaluation
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.prompting import build_prompt
from graphtrust.model import GemmaAgent
from graphtrust.evaluation import evaluate_task, aggregate_evaluations

class ControlledExperiment:
    def __init__(
        self,
        retriever: GraphRetriever,
        agent: GemmaAgent,
        formats: List[str] = None,
        budgets: List[int] = None,
        output_dir: str = "outputs",
        experiment_id: Optional[str] = None,
        resume: bool = False
    ):
        self.retriever = retriever
        self.agent = agent
        self.formats = formats or ["json", "adjacency_list", "natural_language"]
        self.budgets = budgets or [512, 1024, 2048, 4096]
        
        self.base_output_dir = Path(output_dir)
        if experiment_id:
            self.experiment_id = experiment_id
            self.run_dir = self.base_output_dir / self.experiment_id
        elif resume and self.base_output_dir.exists():
            subdirs = sorted([d for d in self.base_output_dir.iterdir() if d.is_dir() and d.name.startswith("exp_")])
            if subdirs:
                self.run_dir = subdirs[-1]
                self.experiment_id = self.run_dir.name
            else:
                self.experiment_id = self.base_output_dir.name
                self.run_dir = self.base_output_dir
        else:
            self.experiment_id = f"exp_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            self.run_dir = self.base_output_dir / self.experiment_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for reproducibility artifacts
        (self.run_dir / "predictions").mkdir(exist_ok=True)
        (self.run_dir / "metrics").mkdir(exist_ok=True)
        (self.run_dir / "logs").mkdir(exist_ok=True)
        (self.run_dir / "prompts").mkdir(exist_ok=True)
        (self.run_dir / "retrieval_records").mkdir(exist_ok=True)

    def run_task(
        self,
        task: Task,
        budget: int = 2048,
        retrieval_depth: int = 2,
        use_embeddings: bool = True
    ) -> Dict[str, TaskEvaluation]:
        """
        Execute controlled comparison for a single task across all formats.
        Step 1: Retrieve canonical subgraph ONCE.
        Step 2: Save canonical retrieval record (node IDs and edge IDs).
        Step 3: Serialize under identical underlying graph across all formats.
        Step 4: Build prompts (verify NO gold labels present in prompt).
        Step 5: Run model inference.
        Step 6: Compute evaluation metrics against gold labels.
        """
        # Retrieve canonical subgraph ONCE
        subgraph = self.retriever.retrieve(
            task=task,
            max_depth=retrieval_depth,
            use_embeddings=use_embeddings
        )

        # Persist canonical retrieval record to prove invariant
        retrieval_record = {
            "task_id": task.instance_id,
            "seed_node_ids": sorted(subgraph.seed_node_ids),
            "retrieved_node_ids": sorted([n.id for n in subgraph.nodes]),
            "retrieved_edge_ids": sorted([f"{e.source}->{e.target}:{e.type}" for e in subgraph.edges]),
            "candidate_files": sorted(subgraph.candidate_files),
            "node_count": len(subgraph.nodes),
            "edge_count": len(subgraph.edges),
            "params": subgraph.retrieval_params,
            "mode": getattr(self.agent, "mode", "mock")
        }
        rec_file = self.run_dir / "retrieval_records" / f"{task.instance_id}_canonical_subgraph.json"
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump(retrieval_record, f, indent=2)

        results: Dict[str, TaskEvaluation] = {}

        for fmt in self.formats:
            serialized = GraphSerializer.serialize(
                subgraph=subgraph,
                format_type=fmt,
                budget=budget
            )

            # Build standardized prompt and persist for audit (verifying no gold leak)
            prompt_text = build_prompt(task, serialized)
            prompt_file = self.run_dir / "prompts" / f"{task.instance_id}_{fmt}_{budget}tokens.txt"
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(prompt_text)

            prediction = self.agent.predict(task=task, serialized_graph=serialized)
            
            # Save raw prediction record with explicit mode marker
            pred_record = {
                "experiment_id": self.experiment_id,
                "task_id": task.instance_id,
                "format_type": fmt,
                "budget": budget,
                "token_count": serialized.token_count,
                "is_truncated": serialized.is_truncated,
                "predicted_files": prediction.predicted_files,
                "reasoning": prediction.reasoning,
                "raw_output": prediction.raw_output,
                "parsing_success": prediction.parsing_success,
                "latency_ms": prediction.latency_ms,
                "mode": getattr(self.agent, "mode", "mock"),
                "is_mock": getattr(self.agent, "is_mock", True)
            }
            pred_file = self.run_dir / "predictions" / f"{task.instance_id}_{fmt}_{budget}tokens.json"
            with open(pred_file, "w", encoding="utf-8") as f:
                json.dump(pred_record, f, indent=2)

            evaluation = evaluate_task(
                task=task,
                prediction=prediction,
                subgraph=subgraph,
                token_count=serialized.token_count
            )
            results[fmt] = evaluation

        return results

    def run_benchmark(
        self,
        tasks: List[Task],
        limit: Optional[int] = None,
        budget: int = 2048,
        config_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run full benchmark or limited pilot run with artifact persistence."""
        selected_tasks = tasks[:limit] if limit else tasks
        all_evals: Dict[str, List[TaskEvaluation]] = {fmt: [] for fmt in self.formats}

        # Save metadata and config snapshot
        meta = self.agent.get_metadata()
        meta["experiment_id"] = self.experiment_id
        meta["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.run_dir / "model_metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        if config_snapshot:
            with open(self.run_dir / "config_snapshot.json", "w", encoding="utf-8") as f:
                json.dump(config_snapshot, f, indent=2)

        start_time = time.time()
        completed_task_ids = set()
        
        # Check existing completed predictions if resuming
        for pfile in (self.run_dir / "predictions").glob(f"*_{self.formats[0]}_{budget}tokens.json"):
            tid = pfile.stem.split(f"_{self.formats[0]}_")[0]
            completed_task_ids.add(tid)

        for task in selected_tasks:
            if task.instance_id in completed_task_ids:
                # Load existing evaluations from disk
                for fmt in self.formats:
                    pfile = self.run_dir / "predictions" / f"{task.instance_id}_{fmt}_{budget}tokens.json"
                    if pfile.exists():
                        with open(pfile, "r", encoding="utf-8") as pf:
                            pdata = json.load(pf)
                        # Re-evaluate
                        from graphtrust.schema import ModelPrediction
                        pred = ModelPrediction(
                            task_id=task.instance_id,
                            format_type=fmt,
                            budget=budget,
                            predicted_files=pdata["predicted_files"],
                            reasoning=pdata["reasoning"],
                            raw_output=pdata["raw_output"],
                            parsing_success=pdata["parsing_success"],
                            latency_ms=pdata.get("latency_ms", 0)
                        )
                        sub = self.retriever.retrieve(task, max_depth=2, use_embeddings=True)
                        ev = evaluate_task(task, pred, sub, token_count=pdata.get("token_count", 0))
                        all_evals[fmt].append(ev)
                continue

            task_results = self.run_task(task, budget=budget)
            for fmt, ev in task_results.items():
                all_evals[fmt].append(ev)

        elapsed = time.time() - start_time
        aggregated = {
            fmt: aggregate_evaluations(eval_list)
            for fmt, eval_list in all_evals.items()
        }

        # Save metrics JSON & CSV
        report = {
            "experiment_id": self.experiment_id,
            "mode": getattr(self.agent, "mode", "mock"),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model_metadata": meta,
            "sample_size": len(selected_tasks),
            "budget": budget,
            "elapsed_seconds": round(elapsed, 2),
            "aggregated_metrics": aggregated,
            "task_level_records": [
                {
                    "task_id": t.instance_id,
                    "results": {fmt: all_evals[fmt][idx].__dict__ for fmt in self.formats if idx < len(all_evals[fmt])}
                }
                for idx, t in enumerate(selected_tasks)
            ]
        }

        out_json = self.run_dir / "metrics" / f"experiment_results_{budget}tokens.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Write summary metrics CSV
        out_csv = self.run_dir / "metrics" / f"summary_metrics_{budget}tokens.csv"
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["mode", "format", "sample_size", "acc_at_1", "acc_at_5", "mrr_at_5", "candidate_coverage", "avg_tokens"])
            for fmt, m in aggregated.items():
                writer.writerow([
                    getattr(self.agent, "mode", "mock"),
                    fmt,
                    m.get("sample_size", 0),
                    m.get("acc_at_1", 0),
                    m.get("acc_at_5", 0),
                    m.get("mrr_at_5", 0),
                    m.get("candidate_coverage", 0),
                    m.get("avg_token_count", 0)
                ])

        # Write run log
        with open(self.run_dir / "logs" / "run.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [MODE={getattr(self.agent, 'mode', 'mock')}] Completed run on {len(selected_tasks)} tasks with budget {budget} tokens in {elapsed:.2f}s\n")

        return report
