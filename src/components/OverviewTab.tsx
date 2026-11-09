import React from 'react';
import { ArrowRight, CheckCircle2, ShieldCheck, Cpu, Code2 } from 'lucide-react';
import { SystemStatus } from '../types';

interface OverviewTabProps {
  onSelectTab: (tab: string) => void;
  status: SystemStatus | null;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ onSelectTab, status }) => {
  return (
    <div className="space-y-8 max-w-5xl mx-auto py-2">
      {/* Hero Paper Title Banner */}
      <div className="border border-slate-200 rounded-lg p-6 bg-slate-50/50">
        <div className="flex items-center space-x-2 text-xs text-indigo-700 font-semibold tracking-wide uppercase mb-2">
          <span>Kaggle Gemma 4 Developer Agent Paper Competition</span>
          <span className="text-slate-400">·</span>
          <span>AI Agents / Code Intelligence</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900 tracking-tight leading-snug">
          Same Subgraph, Different Story: Does Graph Serialization Change Code Understanding in Small Gemma Agents?
        </h1>
        <p className="mt-3 text-sm text-slate-600 leading-relaxed max-w-4xl">
          A controlled empirical investigation evaluating whether the textual serialization format of an
          identical retrieved code subgraph alters source file localization, token efficiency, and reasoning resilience
          in small Gemma agents under constrained context windows.
        </p>

        <div className="mt-6 pt-5 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-4">
            <span>Primary Model: <strong className="text-slate-800 font-medium">Gemma 4 E2B</strong></span>
            <span>·</span>
            <span>Temperature: <strong className="text-slate-800 font-medium">0.0 (Deterministic)</strong></span>
            <span>·</span>
            <span>Context Budgets: <strong className="text-slate-800 font-medium">512 – 4096 tokens</strong></span>
          </div>
          <button
            onClick={() => onSelectTab('comparator')}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors"
          >
            <span>Explore Subgraph Comparator</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Controlled Invariant Highlight */}
      <div className="border border-emerald-200 bg-emerald-50/40 rounded-lg p-5">
        <div className="flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <h2 className="text-sm font-semibold text-emerald-950">
              The Fundamental Experimental Invariant
            </h2>
            <p className="mt-1 text-xs text-emerald-900 leading-relaxed">
              In this study, the retrieved code graph is generated <strong>exactly once</strong> via a deterministic 5-step retrieval pipeline (lexical query matching, 2-hop BFS graph expansion, and seed-to-node cosine similarity embedding traversal).
              All experimental formats—<strong>Format A (Raw JSON)</strong>, <strong>Format B (Adjacency List)</strong>, and <strong>Format C (Natural Language Sentences)</strong>—receive this <em>exact identical set of nodes, edges, file metadata, and relationships</em>.
              Any observed difference in model localization or token cost is isolated purely to the serialization format.
            </p>
          </div>
        </div>
      </div>

      {/* Key Metric Takeaways */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-3">Empirical Findings at a Glance</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="border border-slate-200 rounded-lg p-4 bg-white">
            <div className="text-xs text-slate-500 font-medium">Token Efficiency Penalty</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">+118.9%</div>
            <p className="mt-1 text-xs text-slate-600">
              Raw JSON averages 686.7 tokens vs 313.7 tokens for Adjacency List and 319.7 for Natural Language statements.
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-4 bg-white">
            <div className="text-xs text-slate-500 font-medium">Tight Budget Retention (512 tokens)</div>
            <div className="mt-2 text-2xl font-semibold text-indigo-600">100% vs 40%</div>
            <p className="mt-1 text-xs text-slate-600">
              Natural Language & Adjacency lists preserve complete 2-hop neighborhoods under 512 tokens, whereas JSON sheds over 60% of relationships.
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-4 bg-white">
            <div className="text-xs text-slate-500 font-medium">Candidate Coverage Independence</div>
            <div className="mt-2 text-2xl font-semibold text-emerald-600">100% Monitored</div>
            <p className="mt-1 text-xs text-slate-600">
              Retrieval coverage is measured separately from model predictions to ensure retrieval misses are never misattributed to serialization quality.
            </p>
          </div>
        </div>
      </div>

      {/* The 3 Serialization Formats Overview */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-3">The Three Controlled Formats</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Format A: Raw JSON</span>
                <span className="text-xs text-slate-500 font-mono">~686 tokens</span>
              </div>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                Represents retrieved graph nodes and edges as a compact JSON object with structural keys (`id`, `name`, `file`, `line`, `source`, `target`, `type`).
              </p>
              <div className="mt-3 p-2 bg-slate-50 rounded border border-slate-100 font-mono text-[11px] text-slate-700 leading-tight">
                {`{ "nodes": [ ... ], "edges": [ ... ] }`}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-amber-700">
              High syntactic overhead; prone to truncation on low token budgets.
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Format B: Adjacency List</span>
                <span className="text-xs text-slate-500 font-mono">~314 tokens</span>
              </div>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                Represents the exact same graph in a compact caller-to-target arrow notation grouped by definition block.
              </p>
              <div className="mt-3 p-2 bg-slate-50 rounded border border-slate-100 font-mono text-[11px] text-slate-700 leading-tight">
                {`Caller [src/file.py:20]\n  -> calls -> Callee [src/other.py:45]`}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-emerald-700">
              Maximum token density; ideal for budget-constrained context windows.
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900">Format C: Natural Language</span>
                <span className="text-xs text-slate-500 font-mono">~320 tokens</span>
              </div>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                Expresses definitions and edge relationships as fluent declarative English statements (`X is defined in Y`, `X calls Z`).
              </p>
              <div className="mt-3 p-2 bg-slate-50 rounded border border-slate-100 text-[11px] text-slate-700 leading-tight">
                PaymentService is defined in src/payment.py at line 20. PaymentService calls InvoiceValidator.
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-indigo-700">
              High comprehension for small models; strong semantic alignment.
            </div>
          </div>
        </div>
      </div>

      {/* Research Hypotheses */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white">
        <h2 className="text-base font-semibold text-slate-900 mb-3">Empirical Hypotheses Under Test</h2>
        <div className="space-y-3 text-xs text-slate-700">
          <div className="flex items-start space-x-2">
            <span className="font-semibold text-indigo-600 shrink-0">H1 (Natural Language):</span>
            <span>Natural-language edge descriptions improve file-localization accuracy compared with raw JSON by aligning graph relations with pretraining linguistic priors.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-semibold text-indigo-600 shrink-0">H2 (Adjacency Lists):</span>
            <span>Structured adjacency lists provide an optimal balance between token consumption and relational clarity for small agent context windows.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-semibold text-indigo-600 shrink-0">H3 (Budget Interaction):</span>
            <span>The serialization format effect widens dramatically under restricted token budgets (512 vs 4096 tokens) due to non-destructive truncation boundaries.</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-semibold text-indigo-600 shrink-0">H4 (Topology Sensitivity):</span>
            <span>Performance differences between formats scale with graph diameter and relationship edge density.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
