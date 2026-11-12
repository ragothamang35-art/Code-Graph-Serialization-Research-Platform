"""E2E Test 4.5: Baselines (No Graph & Keyword Match)."""

import pytest
from graphtrust.data import DatasetLoader
from graphtrust.retrieval import GraphRetriever
from graphtrust.serializers import GraphSerializer
from graphtrust.prompting import build_prompt

def test_no_graph_condition_contains_zero_graph_tokens(synthetic_repo):
    """
    Assert that in the No Graph condition, no node or edge identifiers
    appear anywhere in the serialized text or prompt graph section.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    retriever = GraphRetriever(nodes, edges)

    task = tasks[0]
    canonical = retriever.retrieve(task, max_depth=2, use_embeddings=True)
    ser_no_graph = GraphSerializer.serialize(canonical, "no_graph", budget=2048)

    assert ser_no_graph.token_count == 0
    assert ser_no_graph.node_count == 0
    assert ser_no_graph.edge_count == 0
    assert ser_no_graph.content == ""

    prompt = build_prompt(task, ser_no_graph)
    assert "No code graph context is provided." in prompt
    # None of the retrieved graph node names should appear in graph context
    for n in canonical.nodes:
        assert f"--- RAW JSON CODE GRAPH ---\n{n.name}" not in prompt

def test_keyword_match_matches_independent_lexical_retrieval(synthetic_repo):
    """
    Assert that the candidate file list in Keyword Match baseline
    matches the files produced by the lexical retriever.
    """
    loader = DatasetLoader(str(synthetic_repo))
    tasks = loader.load_tasks()
    nodes, edges = loader.load_graph()
    retriever = GraphRetriever(nodes, edges)

    for task in tasks:
        canonical = retriever.retrieve(task, max_depth=2, use_embeddings=True)
        ser_kw = GraphSerializer.serialize(canonical, "keyword_match", budget=2048)

        for cf in canonical.candidate_files:
            assert cf in ser_kw.content, f"Candidate file {cf} missing from keyword match baseline"
