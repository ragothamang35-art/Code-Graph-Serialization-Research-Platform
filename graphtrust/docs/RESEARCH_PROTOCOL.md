# GraphTrust Research Protocol

## Project Identity
- **Research Paper Title**: Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?
- **Domain**: AI Agents / Code Intelligence / Graph-Augmented Retrieval / Empirical Evaluation
- **Target Model**: Gemma 4 E2B (GGUF, 4-bit quantized) / Controlled Deterministic Inference ($T = 0.0$)

## Core Research Question
Does the textual representation of an identical retrieved code graph affect the ability of a small Gemma coding agent to localize relevant source files when solving software engineering issues?

## Experimental Invariant
For every evaluated task, the retrieved candidate code subgraph is generated **exactly once** using a deterministic 5-step retrieval pipeline. This identical set of nodes, edges, file metadata, and relationships is preserved across all experimental conditions:
1. **Format A: Raw JSON** (compact structural syntax)
2. **Format B: Structured Adjacency List** (compact graph edge blocks)
3. **Format C: Natural Language Sentences** (explicit linguistic relationship statements)

## Hypotheses
- **H1**: Natural language edge statements improve small model file localization accuracy by converting graph relations into fluent linguistic context.
- **H2**: Adjacency lists yield optimal token efficiency, minimizing boilerplate overhead while preserving relationship clarity.
- **H3**: Serialization differences widen significantly under constrained token budgets (512 vs 4096 tokens).
- **H4**: Performance varies with graph diameter and relationship density.

## Separation of Failure Modes
Candidate coverage (whether the gold modified file exists in the retrieved candidate set) is tracked independently from localization accuracy. A retrieval failure cannot be misattributed to serialization quality.
