"""Controlled Experiment Runner for GraphTrust.

Ensures strict scientific control:
- Canonical retrieved subgraph is created ONCE per task.
- The identical canonical subgraph is provided to all 3 serialization formats (JSON, Adjacency List, Natural Language).
- Identical prompt template and decoding temperature (0.0).
- Gold patches are strictly isolated to evaluation.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from graphtrust.schema import Task, RetrievedSubgraph, TaskEvaluation
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.model import GemmaAgent
from graphtrust.evaluation import evaluate_task, aggregate_evaluations

class ControlledExperiment:
    def __init__(
        self,
        retriever: GraphRetriever,
        agent: GemmaAgent,
        formats: List[str] = None,
        budgets: List[int] = None,
        output_dir: str = "outputs"
    ):
        self.retriever = retriever
        self.agent = agent
        self.formats = formats or ["json", "adjacency_list", "natural_language"]
        self.budgets = budgets or [512, 1024, 2048, 4096]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        Step 2: Serialize under identical underlying graph across all formats.
        Step 3: Run model inference with temperature=0.
        Step 4: Compute evaluation metrics against gold labels.
        """
        # Retrieve canonical subgraph ONCE
        subgraph = self.retriever.retrieve(
            task=task,
            max_depth=retrieval_depth,
            use_embeddings=use_embeddings
        )

        results: Dict[str, TaskEvaluation] = {}

        for fmt in self.formats:
            serialized = GraphSerializer.serialize(
                subgraph=subgraph,
                format_type=fmt,
                budget=budget
            )

            prediction = self.agent.predict(task=task, serialized_graph=serialized)
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
        budget: int = 2048
    ) -> Dict[str, Any]:
        """Run full benchmark or limited pilot run."""
        selected_tasks = tasks[:limit] if limit else tasks
        all_evals: Dict[str, List[TaskEvaluation]] = {fmt: [] for fmt in self.formats}

        start_time = time.time()
        for task in selected_tasks:
            task_results = self.run_task(task, budget=budget)
            for fmt, ev in task_results.items():
                all_evals[fmt].append(ev)

        elapsed = time.time() - start_time
        aggregated = {
            fmt: aggregate_evaluations(eval_list)
            for fmt, eval_list in all_evals.items()
        }

        # Save results
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model_metadata": self.agent.get_metadata(),
            "sample_size": len(selected_tasks),
            "budget": budget,
            "elapsed_seconds": round(elapsed, 2),
            "aggregated_metrics": aggregated,
            "task_level_records": [
                {
                    "task_id": t.instance_id,
                    "results": {fmt: all_evals[fmt][idx].__dict__ for fmt in self.formats}
                }
                for idx, t in enumerate(selected_tasks)
            ]
        }

        out_file = self.output_dir / "metrics" / f"experiment_results_{budget}tokens.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
