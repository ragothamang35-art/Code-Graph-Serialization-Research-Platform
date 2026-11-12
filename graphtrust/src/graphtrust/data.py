"""Dataset loading, validation, and gold label extraction from unified diffs."""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any
from graphtrust.schema import Task, GraphNode, GraphEdge

def normalize_path(path: str) -> str:
    """Normalize file path for consistent comparison."""
    p = path.strip()
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    p = p.lstrip("./").lstrip("/")
    return p

def extract_gold_files_from_patch(patch_str: str, exclude_tests: bool = True) -> List[str]:
    """
    Extract modified source file paths from unified diff headers.
    Supports 'diff --git a/... b/...', '--- a/...', '+++ b/...', 'rename to ...', and '/dev/null'.
    Excludes test files by default as specified in research protocol.
    """
    if not patch_str:
        return []
    
    files = set()
    for raw_line in patch_str.splitlines():
        line = raw_line.strip()
        
        # Match 'rename to path'
        rename_match = re.match(r"^rename to (.+)$", line)
        if rename_match:
            f = normalize_path(rename_match.group(1))
            if f and f != "dev/null":
                files.add(f)
            continue

        # Match 'diff --git a/path b/path'
        git_match = re.match(r"^diff --git a/(.+?) b/(.+?)$", line)
        if git_match:
            tgt = normalize_path(git_match.group(2))
            src = normalize_path(git_match.group(1))
            if tgt and tgt != "dev/null":
                files.add(tgt)
            elif src and src != "dev/null":
                files.add(src)
            continue
        
        # Match '+++ b/path' or '+++ path'
        plus_match = re.match(r"^\+\+\+ (?:b/)?(.+?)$", line)
        if plus_match:
            f = normalize_path(plus_match.group(1))
            if f and f != "dev/null":
                files.add(f)
            continue

        # Match '--- a/path' when not /dev/null
        minus_match = re.match(r"^--- (?:a/)?(.+?)$", line)
        if minus_match:
            f = normalize_path(minus_match.group(1))
            if f and f != "dev/null" and "dev/null" in patch_str:
                files.add(f)
                
    result = []
    test_pattern = re.compile(r"(^|/)(test_|tests/|test/|\.test\.|\.spec\.)", re.IGNORECASE)
    for f in sorted(list(files)):
        if exclude_tests and test_pattern.search(f):
            continue
        result.append(f)
    return result

class DatasetLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_tasks(self, filename: str = "tasks.json") -> List[Task]:
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Task dataset file missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        tasks = []
        for r in raw:
            gold = r.get("gold_files") or extract_gold_files_from_patch(r.get("patch", ""))
            tasks.append(Task(
                instance_id=r["instance_id"],
                repo=r.get("repo", ""),
                base_commit=r.get("base_commit", ""),
                problem_statement=r.get("problem_statement", ""),
                hints_text=r.get("hints_text", ""),
                patch=r.get("patch", ""),
                test_patch=r.get("test_patch", ""),
                created_at=r.get("created_at", ""),
                gold_files=gold
            ))
        return tasks

    def load_graph(self, nodes_file: str = "nodes.json", edges_file: str = "edges.json") -> Tuple[List[GraphNode], List[GraphEdge]]:
        n_path = self.data_dir / nodes_file
        e_path = self.data_dir / edges_file
        if not n_path.exists() or not e_path.exists():
            raise FileNotFoundError(f"Graph files missing: {n_path} or {e_path}")
        with open(n_path, "r", encoding="utf-8") as f:
            raw_nodes = json.load(f)
        with open(e_path, "r", encoding="utf-8") as f:
            raw_edges = json.load(f)
        nodes = [GraphNode(**n) for n in raw_nodes]
        edges = [GraphEdge(**e) for e in raw_edges]
        return nodes, edges

    def load_embeddings(self, filename: str = "embeddings.json") -> Dict[str, List[float]]:
        path = self.data_dir / filename
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def inspect(self) -> Dict[str, Any]:
        """Inspect and report dataset statistics, safely detecting missing files."""
        missing_files = []
        for req_file in ["tasks.json", "nodes.json", "edges.json", "embeddings.json"]:
            if not (self.data_dir / req_file).exists():
                missing_files.append(req_file)

        if missing_files:
            return {
                "status": "error",
                "missing_files": missing_files,
                "error_message": f"Dataset inspection failed: Missing required file(s): {', '.join(missing_files)} in {self.data_dir}",
                "data_directory": str(self.data_dir)
            }

        tasks = self.load_tasks()
        nodes, edges = self.load_graph()
        emb = self.load_embeddings()
        emb_dim = len(next(iter(emb.values()))) if emb else 0

        repos = set(t.repo for t in tasks)
        missing_gold = sum(1 for t in tasks if not t.gold_files)

        return {
            "status": "success",
            "total_tasks": len(tasks),
            "repositories": sorted(list(repos)),
            "graph_nodes": len(nodes),
            "graph_edges": len(edges),
            "embeddings_count": len(emb),
            "embedding_dimension": emb_dim,
            "tasks_missing_gold_labels": missing_gold,
            "valid_task_count": len(tasks),
            "data_directory": str(self.data_dir)
        }
