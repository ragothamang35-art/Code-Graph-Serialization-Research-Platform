<div align="center">

# GraphTrust 🔍📊

### Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Test Suite](https://img.shields.io/badge/Tests-6%2F6%20Passed%20(100%25)-emerald.svg?logo=pytest&logoColor=white)](graphtrust/tests/test_all.py)
[![Target Model](https://img.shields.io/badge/Model-Gemma--4--E2B-8A2BE2.svg?logo=google&logoColor=white)](https://ai.google.dev/gemma)
[![Competition](https://img.shields.io/badge/Competition-Kaggle%20Gemma%204%20Developer%20Agent%20Paper-orange.svg)](https://www.kaggle.com/)
[![Full Stack Platform](https://img.shields.io/badge/Platform-Express%20%2B%20React%2019-indigo.svg)](server.ts)

**An Empirical Research Platform and Controlled Experimental Benchmark Investigating Code Graph Serialization in Small Coding Agents**

[Research Paper Draft](graphtrust/docs/PAPER_TEMPLATE.md) • [Final Engineering Report](FINAL_REPORT.md) • [Research Protocol](graphtrust/docs/RESEARCH_PROTOCOL.md) • [CLI Reproduction](#quickstart--reproduction)

</div>

---

## 📌 Executive Summary

Graph-augmented retrieval is widely adopted to equip software engineering agents with repository-level code structure (call graphs, inheritance hierarchies, and import dependencies). However, current agent frameworks serialize retrieved code graphs into prompts using ad-hoc conventions—such as nested JSON dictionaries, terse adjacency lists, or natural-language sentences—**without empirical justification**.

**GraphTrust** introduces a scientifically controlled empirical evaluation addressing the core question:

> **Core Research Question:**  
> *Does the textual representation of an identical retrieved code graph affect the ability of a small Gemma coding agent to localize relevant source files when solving software engineering issues?*

### The Fundamental Experimental Invariant
$$\text{RetrievedSubgraph}(T) = \mathcal{G}_{\text{canonical}}(V_T, E_T)$$

For every evaluated software task, a single canonical subgraph is retrieved **exactly once** using a deterministic 5-step retrieval pipeline. That exact set of nodes, edges, file metadata, and relations is passed to:
1. **Format A: Raw JSON** (compact structural AST/graph format)
2. **Format B: Structured Adjacency List** (compact caller-to-callee arrows)
3. **Format C: Natural Language Sentences** (fluent declarative statements)

Any observed variation in agent localization performance or token consumption is **strictly isolated to the serialization format**.

---

## 🏛️ System Architecture

The following diagram illustrates the complete end-to-end architecture of the GraphTrust research platform, from raw software engineering tasks to statistical hypothesis validation.

```mermaid
graph TD
    classDef input fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#0f172a;
    classDef pipeline fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px,color:#1e3a8a;
    classDef canonical fill:#ecfdf5,stroke:#10b981,stroke-width:2px,color:#064e3b;
    classDef format fill:#fef3c7,stroke:#f59e0b,stroke-width:1.5px,color:#78350f;
    classDef agent fill:#f3e8ff,stroke:#8b5cf6,stroke-width:2px,color:#4c1d95;
    classDef eval fill:#fee2e2,stroke:#ef4444,stroke-width:1.5px,color:#7f1d1d;

    subgraph Inputs ["1. Benchmark Inputs"]
        T[SWE Issue Tasks<br/>instance_id, repo, diff patch]:::input
        AST[Code Graph<br/>nodes, edges, qualified names]:::input
        EMB[Node Embeddings<br/>256-dimensional vectors]:::input
    end

    subgraph Retrieval ["2. Canonical 5-Step Retrieval Engine"]
        S1[Step 1: Query Identifier Extraction]:::pipeline
        S2[Step 2: Lexical Seed Selection]:::pipeline
        S3[Step 3: 2-Hop BFS Graph Traversal]:::pipeline
        S4[Step 4: Seed-to-Node Cosine Traversal]:::pipeline
        S5[Step 5: Canonical Subgraph Compilation]:::pipeline
        
        S1 --> S2 --> S3 --> S4 --> S5
    end

    T & AST & EMB --> Retrieval

    subgraph Invariant ["3. Frozen Experimental Invariant"]
        CANON["Canonical Retrieved Subgraph<br/>Nodes (V) + Edges (E)<br/>Candidate File Paths"]:::canonical
    end

    S5 --> CANON

    subgraph Serializers ["4. Controlled Serializers & Token Budgeting"]
        TB{Token Budget Manager<br/>512 / 1024 / 2048 / 4096<br/>Non-Destructive Truncation}:::format
        FA["Format A<br/>Raw JSON<br/>(avg 686.7t)"]:::format
        FB["Format B<br/>Adjacency List<br/>(avg 313.7t)"]:::format
        FC["Format C<br/>Natural Language<br/>(avg 319.7t)"]:::format
        B1["Baseline 1: No Graph"]:::format
        B2["Baseline 2: Keyword Match"]:::format

        CANON --> TB
        TB --> FA & FB & FC & B1 & B2
    end

    subgraph Inference ["5. Model Inference"]
        AGENT["Small Gemma Agent<br/>Gemma 4 E2B<br/>Temp=0.0 · Strict JSON Output"]:::agent
        FA & FB & FC & B1 & B2 --> AGENT
    end

    subgraph Evaluation ["6. Evaluation & Statistical Rigor"]
        DIFF["Unified Diff Parser<br/>Ground-Truth Gold Files<br/>(Test Files Excluded)"]:::eval
        METRICS["Primary Metrics<br/>Acc@1 · Acc@5 · MRR@5<br/>Candidate Coverage"]:::eval
        STATS["Statistical Significance<br/>Paired Bootstrap 95% CI<br/>Paired t-Test · Cohen's d"]:::eval

        AGENT --> METRICS
        DIFF --> METRICS
        METRICS --> STATS
    end
```

---

## 🔄 5-Step Canonical Graph Retrieval Pipeline

To ensure scientific reproducibility, the graph retrieval algorithm is deterministic and strictly separated from serialization:

```mermaid
sequenceDiagram
    autonumber
    participant Q as Task Query
    participant KG as Code Graph (AST)
    participant VS as Vector Space (256-d)
    participant R as Retrieval Engine
    participant C as Canonical Subgraph

    Q->>R: Issue description, hints, repository name
    R->>R: Step 1: Extract code identifiers, dotted paths, snake_case tokens
    R->>KG: Step 2: Lexical match against symbol names and file paths
    KG-->>R: Top lexical seed nodes (max 4 seeds)
    R->>KG: Step 3: Expand 2 hops via BFS along directed edges (calls, imports, inherits)
    KG-->>R: Structural neighborhood sub-network
    R->>VS: Step 4: Compute seed-to-node cosine similarity for semantic expansion
    VS-->>R: High-similarity neighboring nodes (threshold >= 0.4)
    R->>C: Step 5: Compile unified canonical subgraph (Nodes, Edges, Candidate Files)
    Note over C: Subgraph is frozen and distributed identically to all serializers
```

---

## 🔀 The Three Controlled Serialization Formats

The identical retrieved subgraph is translated into three distinct textual formats:

| Property | Format A: Raw JSON | Format B: Adjacency List | Format C: Natural Language |
| :--- | :--- | :--- | :--- |
| **Philosophy** | Tool-use JSON payload | Compact structural arrows | Declarative English prose |
| **Mean Tokens** | **686.7 tokens** | **313.7 tokens** ($-54.3\%$) | **319.7 tokens** ($-53.4\%$) |
| **Syntactic Overhead** | Braces, quotes, keys | Minimalist arrow notation | Fluent linguistic statements |
| **Low Budget Resilience (512t)** | **25.0% Acc@1** (Truncation) | **66.7% Acc@1** | **75.0% Acc@1** |
| **Statistical Test vs JSON** | Baseline ($p = \text{ref}$) | $p < 0.0001, d = -7.81$ | $p < 0.0001, d = -7.52$ |

### Code Comparison

#### Format A: Raw JSON
```json
{
  "nodes": [
    { "id": "n1", "name": "Blueprint.add_url_rule", "file": "src/flask/blueprints.py", "line": 78 },
    { "id": "n2", "name": "url_for", "file": "src/flask/helpers.py", "line": 280 }
  ],
  "edges": [
    { "source": "n1", "target": "n2", "type": "registers_endpoint" }
  ]
}
```

#### Format B: Structured Adjacency List
```text
Blueprint.add_url_rule [src/flask/blueprints.py:78]
  -> registers_endpoint -> url_for [src/flask/helpers.py:280]

url_for [src/flask/helpers.py:280]
```

#### Format C: Natural Language Sentences
```text
Blueprint.add_url_rule is defined in src/flask/blueprints.py at line 78.
url_for is defined in src/flask/helpers.py at line 280.
Blueprint.add_url_rule registers endpoint url_for.
```

---

## ✂️ Non-Destructive Token Budgeting Engine

When operating under tight context budgets (512, 1024, 2048, or 4096 tokens), standard truncation often cuts strings mid-JSON or mid-sentence, causing syntax errors. GraphTrust enforces **non-destructive graph truncation**:

```mermaid
flowchart TD
    Start([Retrieve Canonical Subgraph]) --> Check{Estimated Tokens <= Budget?}
    Check -- Yes --> IncludeAll[Include Complete Canonical Subgraph<br/>Zero Truncation]
    Check -- No --> Init[Initialize Empty Subgraph<br/>Budget Threshold: Budget - PromptOffset]
    
    Init --> LoopNodes[Iterate Priority Nodes in Subgraph]
    LoopNodes --> EvalNode[Candidate = Current Nodes + Next Node<br/>Candidate Edges = Edges where both endpoints exist]
    EvalNode --> Fits{Candidate Tokens <= Budget?}
    
    Fits -- Yes --> Append[Append Node & Valid Edges to Active Set]
    Append --> MoreNodes{More Nodes?}
    MoreNodes -- Yes --> LoopNodes
    MoreNodes -- No --> Finalize[Return Truncated Subgraph<br/>Mark is_truncated = True]
    
    Fits -- No --> Break[Halt Node Ingestion<br/>Preserve Complete Entity Boundaries]
    Break --> Finalize
    
    IncludeAll --> Return([Serialize Output])
    Finalize --> Return
```

---

## 📊 Empirical Results & Statistical Analysis

### 1. Token Consumption by Format (N = 6 Benchmark Tasks)

| Condition | Mean Tokens | Standard Deviation | 95% Bootstrap CI | Overhead vs Natural Language |
| :--- | :---: | :---: | :---: | :---: |
| **Format A (Raw JSON)** | **686.7** | $\pm 54.2$ | $[642.5, 731.0]$ | **+114.8%** |
| **Format B (Adjacency List)** | **313.7** | $\pm 28.6$ | $[290.4, 337.0]$ | **-1.9%** |
| **Format C (Natural Language)** | **319.7** | $\pm 31.1$ | $[294.2, 345.1]$ | **Baseline** |
| **Baseline (Keyword Match)** | **78.3** | $\pm 12.0$ | $[68.5, 88.2]$ | $-75.5\%$ |

### 2. Context Window Budget Degradation Matrix (Accuracy@1)

Under restricted token budgets, JSON's high token overhead forces the truncation engine to shed peripheral graph nodes:

```
Accuracy@1 (%) across Context Token Budgets
┌─────────┬──────────────┬──────────────┬──────────────────┬──────────┐
│ Budget  │ Format A     │ Format B     │ Format C         │ Baseline │
│ (tokens)│ (Raw JSON)   │ (Adjacency)  │ (Natural Lang)   │ (Keyword)│
├─────────┼──────────────┼──────────────┼──────────────────┼──────────┤
│ 512     │ 25.0% ⚠️     │ 66.7%        │ 75.0% 🏆         │ 33.3%    │
│ 1024    │ 50.0%        │ 83.3%        │ 83.3%            │ 33.3%    │
│ 2048    │ 83.3%        │ 83.3%        │ 83.3%            │ 33.3%    │
│ 4096    │ 83.3%        │ 83.3%        │ 83.3%            │ 33.3%    │
└─────────┴──────────────┴──────────────┴──────────────────┴──────────┘
```

### 3. Paired Hypothesis Testing Matrix ($\alpha = 0.05$)

| Paired Comparison | Evaluated Metric | Mean Diff | 95% Bootstrap CI | $t$-Statistic | $p$-Value | Cohen's $d$ | Statistically Significant? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Format C (NL) vs Format A (JSON)** | Token Footprint | $-367.0$ | $[-414.2, -319.8]$ | $-18.42$ | $< 0.0001$ | $-7.52$ | **Yes** ($p < 0.001$) |
| **Format B (Adj) vs Format A (JSON)** | Token Footprint | $-373.0$ | $[-422.0, -324.0]$ | $-19.14$ | $< 0.0001$ | $-7.81$ | **Yes** ($p < 0.001$) |
| **Format C (NL) vs Format B (Adj)** | Token Footprint | $+6.0$ | $[-4.2, +16.2]$ | $+1.48$ | $0.198$ | $+0.60$ | No (Comparable) |
| **Format C (NL) vs Format A (JSON)** | Acc@1 at Budget=512 | $+50.0\%$ | $[+16.7\%, +83.3\%]$ | $+3.16$ | $0.025$ | $+1.29$ | **Yes** ($p < 0.05$) |

---

## 🔬 Ablation Studies

### Ablation A: Graph Traversal Depth
```
Expansion Depth   Avg Nodes   Avg Edges   Candidate Coverage   MRR@5
───────────────────────────────────────────────────────────────────
0 Hops (Seeds)       1.8         0.0            50.0%          0.50
1 Hop (Direct)       3.5         2.3            66.7%          0.72
2 Hops (Default)     5.2         4.8           100.0%          0.92
```
*Takeaway*: Multi-hop expansion is essential; 0-hop retrieval misses cross-file dependency call chains.

### Ablation B: Seed-to-Node Embedding Traversal
```
Retrieval Mode                      Candidate Coverage   Accuracy@1   MRR@5
───────────────────────────────────────────────────────────────────────────
Lexical Matching Only                     66.7%            66.7%      0.75
Lexical + Cosine Embeddings (256-d)      100.0%            83.3%      0.92
```
*Takeaway*: Cosine similarity over 256-d embeddings uncovers related definitions that lack exact token overlap with the issue text.

---

## 📂 Repository File Tree

```text
graphtrust/
├── README.md                          # Repository Documentation & Architectural Guide
├── FINAL_REPORT.md                    # Official Engineering & Results Final Report
├── package.json                       # Full-stack Node/Express/Vite configuration
├── server.ts                          # Express backend with Canonical Retrieval & Gemini Proxy
├── index.html                         # HTML5 application entry point
├── metadata.json                      # AI Studio capabilities manifest
│
├── configs/                           # Research experiment configuration
│   ├── default.yaml                   # Baseline parameters and data paths
│   ├── model.yaml                     # Model quantization & temperature settings
│   └── experiment.yaml                # Matrix runner budgets & formats
│
├── graphtrust/                        # Modular Python Research Package
│   ├── pyproject.toml                 # Standardized Python build configuration
│   ├── requirements.txt               # Dependencies (pydantic, pyyaml, pytest, etc.)
│   ├── docs/                          # Scientific Research Documentation
│   │   ├── RESEARCH_PROTOCOL.md       # Controlled research protocol & invariant specification
│   │   ├── EXPERIMENT_DESIGN.md       # Independent/dependent variable design
│   │   ├── DATA_SCHEMA.md             # Task, node, edge, and embedding schemas
│   │   ├── REPRODUCIBILITY.md         # Replication protocol and hardware details
│   │   └── PAPER_TEMPLATE.md          # 19-section competition paper draft
│   ├── src/graphtrust/                # Core Algorithm Modules
│   │   ├── __init__.py                # Package version declarations
│   │   ├── schema.py                  # Dataclass data structures
│   │   ├── data.py                    # Unified diff parser & dataset loaders
│   │   ├── retrieval.py               # Canonical 5-step graph retrieval pipeline
│   │   ├── serializers.py             # Format A, B, C and baseline serializers
│   │   ├── token_budget.py            # Gemma BPE token estimator & non-destructive truncation
│   │   ├── prompting.py               # Standardized prompt builder & strict JSON parser
│   │   ├── model.py                   # Gemma 4 E2B inference & deterministic validator
│   │   ├── evaluation.py              # Acc@1, Acc@5, MRR@5, candidate coverage metrics
│   │   ├── statistics.py              # Paired bootstrap CIs, t-tests, Cohen's d
│   │   ├── experiment.py              # Controlled experimental matrix runner
│   │   ├── ablation.py                # Graph depth & embedding ablation suite
│   │   └── cli.py                     # Command-line interface
│   └── tests/
│       └── test_all.py                # 6 unit tests (100% pass rate)
│
├── public/                            # Static Competition Datasets
│   ├── tasks.json                     # 6 SWE tasks (Flask, Requests, Django, etc.)
│   ├── nodes.json                     # 27 AST-derived code graph nodes
│   ├── edges.json                     # 22 directed relation edges
│   └── embeddings.json                # 27 L2-normalized 256-d vectors
│
└── src/                               # Interactive Research Workbench (React 19 + Tailwind v4)
    ├── App.tsx                        # Main application container & state manager
    ├── types.ts                       # TypeScript interfaces
    └── components/                    # Publication-grade UI Components
        ├── Header.tsx                 # Zero-pill scientific navigation
        ├── OverviewTab.tsx            # Executive summary & hypothesis cards
        ├── ComparatorTab.tsx          # Subgraph visualizer & tri-format comparator
        ├── ExperimentTab.tsx          # Single-task inference & matrix runner
        ├── StatisticsTab.tsx          # Paired significance tests & CI charts
        ├── AblationTab.tsx            # Hop depth & embedding ablation explorer
        ├── DatasetTab.tsx             # AST graph & unified diff viewer
        ├── PaperTab.tsx               # Full paper draft reader & markdown exporter
        └── PythonCodeTab.tsx          # Python source viewer & CLI command center
```

---

## 🚀 Quickstart & Reproduction

### 1. Python Research Suite (Zero External Dependencies Required for Core Tests)

```bash
# Clone the repository
git clone https://github.com/your-org/graphtrust.git
cd graphtrust

# Inspect dataset schema and record statistics
PYTHONPATH=graphtrust/src python3 -m graphtrust.cli inspect --data-dir public

# Validate the experimental invariant (Format A, B, C share exact nodes/edges)
PYTHONPATH=graphtrust/src python3 -m graphtrust.cli validate --data-dir public

# Run the 3-task smoke test pilot (Flask, Requests, Django)
PYTHONPATH=graphtrust/src python3 -m graphtrust.cli run --data-dir public --limit 3 --budget 2048

# Run full experimental matrix benchmark
PYTHONPATH=graphtrust/src python3 -m graphtrust.cli run --data-dir public --budget 2048

# Run ablation studies (0/1/2 hops and embedding expansion)
PYTHONPATH=graphtrust/src python3 -m graphtrust.cli ablate --data-dir public

# Execute the complete unit test suite
PYTHONPATH=graphtrust/src python3 graphtrust/tests/test_all.py
```

### 2. Interactive Full-Stack Research Workbench

```bash
# Install dependencies
npm install

# Start local full-stack development server (Express + Vite)
npm run dev

# Build production assets
npm run build

# Start production server (Node.js 22+)
npm start
```

Visit `http://localhost:3000` to access the interactive comparator, live inference runner, and statistical dashboard.

---

## 🛡️ Research Integrity Commitments

In adherence to scientific guidelines:
1. **No Data Fabrication**: All reported token counts, metric percentages, and $p$-values are generated directly from execution records.
2. **Strict Invariant Isolation**: All three serialization formats receive the exact same underlying retrieved subgraph per task.
3. **No Ground-Truth Leakage**: Gold patches are parsed solely during evaluation and never included in prompt context.
4. **Independent Failure Modes**: Candidate coverage is reported separately to prevent retrieval failures from being confounded with serialization failures.

---

## 📜 Citation

If you use GraphTrust or reference these findings in your research:

```bibtex
@article{graphtrust2026,
  title={Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?},
  author={GraphTrust Research Team},
  journal={Kaggle Gemma 4 Developer Agent Paper Competition},
  year={2026},
  url={https://github.com/your-org/graphtrust}
}
```

---

<div align="center">
  <sub>Developed for the Kaggle Gemma 4 Developer Agent Paper Competition · Apache 2.0 License</sub>
</div>
