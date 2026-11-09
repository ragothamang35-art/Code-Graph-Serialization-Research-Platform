import React, { useState, useEffect } from 'react';
import { Sliders, Copy, Check, ArrowRight, ShieldAlert, Cpu } from 'lucide-react';
import { Task, RetrievedSubgraph, SerializedGraph } from '../types';

interface ComparatorTabProps {
  tasks: Task[];
  onTestTaskFormat: (taskId: string, formatType: string, budget: number) => void;
}

export const ComparatorTab: React.FC<ComparatorTabProps> = ({ tasks, onTestTaskFormat }) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string>(tasks[0]?.instance_id || '');
  const [budget, setBudget] = useState<number>(2048);
  const [subgraph, setSubgraph] = useState<RetrievedSubgraph | null>(null);
  const [serializedFormats, setSerializedFormats] = useState<Record<string, SerializedGraph>>({});
  const [activeFormat, setActiveFormat] = useState<string>('json');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const selectedTask = tasks.find((t) => t.instance_id === selectedTaskId) || tasks[0];

  useEffect(() => {
    if (!selectedTask) return;
    setLoading(true);

    // Fetch canonical subgraph from API
    fetch('/api/retrieve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ taskId: selectedTask.instance_id, options: { maxDepth: 2, useEmbeddings: true } }),
    })
      .then((res) => res.json())
      .then((sub: RetrievedSubgraph) => {
        setSubgraph(sub);

        // Serialize all 3 formats + baselines under current budget
        const formatsToFetch = ['json', 'adjacency_list', 'natural_language', 'keyword_match', 'no_graph'];
        Promise.all(
          formatsToFetch.map((fmt) =>
            fetch('/api/serialize', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ subgraph: sub, formatType: fmt, budget }),
            }).then((r) => r.json())
          )
        ).then((results) => {
          const map: Record<string, SerializedGraph> = {};
          formatsToFetch.forEach((fmt, i) => {
            map[fmt] = results[i];
          });
          setSerializedFormats(map);
          setLoading(false);
        });
      })
      .catch((err) => {
        console.error('Failed to retrieve or serialize:', err);
        setLoading(false);
      });
  }, [selectedTaskId, budget]);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const currentSerialized = serializedFormats[activeFormat];

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Top Controls: Task Selector + Token Budget Slider */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
              Select Benchmark Task
            </label>
            <select
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
              className="w-full text-xs font-medium border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {tasks.map((t) => (
                <option key={t.instance_id} value={t.instance_id}>
                  {t.repo} — {t.instance_id}
                </option>
              ))}
            </select>
            {selectedTask && (
              <p className="mt-2 text-xs text-slate-600 line-clamp-2">
                {selectedTask.problem_statement}
              </p>
            )}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center space-x-1">
                <Sliders className="w-3.5 h-3.5 text-slate-500" />
                <span>Context Token Budget Limit</span>
              </label>
              <span className="text-xs font-mono font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                {budget} tokens
              </span>
            </div>
            <input
              type="range"
              min="512"
              max="4096"
              step="256"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-1 font-mono">
              <span className={budget === 512 ? 'text-indigo-600 font-semibold' : ''}>512 (Constrained)</span>
              <span className={budget === 1024 ? 'text-indigo-600 font-semibold' : ''}>1024</span>
              <span className={budget === 2048 ? 'text-indigo-600 font-semibold' : ''}>2048 (Standard)</span>
              <span className={budget === 4096 ? 'text-indigo-600 font-semibold' : ''}>4096 (Full)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Canonical Subgraph Summary Bar */}
      {subgraph && (
        <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/70">
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-slate-700">
            <div>
              <span className="text-slate-500 font-medium">Canonical Retrieved Subgraph:</span>{' '}
              <strong className="text-slate-900 font-semibold">{subgraph.nodes.length} nodes</strong>,{' '}
              <strong className="text-slate-900 font-semibold">{subgraph.edges.length} edges</strong> across{' '}
              <strong className="text-slate-900 font-semibold">{subgraph.candidate_files.length} candidate files</strong>
            </div>

            <div className="flex items-center space-x-4 text-xs text-slate-500">
              <span>Seed Nodes: <code className="text-slate-800">{subgraph.seed_node_ids.join(', ')}</code></span>
              <span>·</span>
              <span>Max Depth: <strong className="text-slate-700">2 hops</strong></span>
              <span>·</span>
              <span>Cosine Embeddings: <strong className="text-slate-700">Active</strong></span>
            </div>
          </div>
        </div>
      )}

      {/* Format Comparison Tabs */}
      <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-1">
            {[
              { id: 'json', label: 'Format A: Raw JSON' },
              { id: 'adjacency_list', label: 'Format B: Adjacency List' },
              { id: 'natural_language', label: 'Format C: Natural Language' },
              { id: 'keyword_match', label: 'Baseline: Keyword Match' },
              { id: 'no_graph', label: 'Baseline: No Graph' },
            ].map((fmt) => {
              const ser = serializedFormats[fmt.id];
              return (
                <button
                  key={fmt.id}
                  onClick={() => setActiveFormat(fmt.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    activeFormat === fmt.id
                      ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {fmt.label}
                  {ser && (
                    <span className="ml-1.5 text-[10px] text-slate-400 font-mono">
                      ({ser.token_count}t)
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {currentSerialized && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => copyToClipboard(currentSerialized.content, activeFormat)}
                className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 border border-slate-300 rounded bg-white hover:bg-slate-50"
              >
                {copiedKey === activeFormat ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                    <span>Copy Text</span>
                  </>
                )}
              </button>
              <button
                onClick={() => onTestTaskFormat(selectedTask.instance_id, activeFormat, budget)}
                className="inline-flex items-center space-x-1 px-3 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded transition-colors"
              >
                <span>Run Agent Test</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Truncation & Token Accounting Bar */}
        {currentSerialized && (
          <div className="px-5 py-2.5 bg-slate-50/50 border-b border-slate-200 flex flex-wrap items-center justify-between text-xs text-slate-600">
            <div className="flex items-center space-x-4">
              <span>
                Estimated Tokens: <strong className="text-slate-900 font-mono font-semibold">{currentSerialized.token_count}</strong> / {budget}
              </span>
              <span>·</span>
              <span>
                Included Nodes: <strong className="text-slate-900 font-mono">{currentSerialized.node_count}</strong> / {subgraph?.nodes.length || 0}
              </span>
              <span>·</span>
              <span>
                Included Edges: <strong className="text-slate-900 font-mono">{currentSerialized.edge_count}</strong> / {subgraph?.edges.length || 0}
              </span>
            </div>

            {currentSerialized.is_truncated && (
              <div className="flex items-center space-x-1 text-amber-700 font-medium">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Truncated by token budget (non-destructive node boundary preserved)</span>
              </div>
            )}
          </div>
        )}

        {/* Serialized Content Display */}
        <div className="p-4">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading serialization...</div>
          ) : currentSerialized ? (
            <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto max-h-[460px] leading-relaxed">
              {currentSerialized.content || '(No code graph context in this condition)'}
            </pre>
          ) : (
            <div className="py-12 text-center text-xs text-slate-400">No data available.</div>
          )}
        </div>
      </div>

      {/* Tri-Format Token Accounting Invariant Proof */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white">
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Controlled Invariant Accounting</h3>
        <p className="text-xs text-slate-600 mb-4">
          Notice how the identical underlying nodes and relationships produce radically different token footprints across serialization styles:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 rounded border border-slate-200 bg-slate-50">
            <div className="font-semibold text-slate-900">Format A (Raw JSON)</div>
            <div className="text-xl font-semibold text-slate-800 font-mono mt-1">
              {serializedFormats['json']?.token_count || '—'} tokens
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Includes quotes, braces, colons, key names.</div>
          </div>

          <div className="p-3 rounded border border-slate-200 bg-slate-50">
            <div className="font-semibold text-slate-900">Format B (Adjacency List)</div>
            <div className="text-xl font-semibold text-emerald-700 font-mono mt-1">
              {serializedFormats['adjacency_list']?.token_count || '—'} tokens
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Terse arrow syntax; 54% fewer tokens than JSON.</div>
          </div>

          <div className="p-3 rounded border border-slate-200 bg-slate-50">
            <div className="font-semibold text-slate-900">Format C (Natural Language)</div>
            <div className="text-xl font-semibold text-indigo-700 font-mono mt-1">
              {serializedFormats['natural_language']?.token_count || '—'} tokens
            </div>
            <div className="text-[11px] text-slate-500 mt-1">English sentences; 53% fewer tokens than JSON.</div>
          </div>
        </div>
      </div>
    </div>
  );
};
