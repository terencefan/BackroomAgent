import './App.css';
import { AttributeBar } from './components/AttributeBar';
import { ChatBox } from './components/ChatBox';
import { DiceAnimation } from './components/DiceAnimation';
import { InventoryGrid } from './components/InventoryGrid';
import { useGameEngine } from './hooks/useGameEngine';

function App() {
  const {
      messages,
      gameState,
      isLoading,
      isLevelTransition,
      diceAnimation,
      handleSendMessage,
      handleUseItem,
      handleDropItem,
      handleLogicEventConfirm,
      handleDiceAnimationComplete,
      handleOptionSelect,
      handleAnimationComplete // Used for message specific animation report, if any
  } = useGameEngine();

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
      {diceAnimation && (
        <DiceAnimation 
            type={diceAnimation.type} 
            result={diceAnimation.result} 
            reason={diceAnimation.reason}
            onComplete={handleDiceAnimationComplete}
        />
      )}
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
            onOptionSelect={handleOptionSelect}
            onLogicEventConfirm={handleLogicEventConfirm}
            onMessageAnimationComplete={handleAnimationComplete}
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
