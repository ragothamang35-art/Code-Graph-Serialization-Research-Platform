"""Data structures and schemas for the GraphTrust research framework."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Task:
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    hints_text: str = ""
    patch: str = ""
    test_patch: str = ""
    created_at: str = ""
    gold_files: List[str] = field(default_factory=list)

@dataclass
class GraphNode:
    id: str
    name: str
    text: str
    file: str
    line: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "text": self.text
        }

@dataclass
class GraphEdge:
    source: str
    target: str
    type: str
    key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"source": self.source, "target": self.target, "type": self.type}
        if self.key is not None:
            d["key"] = self.key
        return d

@dataclass
class RetrievedSubgraph:
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    seed_node_ids: List[str]
    candidate_files: List[str]
    retrieval_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SerializedGraph:
    format_type: str  # "json", "adjacency_list", "natural_language"
    content: str
    token_count: int
    node_count: int
    edge_count: int
    budget: int
    is_truncated: bool

@dataclass
class ModelPrediction:
    task_id: str
    format_type: str
    budget: int
    predicted_files: List[str]
    reasoning: str
    raw_output: str
    parsing_success: bool
    latency_ms: float = 0.0

@dataclass
class TaskEvaluation:
    task_id: str
    format_type: str
    budget: int
    acc_at_1: float
    acc_at_5: float
    mrr_at_5: float
    candidate_coverage: float
    conditional_acc_1: float
    gold_files: List[str]
    predicted_files: List[str]
    candidate_files: List[str]
    token_count: int
