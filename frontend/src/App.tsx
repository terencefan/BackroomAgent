import { useEffect, useRef, useState } from 'react';
import './App.css';
import { AttributeBar } from './components/AttributeBar';
import { ChatBox } from './components/ChatBox';
import { InventoryGrid } from './components/InventoryGrid';
// import { INITIAL_GAME_STATE, INITIAL_MESSAGES } from './mockData';
import type { GameState, Item, Message, StreamChunk } from './types';
import { EventType, StreamChunkType } from './types';

function App() {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLevelTransition, setIsLevelTransition] = useState(false);
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
        
        if (!response.ok) throw new Error('Network response was not ok');

        const reader = response.body?.getReader();
        if (!reader) throw new Error('Response body is not readable');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const chunk = JSON.parse(line);
                    await processStreamChunk(chunk);
                } catch (e) {
                    console.error('Error parsing JSON chunk', e);
                }
            }
        }
        setIsLoading(false);

      } catch (error) {
        console.error("Failed to fetch initial state:", error);
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

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Response body is not readable');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const chunk = JSON.parse(line);
            await processStreamChunk(chunk);
          } catch (e) {
            console.error('Error parsing JSON chunk', e);
          }
        }
      }
      setIsLoading(false);

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'system',
        text: "错误：与后端的连接已丢失。"
      }]);
      setIsLoading(false);
    } 
  };

  const processStreamChunk = async (chunk: StreamChunk) => {
    switch (chunk.type) {
      case StreamChunkType.MESSAGE:
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: chunk.sender || 'dm',
          text: chunk.text || ''
        }]);
        break;
      
      case StreamChunkType.DICE_ROLL:
        // Handle Dice Roll Visualization
        // For now, let's just show it as a system message
        setMessages(prev => [...prev, {
            id: Date.now() + 1,
            sender: 'system',
            text: `🎲 [${chunk.dice.type}] ${chunk.dice.reason || 'Check'}: ${chunk.dice.result}`
        }]);
        break;

      case StreamChunkType.STATE:
        // Update Game State
        if (chunk.state) {
            // Check for level change to trigger potential animation
            if (gameState && chunk.state.level !== gameState.level) {
                // Trigger Fade Out
                setIsLevelTransition(true);
                // Wait for fade out animation
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Update State (while invisible)
                setGameState(chunk.state);
                
                // Small delay to ensure render phase completes before fade in starts (optional but safer)
                await new Promise(resolve => setTimeout(resolve, 50));
                
                // Trigger Fade In
                setIsLevelTransition(false);
            } else {
                setGameState(chunk.state);
            }
        }
        break;

      case StreamChunkType.SUGGESTIONS:
        // Append suggestions to the LAST message if possible
        setMessages(prev => {
            if (prev.length === 0) return prev;
            const lastMsg = { ...prev[prev.length - 1] };
            // Overwrite options
            lastMsg.options = chunk.options;
            return [...prev.slice(0, -1), lastMsg];
        });
        break;
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

  const formatTime = (totalMinutes: number) => {
    const hours = Math.floor(totalMinutes / 60) % 24;
    const minutes = totalMinutes % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
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
    <div className={`game-container ${isLevelTransition ? 'fade-out' : 'fade-in'}`}>
      {/* Left functionality - Chat */}
      <div className="chat-section">
        <div className="header">
          <h1>后室终端</h1>
          <div className="status-indicator">
            <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>⏱ {formatTime(gameState.time || 480)}</span>
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
          <p style={{ color: '#888', fontSize: '0.9rem', lineHeight: '1.6' }}>
            层级: <strong style={{ color: '#4ade80', fontSize: '1.1em' }}>{gameState.level}</strong><br/>
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
