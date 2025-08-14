import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  WebSocketService, 
  WebSocketConnectionStatus,
  defaultWebSocketService 
} from '../services/websocketService';
import type { AllWebSocketMessages } from '../services/websocketService';

interface UseWebSocketOptions {
  service?: WebSocketService;
  autoConnect?: boolean;
  onMessage?: (message: AllWebSocketMessages) => void;
  onStatusChange?: (status: WebSocketConnectionStatus) => void;
}

interface UseWebSocketReturn {
  connectionStatus: WebSocketConnectionStatus;
  lastMessage: AllWebSocketMessages | null;
  send: (message: object) => boolean;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    service = defaultWebSocketService,
    autoConnect = true,
    onMessage,
    onStatusChange
  } = options;

  // Generate unique handler ID to prevent conflicts
  const handlerIdRef = useRef(`react-hook-${Math.random().toString(36).substr(2, 9)}`);
  const handlerId = handlerIdRef.current;

  const [connectionStatus, setConnectionStatus] = useState<WebSocketConnectionStatus>(() => {
    const initialStatus = service.getConnectionStatus();
    console.log(`🚀 useWebSocket initializing with status: ${initialStatus}`);
    return initialStatus;
  });
  const [lastMessage, setLastMessage] = useState<AllWebSocketMessages | null>(null);
  
  // Use refs to avoid stale closures in effect dependencies
  const onMessageRef = useRef(onMessage);
  const onStatusChangeRef = useRef(onStatusChange);
  
  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);
  
  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
  }, [onStatusChange]);

  // Handle connection status changes
  useEffect(() => {
    console.log(`🔗 Setting up WebSocket status change handler (${handlerId})`);
    const unsubscribe = service.onStatusChange(handlerId, (status) => {
      console.log(`🎯 React hook (${handlerId}) received status change: ${status}`);
      console.log(`   Previous React state: ${connectionStatus}`);
      setConnectionStatus(prevStatus => {
        console.log(`   Updating React state: ${prevStatus} → ${status}`);
        return status;
      });
      onStatusChangeRef.current?.(status);
    });

    return unsubscribe;
  }, [service, handlerId]);

  // Handle incoming messages
  useEffect(() => {
    const unsubscribe = service.onMessage(handlerId, (message) => {
      setLastMessage(message);
      onMessageRef.current?.(message);
    });

    return unsubscribe;
  }, [service, handlerId]);

  // Auto-connect on mount if enabled (only once)
  useEffect(() => {
    let isActive = true; // Track if component is still mounted
    
    if (autoConnect) {
      // Only connect if we're disconnected and not already connecting
      const currentStatus = service.getConnectionStatus();
      console.log(`🚀 Auto-connect check: current status = "${currentStatus}"`);
      
      if (currentStatus === WebSocketConnectionStatus.DISCONNECTED && isActive) {
        console.log('Auto-connecting WebSocket...');
        service.connect();
      } else {
        console.log(`Not auto-connecting: status is "${currentStatus}", isActive: ${isActive}`);
      }
    }

    // Cleanup on unmount
    return () => {
      isActive = false;
      // Don't disconnect in StrictMode development (it causes issues)
      // The WebSocket service will handle connection management
      // if (!autoConnect) {
      //   service.disconnect();
      // }
    };
  }, [service, autoConnect]); // Keep minimal dependencies but ensure stability

  const connect = useCallback(() => {
    service.connect();
  }, [service]);

  const disconnect = useCallback(() => {
    service.disconnect();
  }, [service]);

  const send = useCallback((message: object): boolean => {
    return service.send(message);
  }, [service]);

  const isConnected = connectionStatus === WebSocketConnectionStatus.CONNECTED;

  return {
    connectionStatus,
    lastMessage,
    send,
    connect,
    disconnect,
    isConnected
  };
};

// Hook for workflow updates specifically
export const useWorkflowUpdates = () => {
  const [workflows, setWorkflows] = useState<Map<string, any>>(new Map());
  
  useWebSocket({
    autoConnect: false, // Don't auto-connect, reuse main connection
    onMessage: (message) => {
      if (message.type === 'workflow_update') {
        console.log('📊 Workflow update received:', message);
        const workflowMessage = message as any; // Type assertion for workflow message
        
        setWorkflows(prev => {
          const updated = new Map(prev);
          const existingWorkflow = updated.get(workflowMessage.workflow_id) || {};
          
          updated.set(workflowMessage.workflow_id, {
            ...existingWorkflow,
            id: workflowMessage.workflow_id,
            status: workflowMessage.status,
            current_step: workflowMessage.current_step,
            progress: workflowMessage.progress,
            last_update: message.timestamp,
            event: workflowMessage.event,
            details: workflowMessage.details
          });
          
          console.log('📊 Updated workflows:', Array.from(updated.values()));
          return updated;
        });
      }
    }
  });

  const getWorkflow = (workflowId: string) => workflows.get(workflowId);
  const getAllWorkflows = () => Array.from(workflows.values());
  const getActiveWorkflows = () => Array.from(workflows.values()).filter(w => w.status === 'running');

  return {
    workflows,
    getWorkflow,
    getAllWorkflows,
    getActiveWorkflows
  };
};

// Hook for agent updates specifically
export const useAgentUpdates = () => {
  const [agents, setAgents] = useState<Map<string, any>>(new Map());
  
  useWebSocket({
    autoConnect: false, // Don't auto-connect, reuse main connection
    onMessage: (message) => {
      if (message.type === 'agent_update') {
        console.log('🤖 Agent update received:', message);
        const agentMessage = message as any; // Type assertion for agent message
        
        setAgents(prev => {
          const updated = new Map(prev);
          const existingAgent = updated.get(agentMessage.agent_id) || {};
          
          updated.set(agentMessage.agent_id, {
            ...existingAgent,
            id: agentMessage.agent_id,
            status: agentMessage.status,
            previous_status: agentMessage.previous_status,
            last_update: message.timestamp,
            details: agentMessage.details
          });
          
          console.log('🤖 Updated agents:', Array.from(updated.values()));
          return updated;
        });
      }
    }
  });

  const getAgent = (agentId: string) => agents.get(agentId);
  const getAllAgents = () => Array.from(agents.values());
  const getActiveAgents = () => Array.from(agents.values()).filter(a => 
    ['running', 'busy', 'active'].includes((a as any).status?.toLowerCase())
  );

  return {
    agents,
    getAgent,
    getAllAgents,
    getActiveAgents
  };
};

// Hook for system notifications
export const useSystemNotifications = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  
  const { connectionStatus, lastMessage, ...websocketControls } = useWebSocket({
    autoConnect: false, // Don't auto-connect, reuse main connection
    onMessage: (message) => {
      if (message.type === 'system_notification') {
        const notification = {
          id: Date.now().toString(),
          ...message,
          received_at: new Date().toISOString()
        };
        
        setNotifications(prev => [notification, ...prev].slice(0, 50)); // Keep last 50 notifications
      }
    }
  });

  const clearNotifications = () => setNotifications([]);
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return {
    notifications,
    clearNotifications,
    removeNotification,
    connectionStatus,
    lastMessage,
    ...websocketControls
  };
};
