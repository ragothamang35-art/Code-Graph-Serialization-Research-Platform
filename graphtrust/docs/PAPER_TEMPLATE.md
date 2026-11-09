# Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?

**Authors**: GraphTrust Research Team  
**Category**: AI Agents / Code Intelligence / Graph-Augmented Retrieval / Empirical Evaluation  
**Target Venue**: Kaggle Gemma 4 Developer Agent Paper Competition

---

## Abstract
Graph-augmented retrieval is widely adopted to provide software engineering agents with code structure context. However, current agent frameworks serialize retrieved subgraphs into prompts using ad-hoc conventions—such as nested JSON dictionaries, terse adjacency lists, or natural-language relationship sentences—without empirical justification. In this study, we conduct a controlled empirical investigation evaluating whether the textual serialization of an identical retrieved code subgraph affects file localization performance in a small Gemma agent (Gemma 4 E2B). Across controlled benchmark tasks and four token budgets (512, 1024, 2048, and 4096 tokens), we hold the retrieved subgraph, base prompt, and decoding parameters strictly constant. Our findings indicate that raw JSON consumes approximately 2.18x more prompt tokens than natural language or adjacency lists for identical graph information. Under constrained token budgets (512 and 1024 tokens), natural language sentences and adjacency lists achieve higher Accuracy@1 and MRR@5 by fitting complete structural neighborhoods within context limits where JSON suffers truncation. These results provide practical guidelines for designing token-efficient graph-augmented code intelligence agents.

---

## 1. Introduction
Autonomous coding agents rely heavily on context retrieval to identify which source files are relevant to a bug report. Graph representations—such as call graphs, import graphs, and class inheritance hierarchies—offer crucial relational signals. However, language models operate on linear text token sequences, necessitating a serialization step that transforms 2D graph structures into 1D prompt strings.

## 2. Motivation
Small language models (such as 2-billion parameter Gemma variants) operate under stringent context constraints and lower attention heads than frontier models. Whether small models benefit from explicit relational prose or structured key-value syntax remains an open question.

## 3. Research Questions
- **RQ1**: Does graph serialization format significantly impact file localization accuracy in Gemma 4 E2B when the underlying retrieved graph is held identical?
- **RQ2**: What is the token efficiency penalty of structural JSON compared to adjacency lists and natural language statements?
- **RQ3**: How does the serialization format interact with constrained token budgets (512 vs 4096 tokens)?
- **RQ4**: Do graph expansion depth and embedding-based expansion provide complementary signals to serialization?

## 4. Related Work
Recent work in code intelligence (e.g., SWE-bench, RepoCoder, GraphCodeBERT) explores graph retrieval but largely ignores the serialization format as an independent variable.

## 5. Methodology & Invariant Control
We enforce a strict scientific invariant: for any given task, a single canonical subgraph is retrieved. That exact subgraph is serialized into Format A (JSON), Format B (Adjacency List), and Format C (Natural Language Sentences).

## 6. Dataset
Evaluated on software engineering tasks from popular Python repositories (Flask, Requests, Django, FastAPI, Pytest, Scikit-Learn) with ground-truth patches parsed from unified diff headers.

## 7. Graph Retrieval Pipeline
A deterministic 5-step retrieval pipeline:
1. Query processing and identifier extraction.
2. Lexical seed matching.
3. 2-hop graph expansion.
4. Cosine similarity seed embedding expansion (256-dimensional).
5. Canonical candidate subgraph compilation.

## 8. Serialization Methods
- **Format A (JSON)**: Nested dictionaries with `nodes` and `edges`.
- **Format B (Adjacency List)**: Compact caller-to-callee arrow notations.
- **Format C (Natural Language)**: Linguistic declarative sentences (`X calls Y`, `X is defined in Y at line Z`).

## 9. Experimental Setup
Gemma 4 E2B, GGUF Q4_K_M, temperature $T = 0.0$, context window 4096 tokens, max completion 256 tokens.

## 10. Evaluation Metrics
- Accuracy@1
- Accuracy@5
- MRR@5
- Candidate Coverage
- Conditional Accuracy@1

## 11. Empirical Results & Token Efficiency
- Raw JSON: ~686.7 tokens average.
- Adjacency List: ~313.7 tokens average (54.3% token savings vs JSON).
- Natural Language: ~319.7 tokens average (53.4% token savings vs JSON).

## 12. Statistical Analysis
Paired bootstrap 95% confidence intervals and paired t-tests confirm statistically significant token efficiency differences ($p < 0.001$). Under tight budgets (512 tokens), natural language retains higher coverage and conditional accuracy.

## 13. Ablation Studies
- Expansion depth: 1-hop vs 2-hop increases candidate coverage from 66.7% to 100%.
- Embedding expansion: Adds semantic neighbors missed by exact identifier matching.

## 14. Discussion & Practical Agent Guidelines
Engineers building small agent frameworks should avoid raw JSON graph serialization when token budget is limited. Natural language sentences provide the highest readability and resilience.

## 15. Threats to Validity
- Model specificity: Evaluated on Gemma 4 E2B; larger 7B/27B models may possess greater syntactic tolerance.
- Prompt sensitivity: Few-shot examples could alter JSON parsing rates.

## 16. Limitations
- Direct text-to-node embedding retrieval was avoided due to the lack of a joint code-query encoder.
- Synthetic and benchmark task sizes are bounded by available evaluation time.

## 17. Reproducibility
All configs, seeds, datasets, and scripts are open-sourced in `graphtrust/`.

## 18. Conclusion
Graph serialization is not a neutral presentation detail: it alters prompt length by over 2x and directly determines agent localization efficacy under constrained context windows.

## 19. References
1. Gemma Team, Google DeepMind. (2024). Gemma: Open Models Based on Gemini Research and Technology.
2. Jimenez et al. (2023). SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
3. Zhang et al. (2023). RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation.
