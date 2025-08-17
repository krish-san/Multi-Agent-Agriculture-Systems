import '../App.css'
import './Dashboard.css'
import AgentList from './AgentList'
import WorkflowVisualizer from './WorkflowVisualizer'
import ChatBot from './ChatBot'
import type { Agent } from './AgentList'
import type { Workflow } from './WorkflowVisualizer'
import { useWebSocket, useAgentUpdates, useWorkflowUpdates } from '../hooks/useWebSocket'
import { WebSocketConnectionStatus } from '../services/websocketService'
import { useMemo, useEffect, useState } from 'react'

// Mock data for testing
const mockAgents: Agent[] = [
  {
    id: 'agent-001',
    name: 'Text Analysis Agent',
    status: 'running',
    lastActivity: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    currentTask: 'Analyzing sentiment in customer reviews',
    metrics: {
      tasksCompleted: 23,
      averageExecutionTime: 2.4,
      successRate: 0.96
    }
  },
  {
    id: 'agent-002',
    name: 'Data Processing Agent',
    status: 'idle',
    lastActivity: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    metrics: {
      tasksCompleted: 47,
      averageExecutionTime: 1.8,
      successRate: 0.98
    }
  },
  {
    id: 'agent-003',
    name: 'Harvest Planning Agent',
    status: 'idle',
    lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    metrics: {
      tasksCompleted: 56,
      averageExecutionTime: 4.1,
      successRate: 0.80
    }
  },
  {
    id: 'agent-004',
    name: 'API Interaction Agent',
    status: 'busy',
    lastActivity: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    currentTask: 'Fetching external API data',
    metrics: {
      tasksCompleted: 12,
      averageExecutionTime: 4.2,
      successRate: 0.91
    }
  },
  {
    id: 'agent-005',
    name: 'Backup Agent',
    status: 'error',
    lastActivity: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    currentTask: 'Failed: Connection timeout',
    metrics: {
      tasksCompleted: 8,
      averageExecutionTime: 3.1,
      successRate: 0.75
    }
  },
  {
    id: 'agent-006',
    name: 'Monitor Agent',
    status: 'offline',
    lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    metrics: {
      tasksCompleted: 156,
      averageExecutionTime: 0.8,
      successRate: 0.99
    }
  }
];

// Mock workflow data for testing
const mockWorkflow: Workflow = {
  id: 'workflow-001',
  name: 'Customer Review Analysis Pipeline',
  status: 'running',
  progress: 0.6,
  startTime: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
  totalDuration: 10 * 60 * 1000,
  steps: [
    {
      id: 'step-1',
      name: 'Initialize Data Source',
      status: 'completed',
      startTime: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() - 9 * 60 * 1000).toISOString(),
      duration: 45000,
      output: 'Connected to customer review database\nLoaded 1,247 reviews for processing',
      agent: 'agent-002'
    },
    {
      id: 'step-2',
      name: 'Text Preprocessing',
      status: 'completed',
      startTime: new Date(Date.now() - 9 * 60 * 1000).toISOString(),
      endTime: new Date(Date.now() - 7 * 60 * 1000).toISOString(),
      duration: 120000,
      output: 'Cleaned and tokenized text data\nRemoved stop words and normalized format',
      agent: 'agent-001'
    },
    {
      id: 'step-3',
      name: 'Sentiment Analysis',
      status: 'in-progress',
      startTime: new Date(Date.now() - 7 * 60 * 1000).toISOString(),
      agent: 'agent-001'
    },
    {
      id: 'step-4',
      name: 'Category Classification',
      status: 'pending',
      agent: 'agent-003'
    },
    {
      id: 'step-5',
      name: 'Generate Report',
      status: 'pending',
      agent: 'agent-002'
    }
  ],
  metadata: {
    priority: 'high',
    source: 'customer_feedback_system',
    estimated_completion: new Date(Date.now() + 5 * 60 * 1000).toISOString()
  }
};

function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  const { connectionStatus, isConnected, connect, disconnect, lastMessage } = useWebSocket({
    autoConnect: true,
    onMessage: (message) => {
      console.log('Received WebSocket message:', message);
    },
    onStatusChange: (status) => {
      console.log('WebSocket status changed:', status);
    }
  });

  useEffect(() => {
    console.log(`🔄 Dashboard component: connectionStatus changed to "${connectionStatus}"`);
    console.log(`   isConnected: ${isConnected}`);
  }, [connectionStatus, isConnected]);

  (window as any).debugWebSocket = () => {
    console.log('=== WebSocket Debug Info ===');
    console.log('Current connection status:', connectionStatus);
    console.log('Is connected:', isConnected);
    console.log('Last message:', lastMessage);
    console.log('Status enum values:', WebSocketConnectionStatus);
    console.log('Current status type:', typeof connectionStatus);
    console.log('Current status comparison:', connectionStatus === WebSocketConnectionStatus.CONNECTED);
    console.log('============================');
  };

  const { getAllAgents } = useAgentUpdates();
  const { getAllWorkflows, getActiveWorkflows } = useWorkflowUpdates();

  const realTimeAgents = getAllAgents();
  const realTimeWorkflows = getAllWorkflows();
  const activeWorkflows = getActiveWorkflows();

  const mapBackendStatusToFrontend = (backendStatus: string): Agent['status'] => {
    const statusMap: Record<string, Agent['status']> = {
      'idle': 'idle',
      'running': 'running',
      'busy': 'busy',
      'active': 'running',
      'error': 'error',
      'failed': 'error',
      'offline': 'offline',
      'disconnected': 'offline'
    };
    return statusMap[backendStatus?.toLowerCase()] || 'idle';
  };

  const currentWorkflow = useMemo(() => {
    if (activeWorkflows.length > 0) {
      const rtWorkflow = activeWorkflows[0];
      return {
        id: rtWorkflow.id,
        name: rtWorkflow.details?.name || `Workflow ${rtWorkflow.id}`,
        status: rtWorkflow.status as Workflow['status'],
        progress: rtWorkflow.progress || 0,
        startTime: rtWorkflow.details?.started_at,
        endTime: rtWorkflow.details?.completed_at,
        totalDuration: rtWorkflow.details?.execution_time ? rtWorkflow.details.execution_time * 1000 : undefined,
        steps: rtWorkflow.details?.steps || mockWorkflow.steps.map((step, index) => ({
          ...step,
          status: index < (rtWorkflow.details?.steps_completed || 0) ? 'completed' as const : 
                  index === (rtWorkflow.details?.steps_completed || 0) ? 'in-progress' as const : 
                  'pending' as const
        })),
        metadata: rtWorkflow.details
      } as Workflow;
    }
    return mockWorkflow;
  }, [activeWorkflows]);

  const mergedAgents = useMemo(() => {
    const agentMap = new Map<string, Agent>();
    mockAgents.forEach(agent => {
      agentMap.set(agent.id, agent);
    });
    realTimeAgents.forEach(rtAgent => {
      const existingAgent = agentMap.get(rtAgent.id);
      if (existingAgent) {
        agentMap.set(rtAgent.id, {
          ...existingAgent,
          status: mapBackendStatusToFrontend(rtAgent.status),
          lastActivity: rtAgent.last_update,
          currentTask: rtAgent.details?.current_task || existingAgent.currentTask
        });
      } else {
        agentMap.set(rtAgent.id, {
          id: rtAgent.id,
          name: rtAgent.details?.name || `Agent ${rtAgent.id}`,
          status: mapBackendStatusToFrontend(rtAgent.status),
          lastActivity: rtAgent.last_update,
          currentTask: rtAgent.details?.current_task,
          metrics: rtAgent.details?.metrics || {
            tasksCompleted: 0,
            averageExecutionTime: 0,
            successRate: 1.0
          }
        });
      }
    });
    return Array.from(agentMap.values());
  }, [realTimeAgents]);

  const handleAgentClick = (agent: Agent) => {
    console.log('Agent clicked:', agent);
  };

  const getConnectionStatusDisplay = () => {
    switch (connectionStatus) {
      case WebSocketConnectionStatus.CONNECTED:
        return '🟢 Connected';
      case WebSocketConnectionStatus.CONNECTING:
        return '🟡 Connecting';
      case WebSocketConnectionStatus.RECONNECTING:
        return '🟠 Reconnecting';
      case WebSocketConnectionStatus.ERROR:
        return '🔴 Error';
      default:
        return '🔴 Disconnected';
    }
  };

  const handleConnectionToggle = () => {
    if (isConnected) {
      disconnect();
    } else {
      connect();
    }
  };

  const activeAgentCount = mergedAgents.filter(agent => 
    ['running', 'busy'].includes(agent.status)
  ).length;

  const handleStepClick = (step: any) => {
    console.log('Workflow step clicked:', step);
  };

  return (
    <div className="dashboard-content">
      <header className="dashboard-header">
        <div className="search-bar">
          <input 
            type="text" 
            placeholder="Search workflows, agents, or reports..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className="search-btn">Search</button>
        </div>
        <div className="header-info">
          <span 
            className="connection-status"
            onClick={handleConnectionToggle}
            style={{ cursor: 'pointer' }}
            title={`Click to toggle connection. Current: ${connectionStatus}`}
          >
            {getConnectionStatusDisplay()}
          </span>
          <span className="timestamp">{new Date().toLocaleTimeString()}</span>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Metrics Row */}
        <div className="metrics-row" style={{ 
          gridColumn: "1 / -1", 
          display: "flex", 
          gap: "1.5rem", 
          marginBottom: "1.5rem" 
        }}>
          <div className="metric-card" style={{
            flex: 1,
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.2rem",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
            display: "flex",
            flexDirection: "column",
            transition: "all 0.3s ease",
            border: "1px solid rgba(240, 242, 245, 0.8)",
            position: "relative",
            overflow: "hidden"
          }}>
            <span style={{ fontSize: "0.8rem", color: "#6B7280", fontWeight: "500" }}>Active Agents</span>
            <div style={{ display: "flex", alignItems: "baseline", marginTop: "0.5rem" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: "700", color: "#18A1CC" }}>{activeAgentCount}</span>
              <span style={{ fontSize: "1rem", marginLeft: "0.5rem", color: "#22C55E" }}>/{mergedAgents.length}</span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "#6B7280", marginTop: "0.5rem" }}>Working on tasks</span>
            <div style={{ 
              position: "absolute", 
              right: "-10px", 
              bottom: "-10px", 
              width: "60px", 
              height: "60px", 
              borderRadius: "50%", 
              backgroundColor: "rgba(24, 161, 204, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem"
            }}>🤖</div>
          </div>
          
          <div className="metric-card" style={{
            flex: 1,
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.2rem",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
            display: "flex",
            flexDirection: "column",
            transition: "all 0.3s ease",
            border: "1px solid rgba(240, 242, 245, 0.8)",
            position: "relative",
            overflow: "hidden"
          }}>
            <span style={{ fontSize: "0.8rem", color: "#6B7280", fontWeight: "500" }}>Active Workflows</span>
            <div style={{ display: "flex", alignItems: "baseline", marginTop: "0.5rem" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: "700", color: "#DFBA47" }}>{activeWorkflows.length}</span>
              <span style={{ fontSize: "1rem", marginLeft: "0.5rem", color: "#22C55E" }}>/{realTimeWorkflows.length || 1}</span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "#6B7280", marginTop: "0.5rem" }}>In execution</span>
            <div style={{ 
              position: "absolute", 
              right: "-10px", 
              bottom: "-10px", 
              width: "60px", 
              height: "60px", 
              borderRadius: "50%", 
              backgroundColor: "rgba(223, 186, 71, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem"
            }}>📊</div>
          </div>
          
          <div className="metric-card" style={{
            flex: 1,
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "1.2rem",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
            display: "flex",
            flexDirection: "column",
            transition: "all 0.3s ease",
            border: "1px solid rgba(240, 242, 245, 0.8)",
            position: "relative",
            overflow: "hidden"
          }}>
            <span style={{ fontSize: "0.8rem", color: "#6B7280", fontWeight: "500" }}>Overall Progress</span>
            <div style={{ display: "flex", alignItems: "baseline", marginTop: "0.5rem" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: "700", color: "#22C55E" }}>
                {Math.round(currentWorkflow.progress * 100)}%
              </span>
            </div>
            <div style={{ marginTop: "0.5rem", height: "6px", backgroundColor: "rgba(34, 197, 94, 0.1)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ 
                height: "100%", 
                width: `${Math.round(currentWorkflow.progress * 100)}%`, 
                backgroundColor: "#22C55E",
                borderRadius: "3px",
                transition: "width 0.5s ease"
              }}></div>
            </div>
            <span style={{ fontSize: "0.75rem", color: "#6B7280", marginTop: "0.5rem" }}>Tasks completed</span>
            <div style={{ 
              position: "absolute", 
              right: "-10px", 
              bottom: "-10px", 
              width: "60px", 
              height: "60px", 
              borderRadius: "50%", 
              backgroundColor: "rgba(34, 197, 94, 0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem"
            }}>✅</div>
          </div>
        </div>

        {/* Main content with fixed card heights and widths */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", gridColumn: "1 / -1" }}>
          {/* Agent Status Card - Left Column */}
          <section className="agents-panel dashboard-card" style={{ height: "600px", overflow: "hidden" }}>
            <div className="dashboard-card-header">
              <h3 className="dashboard-card-title">
                <span>Agent Status ({mergedAgents.length})</span>
                {activeAgentCount > 0 && (
                  <span className="active-count"> • {activeAgentCount} Active</span>
                )}
              </h3>
              <div className="card-actions">
                <span style={{ cursor: 'pointer', fontSize: '0.9rem', opacity: '0.7' }} title="Filter Agents">🔍</span>
              </div>
            </div>
            <div className="dashboard-card-body" style={{ height: "calc(100% - 120px)", overflowY: "auto" }}>
              <AgentList 
                agents={mergedAgents} 
                onAgentClick={handleAgentClick}
              />
            </div>
            <div className="dashboard-card-footer">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
            </div>
          </section>

          {/* Right Column Cards - Same height as Agent Status Card */}
          <div style={{ display: "flex", flexDirection: "column", height: "600px", gap: "1.5rem" }}>
            {/* Workflow Execution Card - Top Half */}
            <div className="dashboard-card" style={{ flex: "1", overflow: "hidden" }}>
              <div className="dashboard-card-header">
                <h3 className="dashboard-card-title">
                  <span>Workflow Execution</span>
                  {activeWorkflows.length > 0 && (
                    <span className="active-count"> • {activeWorkflows.length} Active</span>
                  )}
                </h3>
                <div className="card-actions">
                  <span style={{ cursor: 'pointer', fontSize: '1.1rem', opacity: '0.7' }} title="View all workflows">⋮</span>
                </div>
              </div>
              <div className="dashboard-card-body" style={{ height: "calc(100% - 120px)", overflowY: "auto" }}>
                <WorkflowVisualizer 
                  workflow={currentWorkflow}
                  onStepClick={handleStepClick}
                  showDetails={false}
                />
              </div>
              <div className="dashboard-card-footer">
                <span>Started: {new Date(currentWorkflow.startTime).toLocaleString()}</span>
                <div className="card-actions-footer">
                  <button className="action-button">View Details</button>
                  <button className="action-button">Export Data</button>
                </div>
              </div>
            </div>

            {/* Execution Steps Card - Bottom Half */}
            <div className="dashboard-card" style={{ flex: "1", overflow: "hidden" }}>
              <div className="dashboard-card-header">
                <h3 className="dashboard-card-title">
                  <span>Execution Steps</span>
                  <span className="active-count"> • {currentWorkflow.steps.filter(step => step.status === 'in-progress').length} Running</span>
                </h3>
                <div className="card-actions">
                  <span style={{ cursor: 'pointer', fontSize: '0.9rem', opacity: '0.7' }} title="Expand all steps">📊</span>
                </div>
              </div>
              <div className="dashboard-card-body" style={{ padding: '1rem', height: "calc(100% - 120px)", overflowY: "auto" }}>
                <div className="steps-container">
                  {currentWorkflow.steps.map((step) => (
                    <div 
                      key={step.id}
                      onClick={() => handleStepClick(step)}
                      className="step-item"
                      style={{ 
                        marginBottom: '0.75rem', 
                        padding: '0.85rem 1rem', 
                        backgroundColor: '#f8f9fa', 
                        borderRadius: '8px',
                        borderLeft: `4px solid ${step.status === 'completed' ? '#22C55E' : 
                                               step.status === 'in-progress' ? '#18A1CC' : 
                                               step.status === 'failed' ? '#EF4444' : '#F59E0B'}`,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                        transition: 'all 0.25s ease',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <strong>{step.name}</strong>
                        <span style={{ 
                          padding: '0.25rem 0.75rem',
                          fontSize: '0.7rem',
                          fontWeight: '600',
                          borderRadius: '30px',
                          textTransform: 'uppercase',
                          backgroundColor: step.status === 'completed' ? 'rgba(34, 197, 94, 0.1)' :
                                          step.status === 'in-progress' ? 'rgba(24, 161, 204, 0.1)' :
                                          step.status === 'failed' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                          color: step.status === 'completed' ? '#22C55E' : 
                                step.status === 'in-progress' ? '#18A1CC' : 
                                step.status === 'failed' ? '#EF4444' : '#F59E0B'
                        }}>
                          {step.status.replace('-', ' ')}
                        </span>
                      </div>
                      {step.agent && (
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          marginTop: '0.5rem',
                          padding: '0.35rem 0.75rem',
                          backgroundColor: 'rgba(0,0,0,0.03)',
                          borderRadius: '6px',
                          width: 'fit-content'
                        }}>
                          <span style={{ fontSize: '0.8rem', marginRight: '0.25rem', opacity: '0.7' }}>🤖</span>
                          <small style={{ color: '#6B7280', fontSize: '0.8rem', fontWeight: '500' }}>
                            Agent: {step.agent}
                          </small>
                        </div>
                      )}
                      {step.status === 'completed' && step.output && (
                        <div style={{ marginTop: '0.5rem', position: 'relative' }}>
                          <div style={{ 
                            height: '1.5rem', 
                            overflow: 'hidden',
                            fontSize: '0.75rem',
                            color: '#6B7280',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            position: 'relative',
                            paddingRight: '3rem'
                          }}>
                            <span style={{ opacity: '0.7' }}>Output: </span>
                            {step.output?.split('\n')[0]}
                            <span style={{ 
                              position: 'absolute',
                              right: '0',
                              top: '0',
                              padding: '0 0.5rem',
                              backgroundColor: 'rgba(248,249,250,0.8)',
                              color: '#18A1CC',
                              fontSize: '0.7rem',
                              fontWeight: '500'
                            }}>View</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <div className="dashboard-card-footer">
                <div>
                  <span>Total Steps: {currentWorkflow.steps.length}</span>
                  <span style={{ 
                    marginLeft: '1rem',
                    fontWeight: '500',
                    color: currentWorkflow.status === 'completed' ? '#22C55E' :
                           currentWorkflow.status === 'running' ? '#18A1CC' : '#6B7280'
                  }}>
                    {Math.round(currentWorkflow.progress * 100)}% Complete
                  </span>
                </div>
                <div className="card-actions-footer">
                  <button className="action-button">Expand All</button>
                  <button className="action-button">Log View</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {lastMessage && (
          <section className="last-message-panel">
            <h2>WebSocket Debug</h2>
            <div className="last-message">
              <h4>Last Message:</h4>
              <pre>{JSON.stringify(lastMessage, null, 2)}</pre>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;
