import React, { useState, useEffect } from 'react';
import { Activity, Users, MessageSquare, TrendingUp, AlertTriangle, CheckCircle, Clock, Wifi, WifiOff } from 'lucide-react';

interface AgricultureAgent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
  domain: string;
  lastActivity: string;
  currentTask?: string;
  metrics: {
    queriesProcessed: number;
    averageResponseTime: number;
    accuracyRate: number;
  };
}

interface SystemStats {
  totalQueries: number;
  activeQueries: number;
  completedQueries: number;
  averageResponseTime: number;
  systemUptime: string;
  agentStatusCounts: {
    active: number;
    idle: number;
    busy: number;
    error: number;
    offline: number;
  };
}

interface AgricultureDashboardProps {
  className?: string;
}

const AgricultureDashboard: React.FC<AgricultureDashboardProps> = ({ className = '' }) => {
  const [agents, setAgents] = useState<AgricultureAgent[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Mock data for demonstration
  useEffect(() => {
    const mockAgents: AgricultureAgent[] = [
      {
        id: 'crop_selection_agent',
        name: 'Crop Selection Advisor',
        status: 'active',
        domain: 'Crop Selection',
        lastActivity: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
        currentTask: 'Analyzing soil conditions for wheat selection',
        metrics: {
          queriesProcessed: 45,
          averageResponseTime: 3.2,
          accuracyRate: 0.92
        }
      },
      {
        id: 'pest_management_agent',
        name: 'Pest Management Expert',
        status: 'busy',
        domain: 'Pest Management',
        lastActivity: new Date(Date.now() - 1 * 60 * 1000).toISOString(),
        currentTask: 'Processing pest identification request',
        metrics: {
          queriesProcessed: 28,
          averageResponseTime: 4.1,
          accuracyRate: 0.89
        }
      },
      {
        id: 'irrigation_agent',
        name: 'Irrigation Scheduler',
        status: 'idle',
        domain: 'Irrigation',
        lastActivity: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        metrics: {
          queriesProcessed: 33,
          averageResponseTime: 2.8,
          accuracyRate: 0.94
        }
      },
      {
        id: 'finance_agent',
        name: 'Finance & Policy Advisor',
        status: 'active',
        domain: 'Finance & Policy',
        lastActivity: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        currentTask: 'Checking loan eligibility criteria',
        metrics: {
          queriesProcessed: 19,
          averageResponseTime: 5.4,
          accuracyRate: 0.96
        }
      },
      {
        id: 'market_agent',
        name: 'Market Timing Analyst',
        status: 'error',
        domain: 'Market Timing',
        lastActivity: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        currentTask: 'Error: API connection timeout',
        metrics: {
          queriesProcessed: 12,
          averageResponseTime: 6.2,
          accuracyRate: 0.87
        }
      },
      {
        id: 'harvest_agent',
        name: 'Harvest Planner',
        status: 'idle',
        domain: 'Harvest Planning',
        lastActivity: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
        metrics: {
          queriesProcessed: 8,
          averageResponseTime: 3.9,
          accuracyRate: 0.91
        }
      },
      {
        id: 'input_materials_agent',
        name: 'Input Materials Advisor',
        status: 'offline',
        domain: 'Input Materials',
        lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        metrics: {
          queriesProcessed: 15,
          averageResponseTime: 4.5,
          accuracyRate: 0.88
        }
      }
    ];

    const mockStats: SystemStats = {
      totalQueries: 160,
      activeQueries: 3,
      completedQueries: 157,
      averageResponseTime: 4.2,
      systemUptime: '2d 14h 32m',
      agentStatusCounts: {
        active: 2,
        idle: 2,
        busy: 1,
        error: 1,
        offline: 1
      }
    };

    setAgents(mockAgents);
    setSystemStats(mockStats);
    setIsConnected(true);
    setLastUpdate(new Date().toISOString());

    // Simulate real-time updates
    const interval = setInterval(() => {
      setLastUpdate(new Date().toISOString());
      // In a real implementation, this would fetch from the API
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'busy':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'idle':
        return <Activity className="w-4 h-4 text-blue-500" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'offline':
        return <WifiOff className="w-4 h-4 text-gray-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'busy':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'idle':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'offline':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatLastActivity = (timestamp: string) => {
    const now = new Date();
    const activity = new Date(timestamp);
    const diffMs = now.getTime() - activity.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (!systemStats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Agricultural Advisory System</h2>
            <p className="text-gray-600">Multi-agent agricultural advisory dashboard</p>
          </div>
          <div className="flex items-center space-x-3">
            {isConnected ? (
              <div className="flex items-center text-green-600">
                <Wifi className="w-5 h-5 mr-2" />
                <span className="font-medium">Connected</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600">
                <WifiOff className="w-5 h-5 mr-2" />
                <span className="font-medium">Disconnected</span>
              </div>
            )}
            <div className="text-sm text-gray-500">
              Last update: {formatLastActivity(lastUpdate)}
            </div>
          </div>
        </div>
      </div>

      {/* System Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <MessageSquare className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Queries</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.totalQueries}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Queries</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.activeQueries}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.averageResponseTime}s</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">System Uptime</p>
              <p className="text-2xl font-bold text-gray-900">{systemStats.systemUptime}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Status Grid */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Agricultural Specialist Agents</h3>
          <p className="text-sm text-gray-600">Real-time status of all specialist agents in the system</p>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`border rounded-lg p-4 ${getStatusColor(agent.status)}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    {getStatusIcon(agent.status)}
                    <div className="ml-3">
                      <h4 className="font-medium">{agent.name}</h4>
                      <p className="text-sm opacity-75">{agent.domain}</p>
                    </div>
                  </div>
                  <span className="text-xs font-medium px-2 py-1 rounded-full border">
                    {agent.status.toUpperCase()}
                  </span>
                </div>

                {agent.currentTask && (
                  <div className="mb-3">
                    <p className="text-sm font-medium">Current Task:</p>
                    <p className="text-sm opacity-75">{agent.currentTask}</p>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="font-medium">{agent.metrics.queriesProcessed}</p>
                    <p className="opacity-75">Queries</p>
                  </div>
                  <div>
                    <p className="font-medium">{agent.metrics.averageResponseTime}s</p>
                    <p className="opacity-75">Avg Time</p>
                  </div>
                  <div>
                    <p className="font-medium">{(agent.metrics.accuracyRate * 100).toFixed(0)}%</p>
                    <p className="opacity-75">Accuracy</p>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-current opacity-25">
                  <p className="text-xs">
                    Last activity: {formatLastActivity(agent.lastActivity)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Activity className="w-5 h-5 mr-2 text-green-600" />
            <span>Restart All Agents</span>
          </button>
          <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            <span>View Analytics</span>
          </button>
          <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <AlertTriangle className="w-5 h-5 mr-2 text-yellow-600" />
            <span>System Diagnostics</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgricultureDashboard;
