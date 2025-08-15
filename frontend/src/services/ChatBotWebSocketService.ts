import { WebSocketService, WebSocketConnectionStatus } from './websocketService';

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot' | 'system';
  timestamp: string;
  options?: Array<{ text: string; action: string }>;
}

export interface ChatBotWebSocketMessage {
  type: 'chat_message' | 'chat_typing' | 'chat_options';
  message_id?: string;
  content?: string;
  sender?: 'user' | 'bot' | 'system';
  options?: Array<{ text: string; action: string }>;
  timestamp: string;
}

export class ChatBotWebSocketService extends WebSocketService {
  private messageHandlers: Map<string, (message: ChatMessage) => void> = new Map();
  private typingHandlers: Map<string, (isTyping: boolean) => void> = new Map();
  
  constructor() {
    // Connect to the chat-specific WebSocket endpoint
    super({
      url: 'ws://localhost:8000/ws/chat'
    });
    
    // Set up the message handler for chat-specific messages
    this.onMessage('chat_internal', (wsMessage: any) => {
      if (!wsMessage) return;
      
      try {
        // Handle different message types
        const message = wsMessage as ChatBotWebSocketMessage;
        
        switch (message.type) {
          case 'chat_message':
            if (message.content && message.sender) {
              const chatMessage: ChatMessage = {
                id: message.message_id || `msg-${Date.now()}`,
                text: message.content,
                sender: message.sender,
                timestamp: message.timestamp,
                options: message.options
              };
              this.notifyMessageHandlers(chatMessage);
            }
            break;
            
          case 'chat_typing':
            this.notifyTypingHandlers(true);
            // Auto-reset typing after 3 seconds if no message arrives
            setTimeout(() => {
              this.notifyTypingHandlers(false);
            }, 3000);
            break;
            
          case 'chat_options':
            // Handle options sent separately
            if (message.message_id && message.options) {
              this.notifyOptionsUpdate(message.message_id, message.options);
            }
            break;
        }
      } catch (error) {
        console.error('Error processing chat message:', error);
      }
    });
  }
  
  // Send a chat message to the backend
  public sendMessage(text: string): boolean {
    const message: ChatBotWebSocketMessage = {
      type: 'chat_message',
      content: text,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    return this.send(message);
  }
  
  // Register a handler for incoming chat messages
  public onChatMessage(id: string, handler: (message: ChatMessage) => void): () => void {
    this.messageHandlers.set(id, handler);
    return () => {
      this.messageHandlers.delete(id);
    };
  }
  
  // Register a handler for typing indicators
  public onTypingIndicator(id: string, handler: (isTyping: boolean) => void): () => void {
    this.typingHandlers.set(id, handler);
    return () => {
      this.typingHandlers.delete(id);
    };
  }
  
  // Notify all registered message handlers
  private notifyMessageHandlers(message: ChatMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in chat message handler:', error);
      }
    });
  }
  
  // Notify all registered typing handlers
  private notifyTypingHandlers(isTyping: boolean): void {
    this.typingHandlers.forEach(handler => {
      try {
        handler(isTyping);
      } catch (error) {
        console.error('Error in typing indicator handler:', error);
      }
    });
  }
  
  // Update options for a specific message
  private notifyOptionsUpdate(messageId: string, options: Array<{ text: string; action: string }>): void {
    // This would need to be implemented if you want to update options after a message is sent
    console.log(`Received options update for message ${messageId}:`, options);
  }
}

// Create and export a singleton instance
export const chatBotService = new ChatBotWebSocketService();
