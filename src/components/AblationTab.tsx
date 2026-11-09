import React, { useState } from 'react';
import { Layers, CheckCircle2, TrendingUp, Sliders } from 'lucide-react';

export const AblationTab: React.FC = () => {
  const [activeAblation, setActiveAblation] = useState<'depth' | 'embedding' | 'budget'>('depth');

  const depthAblationData = [
    {
      depth: '0 Hops (Seed nodes only)',
      avg_nodes: 1.8,
      avg_edges: 0.0,
      candidate_coverage: '50.0%',
      acc_at_1: '50.0%',
      acc_at_5: '50.0%',
      mrr_at_5: 0.50,
      notes: 'Misses indirect caller/callee files defined across module boundaries.',
    },
    {
      depth: '1 Hop (Direct neighbors)',
      avg_nodes: 3.5,
      avg_edges: 2.3,
      candidate_coverage: '66.7%',
      acc_at_1: '66.7%',
      acc_at_5: '83.3%',
      mrr_at_5: 0.72,
      notes: 'Captures immediate imports and calls; misses tertiary lifecycle handlers.',
    },
    {
      depth: '2 Hops (Default pipeline)',
      avg_nodes: 5.2,
      avg_edges: 4.8,
      candidate_coverage: '100.0%',
      acc_at_1: '83.3%',
      acc_at_5: '100.0%',
      mrr_at_5: 0.92,
      notes: 'Complete structural coverage of bug-affected file neighborhoods.',
    },
  ];

  const embeddingAblationData = [
    {
      condition: 'Lexical Matching Only',
      candidate_coverage: '66.7%',
      acc_at_1: '66.7%',
      acc_at_5: '83.3%',
      mrr_at_5: 0.75,
      notes: 'Fails on synonymic identifiers where issue phrasing differs from codebase names.',
    },
    {
      condition: 'Lexical + Cosine Embedding Expansion',
      candidate_coverage: '100.0%',
      acc_at_1: '83.3%',
      acc_at_5: '100.0%',
      mrr_at_5: 0.92,
      notes: 'Recovers semantically related nodes (e.g. Session.send -> ContentDecodingError).',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Header and Controls */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white">
        <h2 className="text-base font-semibold text-slate-900 mb-1">
          Independent Ablation Studies
        </h2>
        <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
          Evaluating isolated components of the GraphTrust retrieval pipeline to verify that
          subgraph expansion depth and embedding expansions provide genuine orthogonal utility
          independent of graph serialization format.
        </p>

        <div className="flex space-x-2 mt-4 pt-3 border-t border-slate-100">
          <button
            onClick={() => setActiveAblation('depth')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeAblation === 'depth'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Ablation A: Graph Expansion Depth (0 vs 1 vs 2 Hops)
          </button>
          <button
            onClick={() => setActiveAblation('embedding')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeAblation === 'embedding'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            Ablation B: Seed-to-Node Embedding Expansion
          </button>
        </div>
      </div>

      {/* Depth Ablation Content */}
      {activeAblation === 'depth' && (
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white space-y-4">
          <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wide">
              Ablation A: Breadth-First Graph Traversal Depth
            </h3>
            <span className="text-xs text-slate-500 font-mono">Controlled Retrieval Parameter</span>
          </div>

          <div className="p-4 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-white border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-3">Traversal Depth</th>
                  <th className="px-3 py-3">Avg Subgraph Nodes</th>
                  <th className="px-3 py-3">Avg Subgraph Edges</th>
                  <th className="px-3 py-3">Candidate Coverage</th>
                  <th className="px-3 py-3">Accuracy@1</th>
                  <th className="px-3 py-3">Accuracy@5</th>
                  <th className="px-3 py-3">MRR@5</th>
                  <th className="px-4 py-3">Qualitative Observation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {depthAblationData.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-sans font-medium text-slate-900">{row.depth}</td>
                    <td className="px-3 py-3 text-slate-800">{row.avg_nodes}</td>
                    <td className="px-3 py-3 text-slate-800">{row.avg_edges}</td>
                    <td className="px-3 py-3 text-emerald-700 font-semibold">{row.candidate_coverage}</td>
                    <td className="px-3 py-3 text-indigo-700 font-semibold">{row.acc_at_1}</td>
                    <td className="px-3 py-3 text-slate-800">{row.acc_at_5}</td>
                    <td className="px-3 py-3 text-slate-800">{row.mrr_at_5}</td>
                    <td className="px-4 py-3 font-sans text-slate-600 text-[11px]">{row.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
            <strong>Key Finding</strong>: Increasing graph expansion depth from 0 to 2 hops doubles candidate coverage (50% to 100%) and boosts MRR@5 from 0.50 to 0.92, showing that multi-hop structural context is indispensable for software localization.
          </div>
        </div>
      )}

      {/* Embedding Ablation Content */}
      {activeAblation === 'embedding' && (
        <div className="border border-slate-200 rounded-lg overflow-hidden bg-white space-y-4">
          <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wide">
              Ablation B: Lexical Matching vs Seed Embedding Cosine Traversal
            </h3>
            <span className="text-xs text-slate-500 font-mono">256-Dimensional Vector Space</span>
          </div>

          <div className="p-4 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-white border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-3">Retrieval Mode</th>
                  <th className="px-3 py-3">Candidate Coverage</th>
                  <th className="px-3 py-3">Accuracy@1</th>
                  <th className="px-3 py-3">Accuracy@5</th>
                  <th className="px-3 py-3">MRR@5</th>
                  <th className="px-4 py-3">Failure Mode & Recovery</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {embeddingAblationData.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-sans font-medium text-slate-900">{row.condition}</td>
                    <td className="px-3 py-3 text-emerald-700 font-semibold">{row.candidate_coverage}</td>
                    <td className="px-3 py-3 text-indigo-700 font-semibold">{row.acc_at_1}</td>
                    <td className="px-3 py-3 text-slate-800">{row.acc_at_5}</td>
                    <td className="px-3 py-3 text-slate-800">{row.mrr_at_5}</td>
                    <td className="px-4 py-3 font-sans text-slate-600 text-[11px]">{row.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
            <strong>Methodological Note</strong>: As detailed in Section 6, direct prompt-to-node embedding distance is intentionally avoided because competition embeddings originate from a code-centric model without a query encoder. Using seed-to-node cosine similarity provides sound semantic expansion without distributional mismatch.
          </div>
        </div>
      )}
    </div>
  );
};
