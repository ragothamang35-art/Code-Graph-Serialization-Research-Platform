"""E2E Test 4.4: Token Budget Enforcement."""

import pytest
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.token_budget import estimate_gemma_tokens

def test_token_budget_monotonicity_and_truncation_logging(synthetic_repo):
    """
    Assert that as context token budget shrinks (4096 -> 512 -> 256 -> 128),
    the included node and edge counts are strictly non-increasing,
    and truncation status is explicitly set to True when the full graph does not fit.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)

    task = tasks[0]
    canonical = retriever.retrieve(task, max_depth=2, use_embeddings=True)

    budgets = [4096, 512, 256, 128]
    prev_nodes = float("inf")
    prev_edges = float("inf")

    for b in budgets:
        ser = GraphSerializer.serialize(canonical, "json", budget=b, fixed_prompt_tokens=50)
        assert ser.token_count <= b, f"Serialized tokens ({ser.token_count}) exceeded budget ({b})"
        assert ser.node_count <= prev_nodes, f"Node count increased at budget {b}"
        assert ser.edge_count <= prev_edges, f"Edge count increased at budget {b}"

        if ser.node_count < len(canonical.nodes) or ser.edge_count < len(canonical.edges):
            assert ser.is_truncated is True, f"Expected is_truncated=True at budget {b}"

        prev_nodes = ser.node_count
        prev_edges = ser.edge_count

def test_fixed_prompt_overhead_included_in_budget_accounting():
    """
    Assert that the fixed instructions and task metadata tokens
    are accounted for in the effective serialization budget.
    """
    from graphtrust.token_budget import TokenBudgetManager
    from graphtrust.schema import GraphNode, GraphEdge
    from graphtrust.serializers import serialize_raw_json

    nodes = [GraphNode(id=f"n{i}", name=f"Node_{i}", file=f"src/f{i}.py", line=10, text="txt") for i in range(5)]
    edges = [GraphEdge(source=f"n{i}", target=f"n{i+1}", type="calls") for i in range(4)]

    mgr = TokenBudgetManager(budget=200)
    # With 100 fixed tokens, effective budget is 100
    inc_nodes_100, _, _ = mgr.truncate_canonical_graph(nodes, edges, serialize_raw_json, budget=200, fixed_prompt_tokens=100)
    # With 0 fixed tokens, effective budget is 200
    inc_nodes_200, _, _ = mgr.truncate_canonical_graph(nodes, edges, serialize_raw_json, budget=200, fixed_prompt_tokens=0)

    assert len(inc_nodes_100) <= len(inc_nodes_200)
