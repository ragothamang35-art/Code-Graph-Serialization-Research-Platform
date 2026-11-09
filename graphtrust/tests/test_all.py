"""Comprehensive unit tests for GraphTrust research framework."""

import unittest
from graphtrust.data import normalize_path, extract_gold_files_from_patch
from graphtrust.schema import Task, GraphNode, GraphEdge
from graphtrust.retrieval import GraphRetriever, cosine_similarity
from graphtrust.serializers import (
    serialize_raw_json,
    serialize_adjacency_list,
    serialize_natural_language,
    GraphSerializer
)
from graphtrust.token_budget import estimate_gemma_tokens, TokenBudgetManager
from graphtrust.evaluation import compute_reciprocal_rank_5, evaluate_task, aggregate_evaluations
from graphtrust.schema import ModelPrediction
from graphtrust.statistics import paired_bootstrap_ci, paired_t_test, cohens_d

class TestGraphTrust(unittest.TestCase):

    def test_patch_parsing_and_normalization(self):
        patch = """diff --git a/src/flask/blueprints.py b/src/flask/blueprints.py
--- a/src/flask/blueprints.py
+++ b/src/flask/blueprints.py
@@ -190,4 +190,6 @@
+        if "." in self.name:
diff --git a/tests/test_bp.py b/tests/test_bp.py
+++ b/tests/test_bp.py
"""
        gold = extract_gold_files_from_patch(patch, exclude_tests=True)
        self.assertEqual(gold, ["src/flask/blueprints.py"])
        self.assertNotIn("tests/test_bp.py", gold)

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)

    def test_serialization_invariant(self):
        """CRITICAL INVARIANT: All 3 formats must represent the exact same underlying nodes and edges."""
        nodes = [
            GraphNode(id="n1", name="PaymentService", file="src/payment.py", line=20, text="Service"),
            GraphNode(id="n2", name="InvoiceValidator", file="src/validator.py", line=45, text="Validator")
        ]
        edges = [
            GraphEdge(source="n1", target="n2", type="calls")
        ]

        json_str = serialize_raw_json(nodes, edges)
        adj_str = serialize_adjacency_list(nodes, edges)
        nl_str = serialize_natural_language(nodes, edges)

        # Content presence checks
        self.assertIn("PaymentService", json_str)
        self.assertIn("InvoiceValidator", json_str)
        self.assertIn("calls", json_str)

        self.assertIn("PaymentService", adj_str)
        self.assertIn("InvoiceValidator", adj_str)
        self.assertIn("calls", adj_str)

        self.assertIn("PaymentService", nl_str)
        self.assertIn("InvoiceValidator", nl_str)
        self.assertIn("calls", nl_str)

        # Budgeted serialization invariant check
        from graphtrust.schema import RetrievedSubgraph
        sub = RetrievedSubgraph(nodes=nodes, edges=edges, seed_node_ids=["n1"], candidate_files=["src/payment.py", "src/validator.py"])
        ser_a = GraphSerializer.serialize(sub, "json", budget=2048)
        ser_b = GraphSerializer.serialize(sub, "adjacency_list", budget=2048)
        ser_c = GraphSerializer.serialize(sub, "natural_language", budget=2048)

        self.assertEqual(ser_a.node_count, ser_b.node_count)
        self.assertEqual(ser_b.node_count, ser_c.node_count)
        self.assertEqual(ser_a.edge_count, ser_b.edge_count)
        self.assertEqual(ser_b.edge_count, ser_c.edge_count)

    def test_token_budget_truncation_preserves_completeness(self):
        """Test that truncation never cuts mid-node or mid-edge."""
        nodes = [
            GraphNode(id=f"n{i}", name=f"Node_{i}", file=f"src/file_{i}.py", line=i*10, text=f"Text_{i}")
            for i in range(10)
        ]
        edges = [
            GraphEdge(source=f"n{i}", target=f"n{i+1}", type="calls")
            for i in range(9)
        ]
        mgr = TokenBudgetManager(100)
        inc_nodes, inc_edges, truncated = mgr.truncate_canonical_graph(
            nodes, edges, serialize_raw_json, budget=180, fixed_prompt_tokens=20
        )
        self.assertTrue(truncated)
        self.assertLess(len(inc_nodes), len(nodes))
        # Ensure every edge's source and target exist in inc_nodes
        inc_ids = set(n.id for n in inc_nodes)
        for e in inc_edges:
            self.assertIn(e.source, inc_ids)
            self.assertIn(e.target, inc_ids)

    def test_evaluation_metrics(self):
        task = Task(
            instance_id="t1",
            repo="org/repo",
            base_commit="abc",
            problem_statement="issue",
            gold_files=["src/payment.py"]
        )
        sub = from_sub = type("Subgraph", (), {"candidate_files": ["src/payment.py", "src/other.py"]})()

        # Correct at rank 1
        pred1 = ModelPrediction(
            task_id="t1", format_type="json", budget=1024,
            predicted_files=["src/payment.py", "src/other.py"],
            reasoning="test", raw_output="{}", parsing_success=True
        )
        ev1 = evaluate_task(task, pred1, sub, token_count=100)
        self.assertEqual(ev1.acc_at_1, 1.0)
        self.assertEqual(ev1.acc_at_5, 1.0)
        self.assertEqual(ev1.mrr_at_5, 1.0)
        self.assertEqual(ev1.candidate_coverage, 1.0)

        # Correct at rank 2
        pred2 = ModelPrediction(
            task_id="t1", format_type="json", budget=1024,
            predicted_files=["src/other.py", "src/payment.py"],
            reasoning="test", raw_output="{}", parsing_success=True
        )
        ev2 = evaluate_task(task, pred2, sub, token_count=100)
        self.assertEqual(ev2.acc_at_1, 0.0)
        self.assertEqual(ev2.acc_at_5, 1.0)
        self.assertEqual(ev2.mrr_at_5, 0.5)

        # Incorrect
        pred3 = ModelPrediction(
            task_id="t1", format_type="json", budget=1024,
            predicted_files=["src/wrong.py"],
            reasoning="test", raw_output="{}", parsing_success=True
        )
        ev3 = evaluate_task(task, pred3, sub, token_count=100)
        self.assertEqual(ev3.acc_at_1, 0.0)
        self.assertEqual(ev3.acc_at_5, 0.0)
        self.assertEqual(ev3.mrr_at_5, 0.0)

    def test_statistical_calculations(self):
        x = [1.0, 1.0, 1.0, 0.0, 1.0]
        y = [0.0, 0.0, 1.0, 0.0, 0.0]
        diff, low, high = paired_bootstrap_ci(x, y, num_bootstrap=200)
        self.assertGreater(diff, 0)
        t_stat, p_val = paired_t_test(x, y)
        self.assertGreater(t_stat, 0)
        d = cohens_d(x, y)
        self.assertGreater(d, 0)

if __name__ == "__main__":
    unittest.main()
