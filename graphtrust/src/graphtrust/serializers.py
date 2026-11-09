"""Code Graph Serializers for Controlled Empirical Evaluation.

Implements:
- Format A: Raw JSON
- Format B: Structured Adjacency List
- Format C: Natural Language Edge Sentences
- Baseline 1: No Graph
- Baseline 2: Keyword Match candidate list

INVARIANT: For a given retrieved canonical subgraph, all three graph formats
represent exactly the same underlying nodes and edges.
"""

import json
from typing import List, Dict, Any, Tuple
from graphtrust.schema import GraphNode, GraphEdge, RetrievedSubgraph, SerializedGraph
from graphtrust.token_budget import estimate_gemma_tokens, TokenBudgetManager

def serialize_raw_json(nodes: List[GraphNode], edges: List[GraphEdge]) -> str:
    """Format A: Raw compact JSON."""
    payload = {
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "file": n.file,
                "line": n.line
            }
            for n in nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "type": e.type
            }
            for e in edges
        ]
    }
    return json.dumps(payload, indent=2)

def serialize_adjacency_list(nodes: List[GraphNode], edges: List[GraphEdge]) -> str:
    """Format B: Structured Adjacency List."""
    node_map = {n.id: n for n in nodes}
    out_edges: Dict[str, List[Tuple[str, str]]] = {n.id: [] for n in nodes}
    for e in edges:
        if e.source in node_map and e.target in node_map:
            out_edges[e.source].append((e.type, e.target))

    blocks = []
    for node in nodes:
        header = f"{node.name} [{node.file}:{node.line}]"
        lines = [header]
        for rel_type, target_id in out_edges.get(node.id, []):
            target_node = node_map[target_id]
            lines.append(f"  -> {rel_type} -> {target_node.name} [{target_node.file}:{target_node.line}]")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)

def serialize_natural_language(nodes: List[GraphNode], edges: List[GraphEdge]) -> str:
    """Format C: Natural Language Edge Sentences."""
    node_map = {n.id: n for n in nodes}
    sentences = []

    # Declarations of definitions
    for node in nodes:
        sentences.append(f"{node.name} is defined in {node.file} at line {node.line}.")

    # Relationship statements
    for edge in edges:
        if edge.source in node_map and edge.target in node_map:
            src_node = node_map[edge.source]
            tgt_node = node_map[edge.target]
            verb = edge.type.replace("_", " ")
            sentences.append(f"{src_node.name} {verb} {tgt_node.name}.")

    return "\n".join(sentences)

def serialize_keyword_match(candidate_files: List[str]) -> str:
    """Baseline 2: Lexical matching candidate file list."""
    lines = ["Candidate source files identified by keyword matching:"]
    for f in candidate_files:
        lines.append(f"- {f}")
    return "\n".join(lines)

class GraphSerializer:
    @staticmethod
    def serialize(
        subgraph: RetrievedSubgraph,
        format_type: str,
        budget: int = 2048,
        fixed_prompt_tokens: int = 150
    ) -> SerializedGraph:
        """
        Serialize the canonical subgraph under the specified format and token budget.
        Validates that nodes and edges are strictly preserved unless truncated by budget.
        """
        fmt = format_type.lower()
        budget_mgr = TokenBudgetManager(budget)

        if fmt == "no_graph":
            return SerializedGraph(
                format_type="no_graph",
                content="",
                token_count=0,
                node_count=0,
                edge_count=0,
                budget=budget,
                is_truncated=False
            )

        if fmt == "keyword_match":
            content = serialize_keyword_match(subgraph.candidate_files)
            tokens = estimate_gemma_tokens(content)
            return SerializedGraph(
                format_type="keyword_match",
                content=content,
                token_count=tokens,
                node_count=0,
                edge_count=0,
                budget=budget,
                is_truncated=False
            )

        # Select serializer function
        if fmt in ("json", "raw_json"):
            format_func = serialize_raw_json
            canon_name = "json"
        elif fmt in ("adjacency", "adjacency_list", "adj_list"):
            format_func = serialize_adjacency_list
            canon_name = "adjacency_list"
        elif fmt in ("natural_language", "nl", "nl_sentences"):
            format_func = serialize_natural_language
            canon_name = "natural_language"
        else:
            raise ValueError(f"Unknown serialization format: {format_type}")

        # Enforce token budget without truncating mid-node or mid-edge
        inc_nodes, inc_edges, is_truncated = budget_mgr.truncate_canonical_graph(
            subgraph.nodes,
            subgraph.edges,
            format_func,
            budget=budget,
            fixed_prompt_tokens=fixed_prompt_tokens
        )

        content = format_func(inc_nodes, inc_edges)
        tokens = estimate_gemma_tokens(content)

        return SerializedGraph(
            format_type=canon_name,
            content=content,
            token_count=tokens,
            node_count=len(inc_nodes),
            edge_count=len(inc_edges),
            budget=budget,
            is_truncated=is_truncated
        )
