export interface Task {
  instance_id: string;
  repo: string;
  base_commit: string;
  created_at: string;
  problem_statement: string;
  hints_text: string;
  patch: string;
  test_patch: string;
  gold_files: string[];
}

export interface GraphNode {
  id: string;
  name: string;
  text: string;
  file: string;
  line: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  key?: string;
}

export interface RetrievedSubgraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  seed_node_ids: string[];
  candidate_files: string[];
  retrieval_params: {
    max_depth: number;
    use_embeddings: boolean;
    seed_count: number;
    total_nodes: number;
    total_edges: number;
  };
}

export interface SerializedGraph {
  format_type: 'json' | 'adjacency_list' | 'natural_language' | 'no_graph' | 'keyword_match';
  content: string;
  token_count: number;
  node_count: number;
  edge_count: number;
  budget: number;
  is_truncated: boolean;
}

export interface PredictionResult {
  task_id: string;
  format_type: string;
  budget: number;
  token_count: number;
  is_truncated: boolean;
  predicted_files: string[];
  gold_files: string[];
  candidate_files: string[];
  reasoning: string;
  raw_output: string;
  parsing_success: boolean;
  latency_ms: number;
  is_mock: boolean;
  metrics: {
    acc_at_1: number;
    acc_at_5: number;
    mrr_at_5: number;
    candidate_coverage: number;
    conditional_acc_1: number;
  };
}

export interface BenchmarkSummary {
  sample_size: number;
  acc_at_1: number;
  acc_at_5: number;
  mrr_at_5: number;
  candidate_coverage: number;
  avg_tokens: number;
  truncation_rate: number;
}

export interface BenchmarkResult {
  budget: number;
  summaries: Record<string, BenchmarkSummary>;
  task_level: Record<string, any[]>;
}

export interface SystemStatus {
  tasks_count: number;
  graph_nodes: number;
  graph_edges: number;
  embeddings_count: number;
  has_gemini_api_key: boolean;
  python_tests_passed: number;
  python_tests_total: number;
  active_model: string;
}
