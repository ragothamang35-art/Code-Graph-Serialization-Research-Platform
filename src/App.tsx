import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { OverviewTab } from './components/OverviewTab';
import { EnhancementsTab } from './components/EnhancementsTab';
import { ComparatorTab } from './components/ComparatorTab';
import { ExperimentTab } from './components/ExperimentTab';
import { StatisticsTab } from './components/StatisticsTab';
import { AblationTab } from './components/AblationTab';
import { DatasetTab } from './components/DatasetTab';
import { PaperTab } from './components/PaperTab';
import { PythonCodeTab } from './components/PythonCodeTab';
import { Task, GraphNode, GraphEdge, SystemStatus } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [status, setStatus] = useState<SystemStatus | null>(null);

  // Cross-tab interaction state
  const [testContext, setTestContext] = useState<{
    taskId: string;
    formatType: string;
    budget: number;
  } | null>(null);

  useEffect(() => {
    // 1. Fetch system status
    fetch('/api/status')
      .then((r) => r.json())
      .then((data) => setStatus(data))
      .catch((err) => console.error('Error fetching status:', err));

    // 2. Fetch tasks
    fetch('/api/tasks')
      .then((r) => r.json())
      .then((data) => setTasks(data.tasks || []))
      .catch((err) => console.error('Error fetching tasks:', err));

    // 3. Fetch graph nodes & edges
    fetch('/api/graph')
      .then((r) => r.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      })
      .catch((err) => console.error('Error fetching graph:', err));
  }, []);

  const handleTestTaskFormat = (taskId: string, formatType: string, budget: number) => {
    setTestContext({ taskId, formatType, budget });
    setActiveTab('experiment');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} status={status} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <OverviewTab onSelectTab={setActiveTab} status={status} />
        )}

        {activeTab === 'enhancements' && <EnhancementsTab />}

        {activeTab === 'comparator' && (
          <ComparatorTab tasks={tasks} onTestTaskFormat={handleTestTaskFormat} />
        )}

        {activeTab === 'experiment' && (
          <ExperimentTab
            tasks={tasks}
            initialTaskId={testContext?.taskId}
            initialFormat={testContext?.formatType}
            initialBudget={testContext?.budget}
          />
        )}

        {activeTab === 'statistics' && <StatisticsTab />}

        {activeTab === 'ablation' && <AblationTab />}

        {activeTab === 'dataset' && (
          <DatasetTab tasks={tasks} nodes={nodes} edges={edges} />
        )}

        {activeTab === 'paper' && <PaperTab />}

        {activeTab === 'python' && <PythonCodeTab />}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-3">
          <div>
            GraphTrust · Kaggle Gemma 4 Developer Agent Paper Competition Submission
          </div>
          <div className="flex items-center space-x-4">
            <span>Controlled Invariant: Identical Retrieved Subgraphs</span>
            <span>·</span>
            <span>Gemma 4 E2B Evaluation</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
