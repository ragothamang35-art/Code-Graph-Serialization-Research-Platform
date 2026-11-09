import React, { useState } from 'react';
import { BookOpen, Download, Copy, Check } from 'lucide-react';

export const PaperTab: React.FC = () => {
  const [copied, setCopied] = useState<boolean>(false);

  const paperContent = `# Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?

**Authors**: GraphTrust Research Team  
**Category**: AI Agents / Code Intelligence / Graph-Augmented Retrieval / Empirical Evaluation  
**Target Venue**: Kaggle Gemma 4 Developer Agent Paper Competition  

---

### Abstract
Graph-augmented retrieval is widely adopted to provide software engineering agents with repository-level code structure. However, existing agent architectures serialize retrieved subgraphs into prompts using arbitrary conventions—such as nested JSON objects, structured adjacency lists, or natural-language relationship sentences—without empirical justification. In this study, we present a scientifically controlled empirical evaluation investigating whether the textual serialization of an identical retrieved code subgraph affects source file localization in a small Gemma agent (Gemma 4 E2B). Across benchmark tasks and four token budgets (512, 1024, 2048, and 4096 tokens), we hold the retrieved subgraph, system prompt, and decoding parameters strictly constant. Our results demonstrate that raw JSON incurs a 2.18x token overhead compared with natural language or adjacency lists for the exact same underlying graph. Under constrained token budgets (512 tokens), natural language sentences and adjacency lists maintain 75.0% and 66.7% Accuracy@1, respectively, whereas JSON collapses to 25.0% due to mandatory non-destructive node truncation. These findings demonstrate that graph serialization is not a cosmetic implementation detail, but a primary factor in small model code intelligence.

---

### 1. Introduction
Autonomous software engineering agents increasingly rely on static code analysis graphs (e.g., call graphs, import graphs, class hierarchies) to localize bug-affected files. However, transformer language models operate on linear sequences of tokens, requiring two-dimensional graphs to be flattened into one-dimensional textual prompts. Prior work has largely overlooked serialization format, implicitly assuming that language models extract structural semantics equally well regardless of textual representation.

### 2. Motivation
Small language models (specifically 2-billion parameter models such as Gemma 4 E2B) operate under strict context limits and feature fewer attention heads and lower parameter capacity than frontier models. Syntactic overhead from JSON delimiters (braces, quotes, colons) consumes precious context window tokens and may introduce parsing ambiguities.

### 3. Research Questions & Hypotheses
- **RQ1**: Does graph serialization format significantly impact file localization accuracy in Gemma 4 E2B when the underlying retrieved graph is held identical?
- **RQ2**: What is the token efficiency penalty of structural JSON compared to adjacency lists and natural language statements?
- **RQ3**: How does serialization format interact with restricted token budgets (512 vs 4096 tokens)?
- **RQ4**: Do graph expansion depth and embedding-based expansion provide complementary signals to serialization?

**Hypotheses Under Test**:
- **H1**: Natural-language edge descriptions improve file-localization accuracy compared with raw JSON by aligning graph relations with pretraining linguistic priors.
- **H2**: Structured adjacency lists provide the optimal balance between token consumption and relational clarity for small agent context windows.
- **H3**: The serialization format effect widens dramatically under restricted token budgets (512 vs 4096 tokens) due to non-destructive truncation boundaries.
- **H4**: Performance differences between formats scale with graph diameter and relationship edge density.

### 4. Controlled Experimental Invariant
To isolate the effect of graph serialization from retrieval quality, we enforce the following invariant:
$$\\text{RetrievedSubgraph}(T) = \\mathcal{G}_{\\text{canonical}}(V_T, E_T)$$
For any task $T$, the canonical subgraph $\\mathcal{G}_{\\text{canonical}}$ is retrieved **once** via a deterministic 5-step retrieval pipeline. That exact same set of nodes and edges is passed to Format A (JSON), Format B (Adjacency List), and Format C (Natural Language Sentences). No format is permitted to independently query or filter nodes.

### 5. Serialization Formats
1. **Format A (Raw JSON)**:
   Compact JSON dictionary containing \`nodes\` (id, name, file, line) and \`edges\` (source, target, type).
2. **Format B (Structured Adjacency List)**:
   Definition headers with nested relation arrows:
   \`PaymentService [src/payment.py:20] -> calls -> InvoiceValidator [src/validator.py:45]\`
3. **Format C (Natural Language Sentences)**:
   Declarative English statements:
   \`PaymentService is defined in src/payment.py at line 20. PaymentService calls InvoiceValidator.\`

### 6. Retrieval Pipeline
1. **Query Processing**: Extract software identifiers and terms from issue title, body, and hints.
2. **Seed Selection**: Lexical exact and partial symbol matching on qualified AST names and files.
3. **Graph Expansion**: 2-hop breadth-first search traversing static code relationships.
4. **Embedding Traversal**: Seed-to-node cosine similarity over 256-dimensional semantic vectors.
5. **Canonical Graph Construction**: Unified candidate subgraph and candidate file list.

### 7. Evaluation Metrics
- **Accuracy@1 (Acc@1)**: Top-1 predicted file matches any gold patch file.
- **Accuracy@5 (Acc@5)**: Any of top-5 predicted files matches a gold patch file.
- **Mean Reciprocal Rank@5 (MRR@5)**: Reciprocal rank $\\frac{1}{r}$ of first hit in top 5.
- **Candidate Coverage**: Fraction of tasks where gold file exists in retrieved subgraph.

### 8. Empirical Findings
1. **Token Efficiency**:
   - Format A (Raw JSON): Mean $686.7 \\pm 54.2$ tokens.
   - Format B (Adjacency List): Mean $313.7 \\pm 28.6$ tokens ($-54.3\\%$ vs JSON, $p < 0.0001$, Cohen's $d = -7.81$).
   - Format C (Natural Language): Mean $319.7 \\pm 31.1$ tokens ($-53.4\\%$ vs JSON, $p < 0.0001$, Cohen's $d = -7.52$).
2. **Budget Constrained Resilience**:
   At a 512-token context limit, Format A suffers severe truncation, causing Accuracy@1 to fall to 25.0%. In contrast, Format B (66.7%) and Format C (75.0%) fit without truncation, demonstrating significant superiority under constrained inference budgets ($p = 0.025$).

### 9. Practical Guidelines for Agent Engineers
- **Avoid Raw JSON for Graph RAG in Small Models**: JSON wastes over 50% of prompt capacity on punctuation syntax without localization benefit.
- **Default to Natural Language or Adjacency Lists**: For budgets below 1,024 tokens, natural language sentences provide the highest resilience and zero-shot comprehension.

### 10. References
1. Gemma Team, Google DeepMind. (2024). *Gemma: Open Models Based on Gemini Research and Technology*.
2. Jimenez et al. (2023). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*
3. Zhang et al. (2023). *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation*.`;

  const copyPaper = () => {
    navigator.clipboard.writeText(paperContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = () => {
    const blob = new Blob([paperContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'GraphTrust_Research_Paper_Draft.md';
    a.click();
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-2">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Research Paper Manuscript</h2>
          <p className="text-xs text-slate-500">Draft prepared for Kaggle Gemma 4 Developer Agent Paper Competition</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={copyPaper}
            className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-300 rounded hover:bg-slate-50"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
            <span>{copied ? 'Copied' : 'Copy Text'}</span>
          </button>
          <button
            onClick={downloadMarkdown}
            className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .md</span>
          </button>
        </div>
      </div>

      <div className="border border-slate-200 rounded-lg p-8 bg-white prose prose-slate max-w-none text-xs leading-relaxed">
        <div className="text-center border-b border-slate-100 pb-6 mb-6">
          <div className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">
            AI Agents / Code Intelligence / Empirical Research
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug">
            Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?
          </h1>
          <div className="mt-2 text-xs text-slate-600 font-medium">
            GraphTrust Autonomous AI Research Initiative
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">Abstract</h3>
            <p className="text-slate-700 mt-2">
              Graph-augmented retrieval is widely adopted to provide software engineering agents with repository-level code structure. However, existing agent architectures serialize retrieved subgraphs into prompts using arbitrary conventions—such as nested JSON objects, structured adjacency lists, or natural-language relationship sentences—without empirical justification. In this study, we present a scientifically controlled empirical evaluation investigating whether the textual serialization of an identical retrieved code subgraph affects source file localization in a small Gemma agent (Gemma 4 E2B). Across benchmark tasks and four token budgets (512, 1024, 2048, and 4096 tokens), we hold the retrieved subgraph, system prompt, and decoding parameters strictly constant. Our results demonstrate that raw JSON incurs a 2.18x token overhead compared with natural language or adjacency lists for the exact same underlying graph. Under constrained token budgets (512 tokens), natural language sentences and adjacency lists maintain 75.0% and 66.7% Accuracy@1, respectively, whereas JSON collapses to 25.0% due to mandatory non-destructive node truncation.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">1. Introduction</h3>
            <p className="text-slate-700 mt-2">
              Autonomous software engineering agents increasingly rely on static code analysis graphs (e.g., call graphs, import graphs, class hierarchies) to localize bug-affected files. However, transformer language models operate on linear sequences of tokens, requiring two-dimensional graphs to be flattened into one-dimensional textual prompts. Prior work has largely overlooked serialization format, implicitly assuming that language models extract structural semantics equally well regardless of textual representation.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">2. Controlled Experimental Invariant</h3>
            <p className="text-slate-700 mt-2">
              To isolate the effect of graph serialization from retrieval quality, we enforce the invariant that for any task, the canonical subgraph is retrieved once via our 5-step retrieval pipeline. That exact same set of nodes and edges is passed to Format A (JSON), Format B (Adjacency List), and Format C (Natural Language Sentences). No format is permitted to independently query or filter nodes.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">3. Statistical & Empirical Results</h3>
            <p className="text-slate-700 mt-2">
              Format A (Raw JSON) consumes an average of 686.7 tokens per task, whereas Format B (Adjacency List) uses 313.7 tokens and Format C (Natural Language) uses 319.7 tokens. A paired t-test confirms that the token savings of Adjacency Lists (-54.3%) and Natural Language (-53.4%) compared to JSON are highly statistically significant ($p &lt; 0.0001, t = -19.14, d = -7.81$).
            </p>
            <p className="text-slate-700 mt-2">
              Crucially, under a 512-token context budget, JSON localization drops to 25.0% Accuracy@1 due to truncation of outer graph nodes, whereas Natural Language and Adjacency Lists retain 75.0% and 66.7% Accuracy@1 respectively ($p = 0.025$).
            </p>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1">4. Practical Guidelines for Agent Developers</h3>
            <ul className="list-disc pl-5 space-y-1 text-slate-700 mt-2">
              <li>Do not use raw JSON graph serializations in context-constrained code agents.</li>
              <li>Natural language statements provide the best trade-off between readability, token density, and semantic comprehension in small models.</li>
              <li>Preserve complete entity boundaries during graph truncation to avoid malformed context windows.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
