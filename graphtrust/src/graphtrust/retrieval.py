"""Canonical Graph Retrieval Pipeline.

Implements the 5-step retrieval pipeline:
1. Query processing
2. Graph seed selection (lexical matching)
3. Graph expansion (k-hop traversal)
4. Embedding-based expansion (seed-to-node cosine similarity)
5. Canonical candidate graph construction
"""

import re
import math
from typing import List, Dict, Set, Tuple, Any
from collections import deque
from graphtrust.schema import Task, GraphNode, GraphEdge, RetrievedSubgraph

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def extract_query_terms(text: str) -> Set[str]:
    """Extract code identifiers, words, and dotted paths from query text."""
    # Find words with letters, digits, underscores, dots
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_.]*", text)
    terms = set()
    for tok in tokens:
        terms.add(tok.lower())
        # Also split on dot or underscore
        for sub in re.split(r"[._]", tok):
            if len(sub) >= 3:
                terms.add(sub.lower())
    return terms

class GraphRetriever:
    def __init__(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        embeddings: Dict[str, List[float]] = None
    ):
        self.nodes = nodes
        self.edges = edges
        self.embeddings = embeddings or {}
        self.node_by_id: Dict[str, GraphNode] = {n.id: n for n in nodes}
        
        # Build adjacency mapping (bidirectional for traversal)
        self.adj: Dict[str, List[Tuple[str, GraphEdge]]] = {n.id: [] for n in nodes}
        for e in edges:
            if e.source in self.adj and e.target in self.node_by_id:
                self.adj[e.source].append((e.target, e))
            if e.target in self.adj and e.source in self.node_by_id:
                self.adj[e.target].append((e.source, e))

    def retrieve(
        self,
        task: Task,
        max_depth: int = 2,
        use_embeddings: bool = True,
        top_k_embedding_nodes: int = 2,
        embedding_sim_threshold: float = 0.4,
        max_total_nodes: int = 15
    ) -> RetrievedSubgraph:
        """
        Execute deterministic 5-step retrieval to build the single canonical subgraph.
        This canonical subgraph MUST be shared identically across all serialization formats.
        """
        # Step 1: Query processing
        query_text = f"{task.problem_statement} {task.hints_text} {task.repo}"
        terms = extract_query_terms(query_text)

        # Step 2: Seed selection via lexical matching
        seed_scores: Dict[str, float] = {}
        for node in self.nodes:
            score = 0.0
            name_lower = node.name.lower()
            file_lower = node.file.lower()
            text_lower = node.text.lower()

            for term in terms:
                if term in name_lower:
                    score += 3.0
                elif term in file_lower:
                    score += 2.0
                elif term in text_lower:
                    score += 1.0

            if score > 0:
                seed_scores[node.id] = score

        # Select top seed nodes (at least 1, max 4)
        sorted_seeds = sorted(seed_scores.items(), key=lambda x: x[1], reverse=True)
        seed_node_ids = [nid for nid, _ in sorted_seeds[:4]]

        if not seed_node_ids and self.nodes:
            # Fallback to repo match or first node
            for node in self.nodes:
                if task.repo and task.repo.split("/")[-1].lower() in node.file.lower():
                    seed_node_ids.append(node.id)
                    break
            if not seed_node_ids:
                seed_node_ids = [self.nodes[0].id]

        # Step 3: Graph expansion (k-hop breadth-first search)
        visited_nodes: Set[str] = set(seed_node_ids)
        included_edges: List[GraphEdge] = []
        edge_seen = set()

        if max_depth > 0:
            queue = deque([(nid, 0) for nid in seed_node_ids])
            while queue and len(visited_nodes) < max_total_nodes:
                curr_id, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                for neighbor_id, edge in self.adj.get(curr_id, []):
                    edge_key = (edge.source, edge.target, edge.type)
                    if edge_key not in edge_seen:
                        edge_seen.add(edge_key)
                        included_edges.append(edge)

                    if neighbor_id not in visited_nodes:
                        visited_nodes.add(neighbor_id)
                        queue.append((neighbor_id, depth + 1))
                        if len(visited_nodes) >= max_total_nodes:
                            break

        # Step 4: Embedding-based expansion (seed-to-node cosine similarity)
        # Note: We compare lexical seed embeddings with candidate node embeddings
        if use_embeddings and self.embeddings and seed_node_ids:
            seed_vectors = [self.embeddings[sid] for sid in seed_node_ids if sid in self.embeddings]
            if seed_vectors:
                # Average seed vector
                avg_seed_vec = [
                    sum(v[i] for v in seed_vectors) / len(seed_vectors)
                    for i in range(len(seed_vectors[0]))
                ]
                candidates = []
                for node in self.nodes:
                    if node.id not in visited_nodes and node.id in self.embeddings:
                        sim = cosine_similarity(avg_seed_vec, self.embeddings[node.id])
                        if sim >= embedding_sim_threshold:
                            candidates.append((node.id, sim))

                candidates.sort(key=lambda x: x[1], reverse=True)
                for cand_id, _ in candidates[:top_k_embedding_nodes]:
                    if len(visited_nodes) < max_total_nodes:
                        visited_nodes.add(cand_id)
                        # Include connected edges
                        for neighbor_id, edge in self.adj.get(cand_id, []):
                            if neighbor_id in visited_nodes:
                                edge_key = (edge.source, edge.target, edge.type)
                                if edge_key not in edge_seen:
                                    edge_seen.add(edge_key)
                                    included_edges.append(edge)

        # Step 5: Canonical retrieved subgraph
        retrieved_nodes = [self.node_by_id[nid] for nid in visited_nodes if nid in self.node_by_id]
        
        # Sort nodes deterministically by file, then line
        retrieved_nodes.sort(key=lambda n: (n.file, n.line, n.name))
        
        # Candidate files
        candidate_files = sorted(list(set(n.file for n in retrieved_nodes)))

        return RetrievedSubgraph(
            nodes=retrieved_nodes,
            edges=included_edges,
            seed_node_ids=seed_node_ids,
            candidate_files=candidate_files,
            retrieval_params={
                "max_depth": max_depth,
                "use_embeddings": use_embeddings,
                "seed_count": len(seed_node_ids),
                "total_nodes": len(retrieved_nodes),
                "total_edges": len(included_edges)
            }
        )
