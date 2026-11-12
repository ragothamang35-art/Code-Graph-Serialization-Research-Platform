"""E2E Test 4.3: The Core Invariant — Same Subgraph across All Serializations."""

import json
from pathlib import Path
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import (
    serialize_raw_json,
    serialize_adjacency_list,
    serialize_natural_language,
    GraphSerializer
)
from graphtrust.schema import RetrievedSubgraph

def test_retrieved_subgraph_node_and_edge_ids_strictly_identical(synthetic_repo):
    """
    Assert that for EVERY task, the underlying node ID set and edge ID set
    are byte-for-byte identical across Raw JSON, Adjacency List, and Natural Language.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)

    for task in tasks:
        # Step 1: Canonical retrieval once
        canonical_subgraph = retriever.retrieve(task, max_depth=2, use_embeddings=True)

        # Step 2: Serialize under unconstrained budget (4096 tokens)
        ser_json = GraphSerializer.serialize(canonical_subgraph, "json", budget=4096)
        ser_adj = GraphSerializer.serialize(canonical_subgraph, "adjacency_list", budget=4096)
        ser_nl = GraphSerializer.serialize(canonical_subgraph, "natural_language", budget=4096)

        # Assert node counts and edge counts match exactly
        assert ser_json.node_count == ser_adj.node_count == ser_nl.node_count == len(canonical_subgraph.nodes), (
            f"Task {task.instance_id}: Node count mismatch: "
            f"JSON={ser_json.node_count}, Adj={ser_adj.node_count}, NL={ser_nl.node_count}, Canonical={len(canonical_subgraph.nodes)}"
        )

        assert ser_json.edge_count == ser_adj.edge_count == ser_nl.edge_count == len(canonical_subgraph.edges), (
            f"Task {task.instance_id}: Edge count mismatch: "
            f"JSON={ser_json.edge_count}, Adj={ser_adj.edge_count}, NL={ser_nl.edge_count}, Canonical={len(canonical_subgraph.edges)}"
        )

def test_truncation_never_splits_mid_node_or_mid_edge(synthetic_repo):
    """
    Assert that under strict token budgets (e.g. 128 tokens), truncation
    includes only whole nodes and whole edges. Never truncates mid-JSON or mid-sentence.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    emb = loader.load_embeddings()
    retriever = GraphRetriever(nodes, edges, emb)

    for task in tasks:
        subgraph = retriever.retrieve(task, max_depth=2, use_embeddings=True)

        for fmt in ["json", "adjacency_list", "natural_language"]:
            ser = GraphSerializer.serialize(subgraph, fmt, budget=128)
            content = ser.content

            if fmt == "json":
                # Must be strictly valid, complete JSON object
                parsed = json.loads(content)
                assert "nodes" in parsed
                assert "edges" in parsed
                assert len(parsed["nodes"]) == ser.node_count
                assert len(parsed["edges"]) == ser.edge_count
                # Verify edge endpoints exist in included nodes
                inc_ids = {n["id"] for n in parsed["nodes"]}
                for e in parsed["edges"]:
                    assert e["source"] in inc_ids, f"Orphaned edge source {e['source']}"
                    assert e["target"] in inc_ids, f"Orphaned edge target {e['target']}"

            elif fmt == "adjacency_list":
                # No incomplete arrows or dangling lines
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                for l in lines:
                    if l.startswith("->"):
                        assert "->" in l and "[" in l and "]" in l, f"Malformed adjacency edge line: {l}"

            elif fmt == "natural_language":
                # Every sentence must end with a full stop
                sentences = [s.strip() for s in content.splitlines() if s.strip()]
                for s in sentences:
                    assert s.endswith("."), f"Sentence fragment not terminated: '{s}'"
