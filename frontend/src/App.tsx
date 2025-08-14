import './App.css'
import AgentList from './components/AgentList'
import WorkflowVisualizer from './components/WorkflowVisualizer'
import WebSocketDebug from './components/WebSocketDebug'
import type { Agent } from './components/AgentList'
import type { Workflow } from './components/WorkflowVisualizer'
import { useWebSocket, useAgentUpdates, useWorkflowUpdates } from './hooks/useWebSocket'
import { WebSocketConnectionStatus } from './services/websocketService'
import { useMemo, useEffect } from 'react'

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
    id: 'agent-004',
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
    id: 'agent-005',
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

function App() {
  const { connectionStatus, isConnected, connect, disconnect, lastMessage } = useWebSocket({
    autoConnect: true,
    onMessage: (message) => {
      console.log('Received WebSocket message:', message);
    },
    onStatusChange: (status) => {
      console.log('WebSocket status changed:', status);
    }
  });

  // Monitor connection status changes in App component
  useEffect(() => {
    console.log(`🔄 App component: connectionStatus changed to "${connectionStatus}"`);
    console.log(`   isConnected: ${isConnected}`);
  }, [connectionStatus, isConnected]);

  // Debug function to check WebSocket status
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

  // Remove the WebSocketStatusTest since it's working now
  // const testComponent = <WebSocketStatusTest />;

  // Hook for real-time agent updates (reuse main connection)
  const { getAllAgents } = useAgentUpdates();
  
  // Hook for real-time workflow updates (reuse main connection)  
  const { getAllWorkflows, getActiveWorkflows } = useWorkflowUpdates();
  
  // Get real-time agent data
  const realTimeAgents = getAllAgents();
  
  // Get real-time workflow data
  const realTimeWorkflows = getAllWorkflows();
  const activeWorkflows = getActiveWorkflows();
  
  // Map backend status to frontend status types
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
  
  // Merge mock workflow with real-time updates
  const currentWorkflow = useMemo(() => {
    // If we have real-time workflows, use the first active one
    if (activeWorkflows.length > 0) {
      const rtWorkflow = activeWorkflows[0];
      
      // Convert real-time workflow data to frontend format
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
    
    // Otherwise, use mock data
    return mockWorkflow;
  }, [activeWorkflows]);
  
  // Merge mock data with real-time updates
  const mergedAgents = useMemo(() => {
    const agentMap = new Map<string, Agent>();
    
    // Start with mock data
    mockAgents.forEach(agent => {
      agentMap.set(agent.id, agent);
    });
    
    // Override with real-time data
    realTimeAgents.forEach(rtAgent => {
      const existingAgent = agentMap.get(rtAgent.id);
      if (existingAgent) {
        // Update existing agent with real-time data
        agentMap.set(rtAgent.id, {
          ...existingAgent,
          status: mapBackendStatusToFrontend(rtAgent.status),
          lastActivity: rtAgent.last_update,
          currentTask: rtAgent.details?.current_task || existingAgent.currentTask
        });
      } else {
        // Add new agent from real-time data
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
    // Show agent details or perform action
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

  // Count active agents
  const activeAgentCount = mergedAgents.filter(agent => 
    ['running', 'busy'].includes(agent.status)
  ).length;

  const handleStepClick = (step: any) => {
    console.log('Workflow step clicked:', step);
    // Show step details or perform action
  };

  return (
    <div className="dashboard">
      {/* <WebSocketStatusTest /> */}
      <header className="dashboard-header">
        <h1>AgentWeaver Dashboard</h1>
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
        <section className="agents-panel">
          <h2>
            Agent Status ({mergedAgents.length})
            {activeAgentCount > 0 && (
              <span className="active-count"> • {activeAgentCount} Active</span>
            )}
          </h2>
          <AgentList 
            agents={mergedAgents} 
            onAgentClick={handleAgentClick}
          />
        </section>

        <section className="workflow-panel">
          <h2>
            Workflow Execution
            {activeWorkflows.length > 0 && (
              <span className="active-count"> • {activeWorkflows.length} Active</span>
            )}
          </h2>
          <WorkflowVisualizer 
            workflow={currentWorkflow}
            onStepClick={handleStepClick}
            showDetails={true}
          />
          {lastMessage && (
            <div className="last-message">
              <h4>Last WebSocket Message:</h4>
              <pre>{JSON.stringify(lastMessage, null, 2)}</pre>
            </div>
          )}
        </section>
      </main>

      <footer className="dashboard-footer">
        <div className="system-stats">
          <span>Active Workflows: {activeWorkflows.length}</span>
          <span>Total Workflows: {realTimeWorkflows.length || 1}</span>
          <span>Connected Clients: {isConnected ? 1 : 0}</span>
          <span>Active Agents: {activeAgentCount}</span>
          <span>System Status: {isConnected ? 'Ready' : 'Disconnected'}</span>
        </div>
      </footer>
    </div>
  )
}

export default App
