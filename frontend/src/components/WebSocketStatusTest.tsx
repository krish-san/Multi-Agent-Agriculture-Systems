// Add this component to test WebSocket status display specifically
import { useWebSocket } from '../hooks/useWebSocket';
import { WebSocketConnectionStatus } from '../services/websocketService';

export const WebSocketStatusTest = () => {
  const { connectionStatus, isConnected } = useWebSocket();
  
  console.log('🧪 WebSocketStatusTest render:', {
    connectionStatus,
    isConnected,
    timestamp: Date.now()
  });
  
  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      background: 'black', 
      color: 'white', 
      padding: '10px',
      borderRadius: '5px',
      zIndex: 9999,
      fontFamily: 'monospace'
    }}>
      <div>Status: {connectionStatus}</div>
      <div>Connected: {isConnected ? 'Yes' : 'No'}</div>
      <div>Enum Values:</div>
      {Object.entries(WebSocketConnectionStatus).map(([key, value]) => (
        <div key={key} style={{ 
          color: connectionStatus === value ? 'lime' : 'white' 
        }}>
          {key}: {value} {connectionStatus === value ? '← CURRENT' : ''}
        </div>
      ))}
    </div>
  );
};
