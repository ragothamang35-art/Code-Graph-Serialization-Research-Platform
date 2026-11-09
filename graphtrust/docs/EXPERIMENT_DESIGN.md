# GraphTrust Experimental Design & Methodology

## 1. Experimental Conditions
- **Format A (Raw JSON)**: Standard serialization used in modern tool-use agents.
- **Format B (Structured Adjacency List)**: Minimalist node-to-target arrow representations.
- **Format C (Natural Language Sentences)**: English prose declaring definitions and relationships.
- **Baseline 1 (No Graph)**: Model given only issue description and repository context.
- **Baseline 2 (Keyword Match)**: Flat candidate file list derived from lexical search without edge relationships.

## 2. Controlled Variables
- **Task instances**: Evaluated on identical software engineering issues.
- **Retrieved Subgraph**: Frozen canonical graph with identical node IDs, names, files, lines, and edge types.
- **Model & Decoding**: Gemma 4 E2B, temperature = 0.0, top-p = 1.0, max output tokens = 256.
- **Instruction Prompt**: Identical system prompt, instruction text, and JSON schema constraints.
- **Evaluation Procedure**: Gold labels extracted directly from unified diff patches (excluding test files).

## 3. Independent & Dependent Variables
- **Independent Variable**: Textual serialization format of the retrieved code graph.
- **Dependent Variables**:
  - Primary: Accuracy@1, Accuracy@5, MRR@5.
  - Secondary: Prompt Token Consumption, Candidate Coverage, Conditional Accuracy, Parsing Reliability, Latency.

## 4. Token Budget Constraints
Budgets tested: 512, 1024, 2048, and 4096 tokens.
Truncation policy: Non-destructive node-level and edge-level inclusion. Never cut mid-token, mid-node, or mid-edge.

## 5. Statistical Rigor
- Paired task-level bootstrap 95% confidence intervals (1,000 resamples).
- Two-tailed paired t-tests and Wilcoxon signed-rank tests ($p < 0.05$).
- Standardized effect sizes via Cohen's $d$.
