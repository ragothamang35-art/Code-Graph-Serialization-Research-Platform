"""Ablation Studies for GraphTrust.

Independent ablation pipelines:
- Ablation A: Graph expansion depth (0-hop, 1-hop, 2-hop)
- Ablation B: Embedding-based expansion (lexical only vs lexical + embeddings)
- Ablation C: Subgraph size impacts
- Ablation D: Token budget impacts
"""

from typing import List, Dict, Any
from graphtrust.schema import Task
from graphtrust.retrieval import GraphRetriever
from graphtrust.model import GemmaAgent
from graphtrust.serializers import GraphSerializer
from graphtrust.evaluation import evaluate_task, aggregate_evaluations

class AblationSuite:
    def __init__(self, retriever: GraphRetriever, agent: GemmaAgent):
        self.retriever = retriever
        self.agent = agent

    def ablate_depth(self, tasks: List[Task], depths: List[int] = [0, 1, 2], budget: int = 2048) -> Dict[str, Any]:
        """Ablation A: Evaluate effect of graph expansion hop depth."""
        results = {}
        for d in depths:
            evals = []
            for t in tasks:
                subgraph = self.retriever.retrieve(task=t, max_depth=d, use_embeddings=True)
                serialized = GraphSerializer.serialize(subgraph, "json", budget=budget)
                pred = self.agent.predict(t, serialized)
                ev = evaluate_task(t, pred, subgraph, serialized.token_count)
                evals.append(ev)
            results[f"depth_{d}_hops"] = aggregate_evaluations(evals)
        return results

    def ablate_embeddings(self, tasks: List[Task], budget: int = 2048) -> Dict[str, Any]:
        """Ablation B: Lexical retrieval only vs Lexical + Cosine similarity embeddings."""
        res_lexical = []
        res_combined = []

        for t in tasks:
            # Lexical only
            sub_lex = self.retriever.retrieve(task=t, max_depth=2, use_embeddings=False)
            ser_lex = GraphSerializer.serialize(sub_lex, "natural_language", budget=budget)
            pred_lex = self.agent.predict(t, ser_lex)
            res_lexical.append(evaluate_task(t, pred_lex, sub_lex, ser_lex.token_count))

            # Lexical + embeddings
            sub_comb = self.retriever.retrieve(task=t, max_depth=2, use_embeddings=True)
            ser_comb = GraphSerializer.serialize(sub_comb, "natural_language", budget=budget)
            pred_comb = self.agent.predict(t, ser_comb)
            res_combined.append(evaluate_task(t, pred_comb, sub_comb, ser_comb.token_count))

        return {
            "lexical_only": aggregate_evaluations(res_lexical),
            "lexical_plus_embeddings": aggregate_evaluations(res_combined)
        }

    def ablate_token_budgets(
        self,
        tasks: List[Task],
        budgets: List[int] = [512, 1024, 2048, 4096],
        formats: List[str] = ["json", "adjacency_list", "natural_language"]
    ) -> Dict[str, Any]:
        """Ablation D: Evaluate performance under restricted vs generous context windows."""
        results = {}
        for b in budgets:
            results[f"budget_{b}"] = {}
            for fmt in formats:
                evals = []
                for t in tasks:
                    subgraph = self.retriever.retrieve(t, max_depth=2, use_embeddings=True)
                    serialized = GraphSerializer.serialize(subgraph, fmt, budget=b)
                    pred = self.agent.predict(t, serialized)
                    evals.append(evaluate_task(t, pred, subgraph, serialized.token_count))
                results[f"budget_{b}"][fmt] = aggregate_evaluations(evals)
        return results
