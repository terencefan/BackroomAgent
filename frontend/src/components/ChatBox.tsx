import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message, LogicEvent } from '../types';

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (text: string, hidden?: boolean) => void;
  isLoading?: boolean;
  onOptionSelect?: (msgId: number, option: string) => void;
  onLogicEventConfirm?: (msgId: number) => void;
  onMessageAnimationComplete?: (msgId: number) => void;
}

const LogicEventDisplay = ({ 
    event, 
    confirmed, 
    rollResult,
    onConfirm 
}: { 
    event: LogicEvent; 
    confirmed?: boolean; 
    rollResult?: number;
    onConfirm: () => void; 
}) => {
    return (
        <div className="logic-event-container">
            <div className="logic-event-header">
                <strong>事件判定: {event.name}</strong> 
                <span className="die-badge">{event.die_type}</span>
            </div>
            <ul className="logic-event-outcomes">
                {event.outcomes.map((outcome, i) => {
                    const isSelected = rollResult !== undefined && rollResult >= outcome.range[0] && rollResult <= outcome.range[1];
                    
                    const itemStyle: React.CSSProperties = isSelected ? { 
                        backgroundColor: 'rgba(74, 222, 128, 0.2)', 
                        borderColor: '#4ade80' 
                    } : {};

                    const rangeText = `[${outcome.range[0]}-${outcome.range[1]}]`;
                    const rangeStyle: React.CSSProperties = isSelected ? { color: '#4ade80' } : {};

                    return (
                        <li key={i} className="outcome-item" style={itemStyle}>
                            <span className="outcome-range" style={rangeStyle}>{rangeText}</span>
                            <span className="outcome-content">{outcome.result.content}</span>
                        </li>
                    );
                })}
            </ul>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '15px 0 5px 0', minHeight: '40px' }}>
                {!confirmed ? (
                    <button className="logic-confirm-btn" onClick={onConfirm} style={{ margin: 0 }}>
                        <span style={{ marginRight: '8px', fontSize: '1.2em' }}>🎲</span>
                        开始判定 (点击掷骰)
                    </button>
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', color: '#eab308', fontWeight: 'bold' }}>
                        {rollResult !== undefined && (
                            <>
                                <span style={{ marginRight: '8px', fontSize: '1.2em' }}>🎲</span>
                                结果: {rollResult}
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const Typewriter = ({ text, onUpdate, onComplete }: { text: string; onUpdate: () => void; onComplete?: () => void }) => {
  const [displayLength, setDisplayLength] = useState(0);

  useEffect(() => {
    if (displayLength < text.length) {
      // Dynamic speed logic: Max 2000ms total time
      const maxDuration = 2000;
      const baseSpeed = 20; // 20ms per char for short texts
      
      const totalTime = Math.min(text.length * baseSpeed, maxDuration);
      const tickRate = 20; // Update every 20ms
      const totalTicks = Math.max(1, totalTime / tickRate);
      const charsPerTick = Math.max(1, text.length / totalTicks);

      const timeout = setTimeout(() => {
        setDisplayLength((prev) => {
             const next = prev + charsPerTick;
             return next >= text.length ? text.length : next;
        });
        onUpdate();
      }, tickRate);
      return () => clearTimeout(timeout);
    } else {
       if (onComplete) onComplete();
    }
  }, [displayLength, text, onUpdate, onComplete]);

  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {text.slice(0, Math.floor(displayLength))}
      </ReactMarkdown>
    </div>
  );
};

const MessageItem = ({ msg, onSendMessage, isLoading, onScrollRequest, onOptionSelect, onLogicEventConfirm, onAnimationComplete }: { 
    msg: Message; 
    onSendMessage: (text: string, hidden?: boolean) => void;
    isLoading?: boolean;
    onScrollRequest: () => void;
    onOptionSelect?: (msgId: number, option: string) => void;
    onLogicEventConfirm?: (msgId: number) => void;
    onAnimationComplete?: (msgId: number) => void;
}) => {
    const [typingDone, setTypingDone] = useState(msg.sender === 'player');
    const animationReported = useRef(false);

    useEffect(() => {
        // Report completion for player messages immediately (or if already typingDone)
        if (typingDone && !animationReported.current && onAnimationComplete) {
            animationReported.current = true;
            onAnimationComplete(msg.id);
        }
    }, [typingDone, msg.id, onAnimationComplete]);

    const handleTypingComplete = useCallback(() => {
        setTypingDone(true);
    }, []);

    const handleOptionClick = (option: string) => {
        if (!isLoading && !msg.selectedOption && onOptionSelect) {
            onOptionSelect(msg.id, option);
            onSendMessage(option, true);
        }
    };

    return (
        <div className="message-wrapper">
             <div className={`message-bubble ${msg.sender}`}>
                {msg.sender === 'player' ? (
                    msg.text
                ) : (
                    <Typewriter 
                        text={msg.text} 
                        onUpdate={onScrollRequest} 
                        onComplete={handleTypingComplete}
                    />
                )}
             </div>

             {msg.logicEvent && typingDone && (
                 <LogicEventDisplay 
                    event={msg.logicEvent} 
                    confirmed={msg.logicEventConfirmed}
                    rollResult={msg.logicRollResult}
                    onConfirm={() => {
                        if (onLogicEventConfirm) onLogicEventConfirm(msg.id);
                    }}
                 />
             )}

             {msg.options && msg.options.length > 0 && typingDone && (
                <div className="chat-options-container">
                    {msg.options.map((option, idx) => {
                        // Logic:
                        // 1. If NO option is selected -> Show all (regular style)
                        // 2. If option IS selected -> Show ONLY the selected one (blue style)
                        
                        if (msg.selectedOption && msg.selectedOption !== option) {
                            return null;
                        }

                        const isSelected = msg.selectedOption === option;
                        const btnClass = `option-btn ${isSelected ? 'selected' : ''}`;

                        return (
                            <button 
                                key={idx} 
                                className={btnClass}
                                onClick={() => handleOptionClick(option)}
                                disabled={isLoading || !!msg.selectedOption}
                            >
                                {option}
                            </button>
                        );
                    })}
                </div>
             )}
        </div>
    );
};

export const ChatBox: React.FC<ChatBoxProps> = ({ messages, onSendMessage, isLoading, onOptionSelect, onLogicEventConfirm, onMessageAnimationComplete }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  useEffect(() => {
    if (!isLoading) {
        setTimeout(() => {
            inputRef.current?.focus();
        }, 10);
    }
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const lastMsg = messages.length > 0 ? messages[messages.length - 1] : null;
  // If we have a logic event that is NOT confirmed, we are waiting for user interaction (dice roll)
  // Even if backend is 'loading' (stream open), we don't show the loading indicator to the user
  const isWaitingForLogic = lastMsg?.logicEvent && !lastMsg.logicEventConfirmed;
  const showLoading = isLoading && !isWaitingForLogic;

  return (
    <div className="chat-box-content">
      <div className="messages-area">
        {messages.map((msg) => (
          <MessageItem 
            key={msg.id} 
            msg={msg} 
            onSendMessage={onSendMessage}
            isLoading={isLoading}
            onScrollRequest={scrollToBottom}
            onOptionSelect={onOptionSelect}
            onLogicEventConfirm={onLogicEventConfirm}
            onAnimationComplete={onMessageAnimationComplete}
          />
        ))}

        {showLoading && (
            <div className="loading-indicator">
                <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
            </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="请输入你的行动..."
          autoFocus
          disabled={isLoading}
        />
        <button type="submit" disabled={!input.trim() || isLoading}>发送</button>
      </form>
    </div>
  );
};
