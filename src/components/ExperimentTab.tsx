import React, { useState } from 'react';
import { Play, RefreshCw, CheckCircle2, AlertCircle, FileCode, Clock, Cpu, Download } from 'lucide-react';
import { Task, PredictionResult, BenchmarkResult } from '../types';

interface ExperimentTabProps {
  tasks: Task[];
  initialTaskId?: string;
  initialFormat?: string;
  initialBudget?: number;
}

export const ExperimentTab: React.FC<ExperimentTabProps> = ({
  tasks,
  initialTaskId,
  initialFormat = 'json',
  initialBudget = 2048,
}) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string>(initialTaskId || tasks[0]?.instance_id || '');
  const [selectedFormat, setSelectedFormat] = useState<string>(initialFormat);
  const [budget, setBudget] = useState<number>(initialBudget);
  const [forceMock, setForceMock] = useState<boolean>(false);

  // Single run state
  const [singleResult, setSingleResult] = useState<PredictionResult | null>(null);
  const [singleRunning, setSingleRunning] = useState<boolean>(false);

  // Batch run state
  const [batchResults, setBatchResults] = useState<BenchmarkResult[]>([]);
  const [batchRunning, setBatchRunning] = useState<boolean>(false);
  const [batchProgress, setBatchProgress] = useState<string>('');

  const selectedTask = tasks.find((t) => t.instance_id === selectedTaskId) || tasks[0];

  const handleRunSingle = async () => {
    if (!selectedTask) return;
    setSingleRunning(true);
    setSingleResult(null);

    try {
      const res = await fetch('/api/run-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          taskId: selectedTask.instance_id,
          formatType: selectedFormat,
          budget,
          forceMock,
        }),
      });
      const data = await res.json();
      setSingleResult(data);
    } catch (err) {
      console.error('Inference error:', err);
    } finally {
      setSingleRunning(false);
    }
  };

  const handleRunSmokeTest = async () => {
    // 3-Task smoke test required by Section 20/22
    setBatchRunning(true);
    setBatchProgress('Executing 3-task smoke test across JSON, Adjacency List, and Natural Language...');

    try {
      const res = await fetch('/api/run-experiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          formats: ['json', 'adjacency_list', 'natural_language'],
          budgets: [2048],
          limit: 3,
        }),
      });
      const data = await res.json();
      setBatchResults(data.results || []);
      setBatchProgress('Smoke test completed successfully (3 tasks evaluated).');
    } catch (err) {
      console.error('Smoke test error:', err);
      setBatchProgress('Smoke test failed.');
    } finally {
      setBatchRunning(false);
    }
  };

  const handleRunFullBenchmark = async () => {
    setBatchRunning(true);
    setBatchProgress('Running full matrix across all 6 tasks and 4 token budgets (512, 1024, 2048, 4096 tokens)...');

    try {
      const res = await fetch('/api/run-experiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          formats: ['json', 'adjacency_list', 'natural_language', 'keyword_match', 'no_graph'],
          budgets: [512, 1024, 2048, 4096],
          limit: tasks.length,
        }),
      });
      const data = await res.json();
      setBatchResults(data.results || []);
      setBatchProgress(`Full benchmark completed (${tasks.length} tasks x 4 budgets evaluated).`);
    } catch (err) {
      console.error('Benchmark error:', err);
      setBatchProgress('Benchmark error.');
    } finally {
      setBatchRunning(false);
    }
  };

  const exportResultsJson = () => {
    const blob = new Blob([JSON.stringify(batchResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graphtrust_experiment_results.json';
    a.click();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Top Section: Single Task Evaluation */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Task-Level Model Inference & Localization</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Send the standardized prompt and serialized graph context to the agent and observe JSON output & predictions.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-xs text-slate-600 flex items-center space-x-1 cursor-pointer">
              <input
                type="checkbox"
                checked={forceMock}
                onChange={(e) => setForceMock(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-0 text-xs"
              />
              <span>Force Local Deterministic Heuristic</span>
            </label>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
              Select Task
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
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
              Serialization Format
            </label>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value)}
              className="w-full text-xs font-medium border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="json">Format A: Raw JSON</option>
              <option value="adjacency_list">Format B: Adjacency List</option>
              <option value="natural_language">Format C: Natural Language Sentences</option>
              <option value="keyword_match">Baseline: Keyword Match</option>
              <option value="no_graph">Baseline: No Graph</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
              Context Budget
            </label>
            <select
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full text-xs font-medium border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-900 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="512">512 tokens (Constrained)</option>
              <option value="1024">1024 tokens</option>
              <option value="2048">2048 tokens (Standard)</option>
              <option value="4096">4096 tokens (Full)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-500">
            Ground-truth gold files for this task:{' '}
            <code className="text-slate-800 font-medium">{(selectedTask?.gold_files || []).join(', ')}</code>
          </div>

          <button
            onClick={handleRunSingle}
            disabled={singleRunning}
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors disabled:opacity-50"
          >
            {singleRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running Inference...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Run Agent Inference</span>
              </>
            )}
          </button>
        </div>

        {/* Single Run Result Display */}
        {singleResult && (
          <div className="mt-4 pt-4 border-t border-slate-100 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <span className="text-slate-500">Accuracy@1:</span>
                <div className={`text-xl font-bold font-mono mt-0.5 ${singleResult.metrics.acc_at_1 > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>
                  {singleResult.metrics.acc_at_1 > 0 ? 'CORRECT' : 'MISS'}
                </div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <span className="text-slate-500">Accuracy@5:</span>
                <div className={`text-xl font-bold font-mono mt-0.5 ${singleResult.metrics.acc_at_5 > 0 ? 'text-emerald-600' : 'text-slate-400'}`}>
                  {singleResult.metrics.acc_at_5 > 0 ? 'HIT IN TOP 5' : 'MISS'}
                </div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <span className="text-slate-500">MRR@5:</span>
                <div className="text-xl font-bold font-mono text-slate-800 mt-0.5">
                  {singleResult.metrics.mrr_at_5.toFixed(2)}
                </div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <span className="text-slate-500">Prompt Tokens:</span>
                <div className="text-xl font-bold font-mono text-indigo-600 mt-0.5">
                  {singleResult.token_count}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <h4 className="font-semibold text-slate-800 mb-1">Predicted Files (Ranked):</h4>
                <div className="space-y-1">
                  {singleResult.predicted_files.map((p, idx) => {
                    const isGold = (singleResult.gold_files || []).includes(p);
                    return (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-2 rounded border font-mono text-xs ${
                          isGold ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-slate-50 border-slate-200 text-slate-700'
                        }`}
                      >
                        <span className="truncate">#{idx + 1}. {p}</span>
                        {isGold && (
                          <span className="text-[10px] uppercase font-bold text-emerald-700">Gold Match</span>
                        )}
                      </div>
                    );
                  })}
                  {singleResult.predicted_files.length === 0 && (
                    <div className="text-slate-400 italic">No files predicted.</div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-1">Agent Reasoning:</h4>
                <p className="p-3 bg-slate-50 border border-slate-200 rounded text-slate-700 leading-relaxed max-h-[140px] overflow-y-auto">
                  {singleResult.reasoning || 'No explanation provided.'}
                </p>
                <div className="mt-2 text-[11px] text-slate-500 flex items-center space-x-3">
                  <span>Latency: {singleResult.latency_ms}ms</span>
                  <span>·</span>
                  <span>Execution: {singleResult.is_mock ? 'Deterministic Validation Simulation' : 'Live Gemini API'}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-slate-800 text-xs mb-1">Raw Agent Output:</h4>
              <pre className="p-3 bg-slate-900 text-slate-200 rounded text-[11px] font-mono overflow-x-auto max-h-[150px]">
                {singleResult.raw_output}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Batch Runner Suite */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Controlled Batch Experiments</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Execute multi-task benchmarks across formats to compute aggregate statistical distributions.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRunSmokeTest}
              disabled={batchRunning}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50"
            >
              <span>Run 3-Task Smoke Test</span>
            </button>
            <button
              onClick={handleRunFullBenchmark}
              disabled={batchRunning}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50"
            >
              <span>Run Full Matrix Benchmark</span>
            </button>
          </div>
        </div>

        {batchProgress && (
          <div className="text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 p-2.5 rounded flex items-center space-x-2">
            {batchRunning && <RefreshCw className="w-3 h-3 animate-spin" />}
            <span>{batchProgress}</span>
          </div>
        )}

        {batchResults.length > 0 && (
          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wide">
                Aggregated Experimental Matrix
              </h3>
              <button
                onClick={exportResultsJson}
                className="inline-flex items-center space-x-1 text-xs text-slate-600 hover:text-slate-900 border border-slate-300 px-2.5 py-1 rounded"
              >
                <Download className="w-3 h-3" />
                <span>Export JSON Results</span>
              </button>
            </div>

            {batchResults.map((bRes, idx) => (
              <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 text-xs font-semibold text-slate-800 flex items-center justify-between">
                  <span>Context Budget: {bRes.budget} Tokens</span>
                  <span className="text-slate-500 font-normal">Condition Matrix</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-white border-b border-slate-200 text-slate-600 font-semibold">
                      <tr>
                        <th className="px-4 py-2.5">Format Condition</th>
                        <th className="px-3 py-2.5">Accuracy@1</th>
                        <th className="px-3 py-2.5">Accuracy@5</th>
                        <th className="px-3 py-2.5">MRR@5</th>
                        <th className="px-3 py-2.5">Candidate Coverage</th>
                        <th className="px-3 py-2.5">Avg Prompt Tokens</th>
                        <th className="px-3 py-2.5">Truncation Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono">
                      {Object.entries(bRes.summaries).map(([fmt, s]: [string, any]) => (
                        <tr key={fmt} className="hover:bg-slate-50/50">
                          <td className="px-4 py-2.5 font-sans font-medium text-slate-900">
                            {fmt === 'json'
                              ? 'Format A (JSON)'
                              : fmt === 'adjacency_list'
                              ? 'Format B (Adjacency List)'
                              : fmt === 'natural_language'
                              ? 'Format C (Natural Language)'
                              : fmt === 'keyword_match'
                              ? 'Baseline: Keyword Match'
                              : 'Baseline: No Graph'}
                          </td>
                          <td className="px-3 py-2.5 text-slate-800 font-semibold">
                            {(s.acc_at_1 * 100).toFixed(1)}%
                          </td>
                          <td className="px-3 py-2.5 text-slate-800">
                            {(s.acc_at_5 * 100).toFixed(1)}%
                          </td>
                          <td className="px-3 py-2.5 text-slate-800">{s.mrr_at_5.toFixed(3)}</td>
                          <td className="px-3 py-2.5 text-slate-700">
                            {(s.candidate_coverage * 100).toFixed(1)}%
                          </td>
                          <td className="px-3 py-2.5 text-indigo-600 font-semibold">{s.avg_tokens}</td>
                          <td className="px-3 py-2.5 text-slate-600">
                            {(s.truncation_rate * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
