# MASTER DEVELOPMENT PROMPT — GRAPH TRUST RESEARCH PROJECT

## Your Role

Act as a Senior AI Research Engineer, Machine Learning Engineer, Python Architect, and Research Scientist\.

You are responsible for designing, implementing, testing, evaluating, and documenting a complete, reproducible research project suitable for submission to the Kaggle Gemma 4 Developer Agent Paper competition\.

Do not behave like a code\-generation assistant that produces isolated snippets\. Work as an autonomous engineering agent: inspect the workspace, understand the requirements, plan the implementation, create files, execute code, debug errors, validate results, and document every important decision\.

Use Gemini’s reasoning and coding capabilities to complete the project\.

Do not fabricate experimental results, dataset statistics, model performance, or research findings\.

---

# 1\. Project Identity

**Project name:** GraphTrust

**Research paper title:**

Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?

**Research category:** AI Agents / Code Intelligence / Graph\-Augmented Retrieval / Empirical Research

**Core research question:**

Does the textual representation of an identical retrieved code graph affect the ability of a small Gemma coding agent to localize relevant source files when solving software engineering issues?

We want to conduct a controlled empirical study where the retrieved graph information remains identical, but its textual serialization changes\.

The objective is to determine whether the way graph information is presented to a small language model influences its code understanding, file localization accuracy, token efficiency, and performance under constrained context windows\.

This must be a scientifically controlled experiment, not merely a demonstration of an AI agent\.

---

# 2\. Research Hypothesis

## Primary hypothesis

Different textual serialization formats of the same retrieved code subgraph produce statistically and practically different file\-localization performance in a small Gemma coding agent\.

## Secondary hypotheses

H1: Natural\-language edge descriptions may improve file\-localization accuracy compared with raw JSON and adjacency\-list representations\.

H2: Structured adjacency lists may provide a better balance between token efficiency and localization performance\.

H3: Serialization format may have a stronger effect when the model operates under a restricted token budget\.

H4: The performance difference between serialization formats may vary depending on graph size, node count, and relationship complexity\.

These are hypotheses to test, not conclusions to assume\.

---

# 3\. Experimental Design

Build a controlled experiment with the following three graph serialization formats\.

The three formats must represent the same underlying retrieved graph\.

## Format A: Raw JSON

Represent retrieved graph information as compact JSON\.

Example:

```json
{
  "nodes": [
    {
      "id": "n1",
      "name": "PaymentService",
      "file": "src/payment.py",
      "line": 20
    },
    {
      "id": "n2",
      "name": "InvoiceValidator",
      "file": "src/validator.py",
      "line": 45
    }
  ],
  "edges": [
    {
      "source": "n1",
      "target": "n2",
      "type": "calls"
    }
  ]
}
```

## Format B: Adjacency List

Represent the same information in a compact graph structure\.

Example:

```text
PaymentService [src/payment.py:20]
  -> calls -> InvoiceValidator [src/validator.py:45]

InvoiceValidator [src/validator.py:45]
```

## Format C: Natural Language Edge Sentences

Represent the same graph information as readable relationship statements\.

Example:

```text
PaymentService is defined in src/payment.py at line 20.
PaymentService calls InvoiceValidator.
InvoiceValidator is defined in src/validator.py at line 45.
```

**IMPORTANT:** All three formats must contain exactly the same underlying retrieved nodes, edges, node metadata, and relationships\. Only the serialization format is allowed to change\.

---

# 4\. Model Requirements

Use Gemma 4 E2B as the primary model\.

Preferred implementation:

- Model: Gemma 4 E2B
- Model format: GGUF
- Inference: llama\-cpp\-python
- Python integration: Local model inference
- Temperature: 0 for deterministic primary experiments
- Output: Strict JSON
- Model execution: CPU or GPU depending on available hardware

Model loading must be configurable\. Do not hardcode a model path\.

Support configuration through YAML or environment variables\.

The project must clearly report:

- Model name
- Model file
- Model quantization
- Context window
- GPU/CPU configuration
- Inference settings

If the model is unavailable, allow the rest of the pipeline to run in a validation or mock mode\. Clearly label mock results and never treat them as real experimental results\.

Do not silently substitute another model\.

---

# 5\. Dataset Integration

Build the project to support the competition dataset\.

The expected logical data structure is:

## Tasks

- `instance_id`
- `repo`
- `base_commit`
- `problem_statement`
- `hints_text`
- `patch`
- `test_patch`
- `created_at`

## Graph Nodes

- `id`
- `name`
- `text`
- `file`
- `line`

## Graph Edges

- `source`
- `target`
- `type`
- optional `key`

## Embeddings

- Node ID
- Corresponding 256\-dimensional embedding vector

**IMPORTANT:** These are expected logical fields, not guaranteed physical file formats\.

First inspect the actual dataset files and their schemas\. Do not assume the files are JSON, JSONL, CSV, NPZ, Parquet, or any other format until you inspect them\.

Build flexible dataset loaders and schema adapters\.

If a required dataset is missing:

1. Identify the missing file\.
2. Explain the expected schema\.
3. Create a small synthetic fixture only for software testing\.
4. Keep synthetic data separate from the real research dataset\.
5. Never mix synthetic and real experimental results\.

Create a dataset inspection command that reports:

- Available files
- File formats
- Record counts
- Field names
- Missing values
- Graph node counts
- Graph edge counts
- Embedding dimensions
- Number of valid tasks

---

# 6\. Retrieval Pipeline

Implement a consistent graph retrieval pipeline\.

The retrieval system should operate independently of the serialization format\.

## Step 1: Query processing

Input:

- Software engineering problem statement
- Optional hints
- Repository information

Extract relevant identifiers and technical terms\.

Use lexical matching to identify initial graph nodes\.

## Step 2: Graph seed selection

Find candidate seed nodes using:

- Exact identifier matching
- Partial identifier matching
- Filename matching
- Keyword matching

Keep the process deterministic\.

## Step 3: Graph expansion

Expand from the seed nodes using graph relationships\.

Support configurable graph expansion depth\.

Default maximum depth: 2 hops\.

Preserve relevant edge types and relationships\.

## Step 4: Embedding\-based expansion

Use the provided node embeddings\.

Important methodological constraint: Do not directly compare the issue description with the node embeddings unless a compatible query encoder is available\.

Instead:

1. Identify lexical seed nodes\.
2. Retrieve their corresponding embeddings\.
3. Calculate cosine similarity between seed\-node embeddings and other node embeddings\.
4. Add the most similar nodes subject to the configured limits\.

Document this limitation in the research protocol\.

## Step 5: Candidate graph construction

Create one canonical retrieved subgraph\.

This subgraph must be shared by all three serialization methods\.

Save:

- Retrieved node IDs
- Retrieved edge IDs or edge records
- Candidate file paths
- Retrieval configuration
- Candidate coverage

The serialization modules must not independently retrieve nodes\.

---

# 7\. Baselines

Implement the following baselines\.

## Baseline 1: No Graph

Give the model only the problem statement and repository context\. No graph information should be included\.

## Baseline 2: Keyword Match

Use lexical matching to identify relevant files and provide the resulting candidate file list to the model\.

## Experimental Conditions

- Graph \+ Raw JSON
- Graph \+ Adjacency List
- Graph \+ Natural Language

All conditions must use the same task set, retrieval results, candidate paths, model, decoding configuration, and evaluation procedure\.

---

# 8\. Token Budget Experiment

Test the effect of serialization under multiple context budgets\.

Use configurable budgets\.

Default experimental budgets:

- 512 tokens
- 1,024 tokens
- 2,048 tokens
- 4,096 tokens

If a budget is incompatible with the model’s actual context configuration, report the limitation and adjust the experiment transparently\.

Implement token\-aware graph serialization\.

Requirements:

1. Use the actual Gemma GGUF tokenizer for measuring serialized prompt tokens\.
2. Include the fixed prompt and task description when measuring total prompt size\.
3. Apply the same node inclusion policy to all serialization formats\.
4. Never truncate a JSON object or graph relationship in the middle\.
5. Include only complete nodes and edges\.
6. Record the number of included nodes and edges\.
7. Record token consumption per task and serialization format\.
8. Report when the retrieved subgraph cannot fit within the available budget\.

Do not assume that equal node counts automatically mean equal token consumption\. Token consumption is itself an experimental variable\.

---

# 9\. Prompt Engineering

Use a common base prompt for all experimental conditions\.

The model’s task is file localization, not code modification\.

It must identify the most likely source files relevant to the given issue\.

The model must not receive the gold patch or gold file paths\.

Expected model output:

```json
{
  "predicted_files": [
    "src/payment.py",
    "src/validator.py"
  ],
  "reasoning": "Brief explanation based only on the provided evidence."
}
```

Requirements:

- Strict JSON output
- No Markdown fences
- No additional text outside JSON
- Maximum configurable number of predicted files
- Robust JSON parsing
- Retry handling for invalid output
- Record raw model output
- Record parsing failures

Do not let the model access evaluation labels\.

Keep the base instructions identical across all three serialization conditions\.

Only the graph representation should differ\.

---

# 10\. Gold Label Generation

Use the ground\-truth patch field only during evaluation\.

Extract modified source file paths from unified diff headers\.

Support:

- `diff --git` headers
- `---` and `+++` headers
- `a/` and `b/` prefixes
- `/dev/null` entries
- Renamed or deleted files where identifiable

Normalize file paths before comparing predictions\.

Exclude test\-only paths from the source\-file localization target unless the research protocol explicitly defines otherwise\.

Avoid using the patch to construct retrieval inputs or model prompts\.

Document the gold\-label extraction method\.

Add tests for patch parsing and path normalization\.

---

# 11\. Evaluation Metrics

Implement the following metrics\.

## Primary metrics

### Accuracy@1

Whether the top predicted file matches any gold file\.

### Accuracy@5

Whether any of the top five predicted files matches a gold file\.

### Mean Reciprocal Rank@5

For each task, calculate the reciprocal rank of the first correct prediction within the first five results\. If no correct prediction is found, the score is zero\.

## Secondary metrics

- Candidate Coverage
- Token Consumption
- Number of Retrieved Nodes
- Number of Retrieved Edges
- Number of Candidate Files
- Inference Latency
- Parsing Failure Rate
- Accuracy per token budget

**Important:** Candidate coverage must be reported separately from model localization performance\.

If the correct file is missing from the retrieved candidate set, that is a retrieval failure, not a serialization failure\.

Report both:

1. End\-to\-end localization performance\.
2. Performance conditional on the gold file being present in the candidate set\.

Clearly define all metrics in the documentation and research paper\.

---

# 12\. Statistical Analysis

Implement a statistically responsible analysis pipeline\.

Compare the three serialization methods using paired task\-level results\.

Include:

- Mean metric values
- Median metric values
- Standard deviation
- Confidence intervals
- Paired bootstrap confidence intervals
- Appropriate paired significance tests
- Effect sizes where appropriate

Use task\-level paired comparisons rather than treating individual predictions as independent samples\.

If using multiple seeds, report them separately and explain the source of variation\.

Do not describe repeated temperature\-zero runs as independent replications\.

Report sample sizes and missing observations\.

Do not claim statistical significance without appropriate evidence\.

---

# 13\. Ablation Studies

Implement the following optional ablations\.

## Ablation A: Graph expansion depth

Compare:

- 0 hops
- 1 hop
- 2 hops

## Ablation B: Embedding expansion

Compare:

- Lexical retrieval only
- Lexical \+ embedding expansion

## Ablation C: Graph size

Compare performance across different retrieved subgraph sizes\.

## Ablation D: Token budget

Compare the three serialization formats under restricted and larger budgets\.

These experiments must be independently configurable\.

Do not introduce unnecessary variables into the primary experiment\. The primary experiment must remain the controlled comparison of three serialization formats\.

---

# 14\. Software Architecture

Create a modular, maintainable Python project\.

Recommended structure:

```text
graphtrust/
│
├── README.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── configs/
│   ├── default.yaml
│   ├── model.yaml
│   └── experiment.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
│
├── models/
│
├── outputs/
│   ├── predictions/
│   ├── metrics/
│   ├── logs/
│   └── figures/
│
├── notebooks/
│   ├── 01_dataset_inspection.ipynb
│   ├── 02_retrieval_analysis.ipynb
│   ├── 03_experiment_analysis.ipynb
│   └── 04_visualization.ipynb
│
├── src/
│   └── graphtrust/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── data.py
│       ├── schema.py
│       ├── graph_builder.py
│       ├── retrieval.py
│       ├── serializers.py
│       ├── token_budget.py
│       ├── prompting.py
│       ├── model.py
│       ├── evaluation.py
│       ├── statistics.py
│       ├── experiment.py
│       ├── ablation.py
│       └── visualization.py
│
├── tests/
│   ├── test_data.py
│   ├── test_retrieval.py
│   ├── test_serializers.py
│   ├── test_token_budget.py
│   ├── test_evaluation.py
│   └── test_experiment.py
│
└── docs/
    ├── RESEARCH_PROTOCOL.md
    ├── DATA_SCHEMA.md
    ├── EXPERIMENT_DESIGN.md
    ├── REPRODUCIBILITY.md
    └── PAPER_TEMPLATE.md
```

You may improve the architecture if needed, but preserve modularity and separation of responsibilities\.

---

# 15\. Implementation Requirements

Use Python 3\.11 or a compatible version\.

Recommended libraries:

- pandas
- numpy
- networkx
- scipy
- scikit\-learn
- llama\-cpp\-python
- pydantic
- pyyaml
- matplotlib
- seaborn
- pytest
- tqdm

Use type hints\. Use meaningful function names\. Add docstrings to public functions\. Use structured logging\. Keep configuration outside source code\. Avoid unnecessary dependencies\. Make all important paths configurable\.

Make the project installable in editable mode\.

Provide CLI commands\.

Suggested commands:

```bash
python -m graphtrust inspect --data-dir data/raw

python -m graphtrust validate --config configs/default.yaml

python -m graphtrust run --config configs/default.yaml --limit 3

python -m graphtrust run --config configs/default.yaml

python -m graphtrust analyze --results-dir outputs

python -m graphtrust ablate --config configs/experiment.yaml
```

Adjust the CLI implementation as needed, but provide equivalent functionality\.

---

# 16\. Research Visualizations

Generate publication\-quality figures\.

Required figures:

1. Experimental pipeline architecture\.
2. Dataset composition\.
3. Graph retrieval statistics\.
4. Accuracy@1 by serialization format\.
5. Accuracy@5 by serialization format\.
6. MRR@5 by serialization format\.
7. Token consumption comparison\.
8. Performance versus token budget\.
9. Candidate coverage versus end\-to\-end accuracy\.
10. Ablation study results\.

Use clear labels, readable fonts, legends, and consistent formatting\.

Save figures as PNG and PDF\.

Do not generate misleading visualizations from synthetic or incomplete data\.

---

# 17\. Research Paper Preparation

Create a complete paper template with the following sections:

1. Abstract
2. Introduction
3. Motivation
4. Research Questions
5. Related Work
6. Methodology
7. Dataset
8. Graph Retrieval
9. Serialization Methods
10. Experimental Setup
11. Evaluation Metrics
12. Results
13. Statistical Analysis
14. Ablation Studies
15. Discussion
16. Threats to Validity
17. Limitations
18. Conclusion
19. References

The research paper must distinguish between:

- Planned experiments
- Completed experiments
- Actual observations
- Hypothesis interpretations

Do not write fabricated results\. Use placeholders when experiments have not yet been executed\.

Include limitations such as:

- Dependence on retrieval quality
- Dataset coverage
- Model\-specific behavior
- Tokenizer\-specific effects
- Potential prompt sensitivity
- Limited generalizability from a single model
- Missing query encoder for direct issue\-to\-node embedding retrieval

Explain why holding the retrieved subgraph constant is essential for isolating serialization effects\.

---

# 18\. Reproducibility

Every experiment must save:

- Configuration snapshot
- Dataset identifier/version
- Model identifier
- Model quantization
- Random seed
- Retrieval parameters
- Serialization format
- Token budget
- Prompt version
- Raw model output
- Parsed predictions
- Gold labels
- Evaluation metrics
- Execution time
- Software versions

Use unique experiment IDs\.

Support resuming interrupted experiments\.

Do not overwrite completed experiment outputs\.

Ensure that the same task set is used across comparison groups\.

---

# 19\. Testing Requirements

Write unit tests for:

- Dataset loading
- Schema validation
- Graph construction
- Lexical retrieval
- Graph expansion
- Embedding similarity
- JSON serialization
- Adjacency\-list serialization
- Natural\-language serialization
- Candidate consistency across formats
- Token\-budget enforcement
- Patch path extraction
- Accuracy@1
- Accuracy@5
- MRR@5
- Candidate coverage
- Statistical comparisons

Especially test this invariant:

For a given task and retrieval configuration, all three serialization formats must represent exactly the same underlying nodes and edges\.

Test that serialization does not modify or omit graph relationships except when a documented token\-budget constraint applies\.

Run the full test suite and fix failures\.

---

# 20\. Execution Strategy

Work in phases\.

## Phase 1 — Workspace inspection

- Inspect all existing files\.
- Read `PROJECT.md` if present\.
- Identify the available competition dataset\.
- Identify the available Gemma model\.
- Inspect the current Python environment\.
- Check CPU, RAM, GPU, and disk availability\.
- Identify missing prerequisites\.

Do not overwrite existing project files without understanding their purpose\.

## Phase 2 — Research specification

Create:

- `RESEARCH_PROTOCOL.md`
- `EXPERIMENT_DESIGN.md`
- `DATA_SCHEMA.md`

Explain the controlled variables, independent variable, dependent variables, and potential confounders\.

## Phase 3 — Dataset integration

- Implement actual dataset loaders\.
- Inspect real data\.
- Validate schemas\.
- Report data quality\.
- Create small synthetic fixtures only for testing\.

## Phase 4 — Core implementation

Implement:

- Graph construction
- Retrieval
- Three serializers
- Token budgeting
- Prompting
- Model integration
- Gold label extraction
- Evaluation

## Phase 5 — Testing

- Run unit tests\.
- Fix errors\.
- Validate retrieval consistency\.
- Validate token accounting\.
- Validate evaluation metrics\.

## Phase 6 — Smoke experiment

Run a small experiment on three real tasks if the real dataset and model are available\.

If they are not available, run only software validation with synthetic fixtures and clearly label it\.

Inspect the output manually\.

## Phase 7 — Pilot experiment

Run a configurable small pilot\.

Check:

- Model response quality
- Token\-budget compliance
- Runtime
- Parsing success
- Candidate coverage
- Output reproducibility

Do not proceed to the full experiment if the pilot exposes unresolved methodological or software problems\.

## Phase 8 — Full experiment

Run the full controlled experiment across all three formats and configured token budgets\.

Save all task\-level predictions and metrics\.

## Phase 9 — Statistical analysis

Generate comparisons, confidence intervals, significance tests, and visualizations\.

## Phase 10 — Paper preparation

Populate the paper using actual experimental outputs\.

Do not fabricate findings\.

---

# 21\. Critical Research Integrity Rules

These rules are mandatory\.

1. Never fabricate experimental results\.
2. Never use gold patch information in model prompts\.
3. Never change graph retrieval between serialization formats\.
4. Never compare different candidate subgraphs as if serialization were the only variable\.
5. Never silently change models\.
6. Never silently change tokenizer behavior\.
7. Never report synthetic experiments as real dataset experiments\.
8. Never claim a hypothesis is proven based on insufficient evidence\.
9. Record all failed tasks and parsing errors\.
10. Report candidate coverage separately\.
11. Keep primary experiments separate from ablations\.
12. Make the project reproducible from documented instructions\.

If an assumption is necessary, document it rather than hiding it\.

If a methodological flaw is discovered, explain it and propose a correction before continuing\.

---

# 22\. Final Deliverables

At completion, produce:

## Software

- Complete working Python project
- Modular source code
- Configuration files
- CLI
- Unit tests
- Requirements and installation instructions

## Research

- Research protocol
- Experimental design
- Dataset inspection report
- Reproducibility documentation
- Results CSV files
- Task\-level predictions
- Statistical analysis
- Research visualizations
- Paper draft

## Demonstration

- A reproducible three\-task smoke test
- Example input and output
- Example of all three graph serialization formats
- Demonstration of token\-budget enforcement
- Comparison of predictions across formats

## Final report

Create `FINAL_REPORT.md` containing:

1. What was implemented
2. Dataset inspected
3. Model used
4. Experiments executed
5. Tests passed and failed
6. Results generated
7. Known limitations
8. Outstanding work
9. Exact commands to reproduce the experiment

---

# 23\. How You Must Work as an Agent

Follow these operating instructions throughout development\.

- Start by inspecting the workspace\.
- Do not ask me questions that can be answered by inspecting the files\.
- Make reasonable engineering decisions and document them\.
- Build the project incrementally\.
- Execute code rather than assuming it works\.
- Fix errors before moving to the next phase\.
- Do not stop after creating the folder structure\.
- Do not stop after generating code\.
- Do not claim completion without executing tests\.
- Keep me informed about major architectural decisions\.
- If an external dataset or model download is required, give me the exact source and setup instructions\.
- If a long\-running experiment is impractical in the current environment, implement the pipeline and explain how to execute it in Kaggle or a suitable GPU environment\.
- Prioritize scientific validity over adding unnecessary features\.

## First Action

Inspect the current workspace and any existing `PROJECT.md` file\.

Then produce a concise implementation plan identifying:

1. What is already available\.
2. What is missing\.
3. The proposed architecture\.
4. The main technical risks\.
5. The first implementation milestone\.

After presenting the plan, proceed with implementation phase by phase\.

**Final objective: Deliver a technically sound, reproducible, empirically validated research project—not just a prototype or a collection of Python files\.**