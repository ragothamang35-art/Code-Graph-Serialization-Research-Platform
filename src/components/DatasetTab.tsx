import React, { useState } from 'react';
import { Database, FileCode, Search, Network } from 'lucide-react';
import { Task, GraphNode, GraphEdge } from '../types';

interface DatasetTabProps {
  tasks: Task[];
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const DatasetTab: React.FC<DatasetTabProps> = ({ tasks, nodes, edges }) => {
  const [activeSubTab, setActiveSubTab] = useState<'tasks' | 'nodes' | 'edges'>('tasks');
  const [selectedTaskId, setSelectedTaskId] = useState<string>(tasks[0]?.instance_id || '');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const selectedTask = tasks.find((t) => t.instance_id === selectedTaskId) || tasks[0];

  const filteredNodes = nodes.filter(
    (n) =>
      n.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.file.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredEdges = edges.filter(
    (e) =>
      e.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.target.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Dataset Overview Header */}
      <div className="border border-slate-200 rounded-lg p-5 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Benchmark Dataset & Knowledge Graph Inspection
            </h2>
            <p className="text-xs text-slate-600 mt-0.5">
              Inspecting 6 competition-schema tasks, 27 AST-derived graph nodes, 22 directed dependency edges, and 256-dimensional embeddings.
            </p>
          </div>
          <div className="flex space-x-1 bg-slate-100 p-1 rounded-md text-xs font-medium">
            <button
              onClick={() => setActiveSubTab('tasks')}
              className={`px-3 py-1.5 rounded transition-colors ${
                activeSubTab === 'tasks' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Tasks ({tasks.length})
            </button>
            <button
              onClick={() => setActiveSubTab('nodes')}
              className={`px-3 py-1.5 rounded transition-colors ${
                activeSubTab === 'nodes' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Graph Nodes ({nodes.length})
            </button>
            <button
              onClick={() => setActiveSubTab('edges')}
              className={`px-3 py-1.5 rounded transition-colors ${
                activeSubTab === 'edges' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Graph Edges ({edges.length})
            </button>
          </div>
        </div>
      </div>

      {/* SubTab 1: Tasks */}
      {activeSubTab === 'tasks' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Task List */}
          <div className="border border-slate-200 rounded-lg bg-white overflow-hidden md:col-span-1">
            <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 text-xs font-semibold text-slate-700">
              Benchmark Task Instances
            </div>
            <div className="divide-y divide-slate-100 max-h-[580px] overflow-y-auto">
              {tasks.map((t) => {
                const isSelected = t.instance_id === selectedTaskId;
                return (
                  <button
                    key={t.instance_id}
                    onClick={() => setSelectedTaskId(t.instance_id)}
                    className={`w-full text-left p-3 text-xs transition-colors ${
                      isSelected ? 'bg-indigo-50/60 border-l-2 border-indigo-600' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="font-semibold text-slate-900">{t.instance_id}</div>
                    <div className="text-slate-500 text-[11px] mt-0.5">{t.repo}</div>
                    <div className="text-slate-600 text-[11px] line-clamp-2 mt-1">
                      {t.problem_statement}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Task Details & Unified Diff Patch */}
          <div className="border border-slate-200 rounded-lg bg-white p-5 md:col-span-2 space-y-4">
            {selectedTask ? (
              <>
                <div className="border-b border-slate-100 pb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="text-xs text-indigo-600 font-semibold">{selectedTask.repo}</span>
                    <h3 className="text-base font-bold text-slate-900">{selectedTask.instance_id}</h3>
                  </div>
                  <div className="text-xs text-slate-500 font-mono">
                    Base Commit: <code>{selectedTask.base_commit}</code>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
                    Problem Statement
                  </h4>
                  <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded border border-slate-100">
                    {selectedTask.problem_statement}
                  </p>
                </div>

                {selectedTask.hints_text && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
                      Hints Text
                    </h4>
                    <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded border border-slate-100">
                      {selectedTask.hints_text}
                    </p>
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                      Ground Truth Modified Files ({selectedTask.gold_files?.length || 0})
                    </h4>
                    <span className="text-[11px] text-slate-400">Parsed from unified diff patch</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(selectedTask.gold_files || []).map((f, i) => (
                      <span key={i} className="text-xs font-mono font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
                    Ground-Truth Unified Diff Patch
                  </h4>
                  <pre className="p-3 bg-slate-900 text-slate-100 rounded text-[11px] font-mono overflow-x-auto max-h-[220px] leading-relaxed">
                    {selectedTask.patch || '(No patch available)'}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-xs text-slate-400 py-12 text-center">Select a task to view details.</div>
            )}
          </div>
        </div>
      )}

      {/* SubTab 2: Nodes */}
      {activeSubTab === 'nodes' && (
        <div className="border border-slate-200 rounded-lg bg-white overflow-hidden space-y-4">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="relative w-72">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search nodes by name, file, or text..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full text-xs pl-8 pr-3 py-1.5 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Showing {filteredNodes.length} of {nodes.length} nodes
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-2.5">Node ID</th>
                  <th className="px-3 py-2.5">Qualified Symbol Name</th>
                  <th className="px-3 py-2.5">File Path</th>
                  <th className="px-3 py-2.5">Line</th>
                  <th className="px-4 py-2.5">Docstring / Code Definition Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-slate-800">
                {filteredNodes.map((n) => (
                  <tr key={n.id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-2.5 text-slate-500">{n.id}</td>
                    <td className="px-3 py-2.5 text-indigo-700 font-semibold">{n.name}</td>
                    <td className="px-3 py-2.5 text-slate-700">{n.file}</td>
                    <td className="px-3 py-2.5 text-slate-500">{n.line}</td>
                    <td className="px-4 py-2.5 font-sans text-slate-600 max-w-md truncate">{n.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SubTab 3: Edges */}
      {activeSubTab === 'edges' && (
        <div className="border border-slate-200 rounded-lg bg-white overflow-hidden space-y-4">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="relative w-72">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search edges by source, target, or type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full text-xs pl-8 pr-3 py-1.5 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <span className="text-xs text-slate-500 font-mono">
              Showing {filteredEdges.length} of {edges.length} edges
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-2.5">Source Node ID</th>
                  <th className="px-3 py-2.5">Relation Type</th>
                  <th className="px-3 py-2.5">Target Node ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-slate-800">
                {filteredEdges.map((e, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="px-4 py-2.5 font-semibold text-slate-900">{e.source}</td>
                    <td className="px-3 py-2.5 text-indigo-600 uppercase font-sans text-[11px] font-semibold">
                      {e.type}
                    </td>
                    <td className="px-3 py-2.5 text-slate-800">{e.target}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
