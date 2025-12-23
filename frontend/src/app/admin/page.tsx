'use client';

import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Database, 
  Activity, 
  Settings, 
  Cpu, 
  Users, 
  Clock, 
  Zap, 
  AlertCircle,
  Search,
  Terminal,
  Play,
  Save,
  BarChart3,
  Bell
} from 'lucide-react';
import { api } from '@/lib/api';

// Types
interface StatCard {
  label: string;
  value: string;
  change: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
}

interface LogEntry {
  id: string;
  model: string;
  status: string;
  latency: string;
  tokens: number;
  time: string;
  preview: string;
}

interface ModelInfo {
  name: string;
  type: string;
  status: string;
  latency: string;
  cost: string;
}

// Components
const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`bg-slate-800 border border-slate-700 rounded-xl p-5 ${className}`}>
    {children}
  </div>
);

const Badge = ({ status }: { status: string }) => {
  const styles: Record<string, string> = {
    success: 'bg-green-500/10 text-green-400 border-green-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    warning: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    neutral: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };
  
  let type = 'neutral';
  if (['success', 'Operational', 'Low', 'Ultra-Low', 'COMPLETED'].includes(status)) type = 'success';
  if (['error', 'Degraded', 'High', 'FAILED'].includes(status)) type = 'error';
  if (['Medium', 'PROCESSING'].includes(status)) type = 'warning';

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${styles[type]}`}>
      {status}
    </span>
  );
};

const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active, 
  onClick 
}: { 
  icon: React.ComponentType<{ size?: number; className?: string }>; 
  label: string; 
  active: boolean; 
  onClick: () => void;
}) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all ${
      active 
        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' 
        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
    }`}
  >
    <Icon size={20} />
    {label}
  </button>
);

// Views
const DashboardView = ({ stats, logs, systemInfo }: { 
  stats: StatCard[]; 
  logs: LogEntry[]; 
  systemInfo: any;
}) => (
  <div className="space-y-6 animate-in fade-in duration-500">
    {/* Top Stats Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => (
        <Card key={idx} className="hover:border-indigo-500/50 transition-colors cursor-pointer">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-slate-400 text-sm font-medium">{stat.label}</p>
              <h3 className="text-2xl font-bold text-white mt-1">{stat.value}</h3>
            </div>
            <div className={`p-2 rounded-lg bg-slate-700/50 ${stat.color}`}>
              <stat.icon size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center text-xs">
            <span className={stat.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}>
              {stat.change}
            </span>
            <span className="text-slate-500 ml-1">vs yesterday</span>
          </div>
        </Card>
      ))}
    </div>

    {/* Charts & Real-time Logs */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Chart Area */}
      <Card className="lg:col-span-2">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <BarChart3 size={18} className="text-indigo-400"/>
            Token Usage Volume
          </h3>
          <select className="bg-slate-900 border border-slate-700 text-slate-300 text-sm rounded-lg p-1.5 focus:ring-indigo-500 focus:border-indigo-500">
            <option>Last 24 Hours</option>
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
        </div>
        
        {/* Simple chart visualization */}
        <div className="h-64 flex items-end justify-between gap-2 px-2">
          {[40, 65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 95].map((h, i) => (
            <div key={i} className="w-full bg-indigo-500/20 hover:bg-indigo-500/40 rounded-t-sm transition-all relative group h-full flex items-end">
              <div style={{ height: `${h}%` }} className="w-full bg-indigo-500 relative rounded-t-sm">
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap border border-slate-700 z-10">
                  {h * 100} Tokens
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-500 px-1">
          <span>00:00</span>
          <span>06:00</span>
          <span>12:00</span>
          <span>18:00</span>
          <span>23:59</span>
        </div>
      </Card>

      {/* GPU/Resource Status */}
      <Card>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu size={18} className="text-pink-400"/>
          Infrastructure Health
        </h3>
        
        <div className="space-y-6">
          {systemInfo?.gpu_info && systemInfo.gpu_info.length > 0 ? (
            systemInfo.gpu_info.map((gpu: any, idx: number) => (
              <div key={idx}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300">GPU {gpu.index} ({gpu.name})</span>
                  <span className="text-green-400">{gpu.utilization}% Load</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${gpu.utilization}%` }}></div>
                </div>
              </div>
            ))
          ) : (
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">CPU Usage</span>
                <span className="text-blue-400">{systemInfo?.cpu_percent?.toFixed(1) || 0}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${systemInfo?.cpu_percent || 0}%` }}></div>
              </div>
            </div>
          )}

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-300">Memory</span>
              <span className="text-yellow-400">{systemInfo?.memory_percent?.toFixed(1) || 0}% Used</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-yellow-500 h-2 rounded-full" style={{ width: `${systemInfo?.memory_percent || 0}%` }}></div>
            </div>
          </div>
        </div>
      </Card>
    </div>

    {/* Recent Logs Table */}
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-white">Recent TTS Interactions</h3>
        <button className="text-sm text-indigo-400 hover:text-indigo-300">View All Logs &rarr;</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-400">
          <thead className="text-xs uppercase bg-slate-900/50 text-slate-300">
            <tr>
              <th className="px-4 py-3 rounded-l-lg">Task ID</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Input Preview</th>
              <th className="px-4 py-3">Cost</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 rounded-r-lg">Time</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => (
              <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-indigo-300">{log.id.slice(0, 8)}...</td>
                <td className="px-4 py-3">{log.model}</td>
                <td className="px-4 py-3 text-slate-300 max-w-xs truncate">{log.preview}</td>
                <td className="px-4 py-3 font-mono">{log.tokens}</td>
                <td className="px-4 py-3"><Badge status={log.status} /></td>
                <td className="px-4 py-3 text-xs">{log.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  </div>
);

const PromptLabView = () => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">
    <div className="flex flex-col gap-4">
      <Card className="flex-1 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Terminal size={18} className="text-indigo-400"/>
            Prompt Editor
          </h3>
          <div className="flex gap-2">
            <select className="bg-slate-900 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1">
              <option>System Prompt v2.1</option>
              <option>System Prompt v2.0</option>
              <option>Create New...</option>
            </select>
            <button className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white"><Save size={16}/></button>
          </div>
        </div>
        <div className="flex-1 flex flex-col gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-500 uppercase">System Context</label>
            <textarea 
              className="w-full h-32 bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-300 font-mono focus:ring-1 focus:ring-indigo-500 focus:outline-none resize-none"
              defaultValue="You are a helpful AI assistant specialized in text-to-speech generation. You should provide clear and natural voice synthesis."
            />
          </div>
          <div className="space-y-1 flex-1 flex flex-col">
            <label className="text-xs font-semibold text-slate-500 uppercase">User Input (Test Case)</label>
            <textarea 
              className="w-full flex-1 bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-300 font-mono focus:ring-1 focus:ring-indigo-500 focus:outline-none resize-none"
              defaultValue="Generate speech for: Hello, this is a test message."
            />
          </div>
        </div>
        <div className="mt-4 flex justify-between items-center border-t border-slate-700 pt-4">
          <div className="flex gap-4 text-xs text-slate-400">
            <span>Temperature: <span className="text-white">0.7</span></span>
            <span>Max Tokens: <span className="text-white">2048</span></span>
          </div>
          <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
            <Play size={16} fill="currentColor" /> Run Test
          </button>
        </div>
      </Card>
    </div>

    <div className="flex flex-col gap-4">
      <Card className="flex-1 flex flex-col h-full">
        <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-4">
          <h3 className="text-lg font-semibold text-white">Output Preview</h3>
          <Badge status="success" /> 
        </div>
        <div className="flex-1 bg-slate-900/50 rounded-lg p-4 font-mono text-sm text-slate-300 overflow-y-auto">
          <p className="text-slate-500 mb-2"># Generated by VoxCPM in 1.4s</p>
          <p>Audio file generated successfully.</p>
          <br/>
          <p className="text-green-400">Output: /static/generated/audio.wav</p>
          <p className="text-green-400">Duration: 3.2s</p>
          <p className="text-green-400">Sample Rate: 16000 Hz</p>
        </div>
        <div className="mt-4 flex gap-2">
          <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm">Save as Evaluation Case</button>
          <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm">Compare with V1.0</button>
        </div>
      </Card>
    </div>
  </div>
);

const ModelsView = ({ models }: { models: ModelInfo[] }) => (
  <div className="space-y-6 animate-in fade-in duration-500">
    <div className="flex justify-between items-center">
      <h2 className="text-xl font-bold text-white">Model Registry & Routing</h2>
      <button className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm">Connect New Model</button>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {models.map((model, idx) => (
        <Card key={idx} className="flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-700 rounded-lg">
                  <Cpu size={24} className="text-indigo-400"/>
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg">{model.name}</h3>
                  <p className="text-slate-400 text-sm">{model.type}</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge status={model.status} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-slate-900/50 p-2 rounded">
                <span className="text-xs text-slate-500 block">Avg Latency</span>
                <span className="text-sm font-medium text-slate-200">{model.latency}</span>
              </div>
              <div className="bg-slate-900/50 p-2 rounded">
                <span className="text-xs text-slate-500 block">Cost Tier</span>
                <span className="text-sm font-medium text-slate-200">{model.cost}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2 mt-2 pt-4 border-t border-slate-700">
            <button className="flex-1 text-sm bg-slate-700 hover:bg-slate-600 text-white py-2 rounded">Configure</button>
            <button className="flex-1 text-sm border border-slate-600 hover:bg-slate-700 text-slate-300 py-2 rounded">View Metrics</button>
          </div>
        </Card>
      ))}
    </div>
  </div>
);

// Main Component
export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState<StatCard[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load system info
      const systemRes = await api.get('/monitor/system');
      setSystemInfo(systemRes.data);

      // Load database stats
      const dbRes = await api.get('/monitor/stats/database');
      const dbStats = dbRes.data;

      // Calculate stats
      const totalChars = dbStats.today_tasks * 100; // Estimate
      const totalCost = dbStats.total_credits || 0;
      const avgLatency = '240ms'; // TODO: Calculate from actual data
      
      setStats([
        { 
          label: 'Total Characters (24h)', 
          value: totalChars.toLocaleString(), 
          change: '+12.5%', 
          icon: Database, 
          color: 'text-blue-400' 
        },
        { 
          label: 'Avg Latency (TTFT)', 
          value: avgLatency, 
          change: '-15ms', 
          icon: Clock, 
          color: 'text-green-400' 
        },
        { 
          label: 'Est. Cost (Today)', 
          value: `$${(totalCost * 0.001).toFixed(2)}`, 
          change: '+5.2%', 
          icon: Zap, 
          color: 'text-yellow-400' 
        },
        { 
          label: 'Active Sessions', 
          value: dbStats.total_users?.toString() || '0', 
          change: '+12', 
          icon: Activity, 
          color: 'text-purple-400' 
        },
      ]);

      // Load recent tasks as logs
      const recentTasks = dbStats.recent_tasks || [];
      setLogs(recentTasks.map((task: any) => ({
        id: task.id,
        model: 'VoxCPM',
        status: task.status,
        latency: '1.2s',
        tokens: task.cost || 0,
        time: new Date(task.created_at).toLocaleTimeString(),
        preview: task.text?.substring(0, 50) || 'N/A',
      })));

      // Load models
      const servicesRes = await api.get('/monitor/services');
      const services = servicesRes.data;
      
      setModels([
        { 
          name: 'VoxCPM 1.5', 
          type: 'Self-Hosted', 
          status: services.tts_engine ? 'Operational' : 'Degraded', 
          latency: 'Medium', 
          cost: 'Low' 
        },
        { 
          name: 'Embedding Service', 
          type: 'Vector', 
          status: 'Operational', 
          latency: 'Ultra-Low', 
          cost: 'Low' 
        },
      ]);

      setLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Zap size={20} className="text-white" fill="currentColor"/>
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            MoshengAI
          </span>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          <div className="text-xs font-semibold text-slate-500 uppercase px-4 mb-2 mt-4">Platform</div>
          <SidebarItem icon={LayoutDashboard} label="Overview" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <SidebarItem icon={MessageSquare} label="Conversations" active={activeTab === 'conversations'} onClick={() => setActiveTab('conversations')} />
          <SidebarItem icon={Database} label="Datasets" active={activeTab === 'datasets'} onClick={() => setActiveTab('datasets')} />
          
          <div className="text-xs font-semibold text-slate-500 uppercase px-4 mb-2 mt-6">Engineering</div>
          <SidebarItem icon={Terminal} label="Prompt Lab" active={activeTab === 'prompts'} onClick={() => setActiveTab('prompts')} />
          <SidebarItem icon={Cpu} label="Models & Keys" active={activeTab === 'models'} onClick={() => setActiveTab('models')} />
          <SidebarItem icon={Activity} label="Evaluation" active={activeTab === 'eval'} onClick={() => setActiveTab('eval')} />
        </nav>

        <div className="p-4 border-t border-slate-800">
          <SidebarItem icon={Settings} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Top Header */}
        <header className="h-16 bg-slate-900/50 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-6 z-10">
          <div className="md:hidden flex items-center gap-2">
            <span className="font-bold text-white">MoshengAI</span>
          </div>
          
          <div className="hidden md:block">
            <h1 className="text-lg font-semibold text-white capitalize">{activeTab}</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input 
                type="text" 
                placeholder="Search logs, prompts..." 
                className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-full pl-10 pr-4 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none w-64"
              />
            </div>
            <button className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-colors">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
          </div>
        </header>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-950">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && <DashboardView stats={stats} logs={logs} systemInfo={systemInfo} />}
            {activeTab === 'prompts' && <PromptLabView />}
            {activeTab === 'models' && <ModelsView models={models} />}
            {!['dashboard', 'prompts', 'models'].includes(activeTab) && (
              <div className="flex flex-col items-center justify-center h-96 text-slate-500">
                <Settings size={48} className="mb-4 opacity-50"/>
                <p>This module is under construction.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

