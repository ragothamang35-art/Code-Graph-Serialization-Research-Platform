import React from 'react';
import { Network, Terminal, BookOpen, BarChart3, Database, Layers, Play } from 'lucide-react';
import { SystemStatus } from '../types';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  status: SystemStatus | null;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, status }) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: BookOpen },
    { id: 'comparator', label: 'Graph & Formats', icon: Network },
    { id: 'experiment', label: 'Experiment Runner', icon: Play },
    { id: 'statistics', label: 'Statistical Analysis', icon: BarChart3 },
    { id: 'ablation', label: 'Ablations', icon: Layers },
    { id: 'dataset', label: 'Dataset Explorer', icon: Database },
    { id: 'paper', label: 'Research Paper', icon: BookOpen },
    { id: 'python', label: 'Python CLI & Suite', icon: Terminal },
  ];

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-semibold text-sm">
              GT
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-900 tracking-tight text-base">GraphTrust</span>
                <span className="text-slate-400">/</span>
                <span className="text-xs text-slate-500 font-medium">Empirical Code Intelligence</span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Gemma 4 Agent Code Graph Serialization Study
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-xs text-slate-600">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-slate-700 font-medium">
                {status ? status.active_model : 'Gemma-4-E2B Engine'}
              </span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="text-slate-500 hidden md:block">
              Invariant: Frozen Canonical Subgraphs
            </div>
          </div>
        </div>

        {/* Clean segmented navigation bar */}
        <nav className="flex space-x-1 overflow-x-auto pb-1 pt-1 -mb-px">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-2 px-3 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-indigo-600 text-indigo-600 font-semibold'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
