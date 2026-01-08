import { useState } from 'react';
import './App.css';
import { AttributeBar } from './components/AttributeBar';
import { ChatBox } from './components/ChatBox';
import { InventoryGrid } from './components/InventoryGrid';
import type { Attributes, ChatResponse, Item, Vitals } from './types';

interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system';
  text: string;
}

function App() {
  // Mock State
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, sender: 'system' as const, text: 'System Initialized. Connection to Backrooms established.' },
    { id: 2, sender: 'dm' as const, text: 'You wake up in a damp, yellow room. The hum of fluorescent lights is deafening. You see exits to the North and East.' }
  ]);

  const [attributes, setAttributes] = useState<Attributes>({
    STR: 12,
    DEX: 14,
    CON: 13,
    INT: 16,
    WIS: 10,
    CHA: 8
  });

  const [vitals, setVitals] = useState<Vitals>({
    hp: 18,
    maxHp: 20,
    sanity: 85,
    maxSanity: 100
  });

  const [inventory, setInventory] = useState<(Item | null)[]>([
    { id: '1', name: 'Almond Water', icon: '💧' },
    { id: '2', name: 'Flashlight', icon: '🔦' },
    null, null, null, null
  ]);

  const handleSendMessage = async (text: string) => {
    // Add player message immediately
    const playerMsg = { id: Date.now(), sender: 'player' as const, text };
    setMessages(prev => [...prev, playerMsg]);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_input: text,
          current_state: {
            level: "Level 1", // Hardcoded for now, should be state
            attributes,
            vitals,
            inventory
          }
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data: ChatResponse = await response.json();

      // Add DM response
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: data.sender,
        text: data.message
      }]);

      // Update State if provided
      if (data.new_state) {
        if (data.new_state.vitals) setVitals(data.new_state.vitals);
        if (data.new_state.attributes) setAttributes(data.new_state.attributes);
        if (data.new_state.inventory) setInventory(data.new_state.inventory);
      }

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'system',
        text: "Error: Connection to backend lost."
      }]);
    }
  };

  return (
    <div className="game-container">
      {/* Left functionality - Chat */}
      <div className="chat-section">
        <div className="header">
          <h1>BACKROOMS TERMINAL</h1>
          <div className="status-indicator">
            <span>LEVEL: 1</span>
            <span>STATUS: ONLINE</span>
          </div>
        </div>
        <ChatBox messages={messages} onSendMessage={handleSendMessage} />
      </div>

      {/* Right functionality - Sidebar */}
      <div className="sidebar-section">
        <AttributeBar attributes={attributes} vitals={vitals} />
        <InventoryGrid items={inventory} />
        
        <div className="panel">
          <h3 className="panel-header">Location Info</h3>
          <p style={{ color: '#888', fontSize: '0.9rem' }}>
            Current Zone: <strong>Habitable Zone</strong><br/>
            Temperature: 22°C<br/>
            Light Level: Moderate
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
