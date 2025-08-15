import { useState, useEffect, useCallback } from 'react';
import { chatBotService } from '../services/ChatBotWebSocketService';
import type { ChatMessage } from '../services/ChatBotWebSocketService';
import { WebSocketConnectionStatus } from '../services/websocketService';

interface UseChatBotOptions {
  initialMessages?: ChatMessage[];
  autoConnect?: boolean;
}

export const useChatBot = (options: UseChatBotOptions = {}) => {
  const { 
    initialMessages = [],
    autoConnect = true
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<WebSocketConnectionStatus>(
    chatBotService.getConnectionStatus()
  );
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  // Handle WebSocket connection status changes
  useEffect(() => {
    const unsubscribe = chatBotService.onStatusChange('chat-hook', (status) => {
      setConnectionStatus(status);
      
      // If we reconnected and had a pending message, try to send it
      if (status === WebSocketConnectionStatus.CONNECTED && pendingMessage) {
        sendMessage(pendingMessage);
        setPendingMessage(null);
      }
    });
    
    return unsubscribe;
  }, [pendingMessage]);

  // Handle incoming chat messages
  useEffect(() => {
    const unsubscribe = chatBotService.onChatMessage('chat-hook', (message) => {
      setMessages(prevMessages => {
        // If this is a bot message, replace any typing indicator
        if (message.sender === 'bot') {
          setIsTyping(false);
          // Remove any typing indicators (these would be handled separately)
          return [...prevMessages, message];
        }
        return [...prevMessages, message];
      });
    });
    
    return unsubscribe;
  }, []);

  // Handle typing indicators
  useEffect(() => {
    const unsubscribe = chatBotService.onTypingIndicator('chat-hook', (typing) => {
      setIsTyping(typing);
    });
    
    return unsubscribe;
  }, []);

  // Connect to WebSocket when component mounts if autoConnect is true
  useEffect(() => {
    if (autoConnect && connectionStatus === WebSocketConnectionStatus.DISCONNECTED) {
      chatBotService.connect();
    }
    
    // We're not disconnecting on unmount because other components might use the same service
  }, [autoConnect, connectionStatus]);

  // Send a message
  const sendMessage = useCallback((text: string): boolean => {
    // Don't send empty messages
    if (!text.trim()) return false;
    
    // Create user message for local state
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      text,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    // Add to messages immediately for responsive UI
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Try to send via WebSocket
    if (connectionStatus === WebSocketConnectionStatus.CONNECTED) {
      const sent = chatBotService.sendMessage(text);
      
      // If sent successfully, add typing indicator
      if (sent) {
        setIsTyping(true);
      } else {
        // Save for retry
        setPendingMessage(text);
      }
      
      return sent;
    } else {
      // Not connected, save message for later
      setPendingMessage(text);
      
      // Try to connect
      if (connectionStatus === WebSocketConnectionStatus.DISCONNECTED) {
        chatBotService.connect();
      }
      
      return false;
    }
  }, [connectionStatus]);

  const connect = useCallback(() => {
    chatBotService.connect();
  }, []);

  const disconnect = useCallback(() => {
    chatBotService.disconnect();
  }, []);

  return {
    messages,
    isTyping,
    connectionStatus,
    isConnected: connectionStatus === WebSocketConnectionStatus.CONNECTED,
    sendMessage,
    connect,
    disconnect
  };
};

export default useChatBot;
