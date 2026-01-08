import { useEffect, useRef, useState } from 'react';
import './App.css';
import { AttributeBar } from './components/AttributeBar';
import { ChatBox } from './components/ChatBox';
import { InventoryGrid } from './components/InventoryGrid';
// import { INITIAL_GAME_STATE, INITIAL_MESSAGES } from './mockData';
import type { ChatResponse, GameState, Item, Message } from './types';
import { EventType } from './types';

function App() {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isInitialized = useRef(false);

  // Fetch initial state on mount
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const fetchInitialState = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/chat', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event: { type: EventType.INIT },
                player_input: '',
                current_state: null
            })
        });
        if (response.ok) {
          const data: ChatResponse = await response.json();
          setGameState(data.new_state);
          
          if (data.messages && data.messages.length > 0) {
            const newMessages = data.messages.map((msg, index) => ({
                id: Date.now() + index,
                sender: msg.sender,
                text: msg.text,
                options: msg.options
            }));
            setMessages(prev => [...prev, ...newMessages]);
          }
        }
      } catch (error) {
        console.error("Failed to fetch initial state:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialState();
  },[]);

  const processGameEvent = async (text: string, eventType: EventType, eventData?: { item_id?: string, quantity?: number }) => {
    // Add player message immediately
    const playerMsg = { id: Date.now(), sender: 'player' as const, text };
    setMessages(prev => [...prev, playerMsg]);
    
    // Guard clause if state isn't loaded yet (though UI should prevent this)
    if (!gameState) return;

    try {
      setIsLoading(true);
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: { type: eventType, ...eventData },
          player_input: text,
          current_state: gameState
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data: ChatResponse = await response.json();

      // Update State (Required by protocol)
      setGameState(data.new_state);

      // Add DM/System responses
      if (data.messages && data.messages.length > 0) {
        const newMessages = data.messages.map((msg, index) => ({
            id: Date.now() + 1 + index,
            sender: msg.sender,
            text: msg.text,
            options: msg.options
        }));
        setMessages(prev => [...prev, ...newMessages]);
      }

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'system',
        text: "错误：与后端的连接已丢失。"
      }]);
    } finally {
        setIsLoading(false);
    }
  };

  const handleSendMessage = (text: string) => {
    processGameEvent(text, EventType.MESSAGE);
  };

  const handleUseItem = (item: Item) => {
    processGameEvent(`使用 ${item.name}`, EventType.USE, { item_id: item.id, quantity: 1 });
  };

  const handleDropItem = (item: Item, mode: 'one' | 'half' | 'all') => {
    let quantity = 1;
    const currentQty = item.quantity || 1;
    
    if (mode === 'half') {
      quantity = Math.ceil(currentQty / 2);
    } else if (mode === 'all') {
      quantity = currentQty;
    }
    
    processGameEvent(`丢弃 ${quantity} 个 ${item.name}`, EventType.DROP, { item_id: item.id, quantity });
  };

  if (!gameState) {
    return <div className="loading-screen" style={{
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh', 
        color: '#0f0', 
        backgroundColor: '#111',
        fontFamily: 'monospace'
    }}>连接后室中... Connecting to The Backrooms...</div>;
  }

  return (
    <div className="game-container">
      {/* Left functionality - Chat */}
      <div className="chat-section">
        <div className="header">
          <h1>后室终端</h1>
          <div className="status-indicator">
            <span>层级: {gameState.level.replace("Level ", "")}</span>
            <span>状态: 在线</span>
          </div>
        </div>
        <ChatBox 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            isLoading={isLoading}
        />
      </div>

      {/* Right functionality - Sidebar */}
      <div className="sidebar-section">
        <AttributeBar attributes={gameState.attributes} vitals={gameState.vitals} />
        <InventoryGrid 
            items={gameState.inventory} 
            onUseItem={handleUseItem}
            onDropItem={handleDropItem}
            isLoading={isLoading}
        />
        
        <div className="panel">
          <h3 className="panel-header">位置信息</h3>
          <p style={{ color: '#888', fontSize: '0.9rem' }}>
            当前区域: <strong>宜居带</strong><br/>
            温度: 22°C<br/>
            光照等级: 中等
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
