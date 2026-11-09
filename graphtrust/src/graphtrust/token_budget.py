"""Token budgeting and tokenizer accounting for Gemma models."""

import re
from typing import List, Dict, Any, Tuple
from graphtrust.schema import GraphNode, GraphEdge

def estimate_gemma_tokens(text: str) -> int:
    """
    Estimate token count for Gemma 2/4 SentencePiece BPE tokenizer.
    Gemma's vocabulary handles code punctuation, camelCase splits, snake_case, and indentations.
    Empirically, 1 token ~ 3.5 to 3.8 characters for code/JSON.
    We split on whitespace, subwords, and punctuation to provide an accurate BPE proxy.
    """
    if not text:
        return 0
    # Tokenize by punctuation, numbers, camelCase splits, whitespace
    parts = re.findall(r"\w+|[^\w\s]|\s+", text)
    count = 0
    for p in parts:
        if p.isspace():
            count += max(1, len(p) // 4)
        elif len(p) <= 4:
            count += 1
        else:
            # Subword decomposition for longer identifiers
            count += (len(p) + 2) // 3
    return max(1, count)

class TokenBudgetManager:
    def __init__(self, budget: int):
        self.budget = budget

    def fits(self, text: str) -> bool:
        return estimate_gemma_tokens(text) <= self.budget

    def truncate_canonical_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        format_func,
        budget: int,
        fixed_prompt_tokens: int = 120
    ) -> Tuple[List[GraphNode], List[GraphEdge], bool]:
        """
        Enforce token budget without ever truncating mid-node or mid-edge.
        Preserves graph integrity by incrementally including nodes in priority order
        and only edges whose endpoints are both present.
        """
        effective_budget = max(50, budget - fixed_prompt_tokens)

        # First check if the complete graph fits
        test_str = format_func(nodes, edges)
        if estimate_gemma_tokens(test_str) <= effective_budget:
            return nodes, edges, False

        # If it exceeds, incrementally add nodes and valid edges
        included_nodes: List[GraphNode] = []
        included_edges: List[GraphEdge] = []
        node_id_set = set()

        for node in nodes:
            cand_nodes = included_nodes + [node]
            cand_id_set = set(n.id for n in cand_nodes)
            cand_edges = [
                e for e in edges
                if e.source in cand_id_set and e.target in cand_id_set
            ]
            cand_str = format_func(cand_nodes, cand_edges)
            if estimate_gemma_tokens(cand_str) <= effective_budget:
                included_nodes = cand_nodes
                node_id_set = cand_id_set
                included_edges = cand_edges
            else:
                break

        # If even 1 node doesn't fit, take at least 1 node so model gets minimal context
        if not included_nodes and nodes:
            included_nodes = [nodes[0]]
            included_edges = []

        is_truncated = (len(included_nodes) < len(nodes)) or (len(included_edges) < len(edges))
        return included_nodes, included_edges, is_truncated
