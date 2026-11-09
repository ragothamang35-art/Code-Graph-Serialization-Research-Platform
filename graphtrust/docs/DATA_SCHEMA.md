# GraphTrust Data Schema Specification

## 1. Tasks (`tasks.json`)
Conforms to standard SWE benchmark records:
- `instance_id` (string): Unique task identifier (e.g., `flask__flask-4045`).
- `repo` (string): GitHub repository path (`pallets/flask`).
- `base_commit` (string): Git SHA of the parent commit.
- `problem_statement` (string): Real-world issue report or bug description.
- `hints_text` (string): Optional issue commentary or triage discussion.
- `patch` (string): Ground-truth unified diff patch modifying source files.
- `test_patch` (string): Unified diff adding or updating validation tests.
- `created_at` (string): ISO-8601 timestamp.
- `gold_files` (list[string]): Extracted source files modified by `patch` (test paths excluded).

## 2. Graph Nodes (`nodes.json`)
Syntactic code entities extracted via AST:
- `id` (string): Unique node identifier (e.g., `flask_bp_add_url_rule`).
- `name` (string): Qualified function, class, or method symbol name.
- `text` (string): Docstring, comment, or definition summary.
- `file` (string): Relative repository file path (e.g., `src/flask/blueprints.py`).
- `line` (integer): 1-indexed source code line number.

## 3. Graph Edges (`edges.json`)
Directed static analysis dependencies:
- `source` (string): Origin node ID.
- `target` (string): Destination node ID.
- `type` (string): Relation category (`calls`, `inherits`, `imports`, `delegates`, `raises`, `instantiates`).
- `key` (optional string): Auxiliary edge attribute.

## 4. Node Embeddings (`embeddings.json`)
Precomputed dense semantic representations:
- Key: Node ID.
- Value: 256-dimensional $L_2$-normalized floating-point vector.
