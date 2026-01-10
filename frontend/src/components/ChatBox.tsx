import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import type { Message, LogicEvent, SettlementDelta } from '../types';

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (text: string, hidden?: boolean) => void;
  isLoading?: boolean;
  onOptionSelect?: (msgId: number, option: string) => void;
  onLogicEventConfirm?: (msgId: number) => void;
  onMessageAnimationComplete?: (msgId: number) => void;
}

const SettlementDisplay = ({ delta }: { delta: SettlementDelta }) => {
    // Styling constants
    const COLOR_HP = '#e53e3e';
    const COLOR_SANITY = '#805ad5';
    const COLOR_ITEM = '#ffee00';
    const COLOR_TEXT = '#a0aec0';

    const formatVal = (val: number, color: string) => (
        <span style={{ color, fontWeight: 'bold', marginLeft: '4px' }}>
            {val > 0 ? '+' : ''}{val}
        </span>
    );

    return (
        <div className="settlement-container" style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '0.95em',
            margin: '10px 0',
            // Use lighter background to separate from dark chat
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            padding: '10px',
            borderRadius: '4px',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
            {/* Row 1: Vitals */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
                {delta.hp_change !== 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', color: COLOR_HP }}>
                        <span style={{ fontWeight: 'bold' }}>生命值</span>
                        {formatVal(delta.hp_change, COLOR_HP)}
                    </div>
                )}
                {delta.sanity_change !== 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', color: COLOR_SANITY }}>
                        <span style={{ fontWeight: 'bold' }}>理智值</span>
                        {formatVal(delta.sanity_change, COLOR_SANITY)}
                    </div>
                )}
            </div>

            {/* Row 2: Level Transition */}
            {delta.level_transition && (
                <div style={{ textAlign: 'center', color: COLOR_TEXT }}>
                    进入新层级: <span style={{ color: COLOR_ITEM }}>{delta.level_transition}</span>
                </div>
            )}

            {/* Row 3: Items */}
            {(delta.items_added.length > 0 || delta.items_removed.length > 0) && (
                <div style={{ 
                    display: 'flex', 
                    flexWrap: 'wrap', 
                    justifyContent: 'center', 
                    gap: '12px',
                    marginTop: '4px'
                }}>
                    {delta.items_added.map((item, idx) => (
                        <span key={`add-${idx}`} style={{ color: COLOR_TEXT }}>
                            + <span style={{ color: COLOR_ITEM }}>{item}</span>
                        </span>
                    ))}
                    {delta.items_removed.map((item, idx) => (
                        <span key={`remove-${idx}`} style={{ color: COLOR_TEXT }}>
                            - <span style={{ color: COLOR_ITEM }}>{item}</span>
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
};

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
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
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
    // If it's a generic system message (not the player), we assume it might contain status updates.
    // However, if the message is from "system" specifically (mechanistic logs),
    // we might want to skip typewriter simply because it's usually short and we want to see the formatting instantly.
    // For now, let's keep it simple: player messages instant, others typed.
    // But if it's 'system' sender, let's display instantly to avoid HTML tag typing glitch.
    
    // Check if we should typewrite:
    // Player: No
    // System (Visual Logs): No (Instant)
    // DM (Narrative): Yes

    const shouldTypewrite = msg.sender === 'dm';

    const [typingDone, setTypingDone] = useState(!shouldTypewrite);
    const animationReported = useRef(false);

    useEffect(() => {
        // Report completion immediately if no typing needed
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
             {/* Render Text Content if exists */}
             {msg.text && (
                 <div className={`message-bubble ${msg.sender}`}>
                    {shouldTypewrite ? (
                        <Typewriter 
                            text={msg.text} 
                            onUpdate={onScrollRequest} 
                            onComplete={handleTypingComplete}
                        />
                    ) : (
                        <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                {msg.text}
                            </ReactMarkdown>
                        </div>
                    )}
                 </div>
             )}
             
             {/* Helper to just "complete typing" if no text */}
             {!msg.text && !typingDone && (
                  // If msg has no text (e.g. pure logic event or settlement), mark as done immediately
                  // Using effect or simple immediate state update logic
                  // For now, rely on useEffect above for typingDone... wait, if text is empty, Typewriter might be confused.
                  // Actually if text is empty, we skip the bubble above, so we should setTypingDone true.
                  // Effect logic needs review or just force it here
                  <div style={{ display: 'none' }} />
             )}

             {/* Logic Event Display */}
             {msg.logicEvent && (typingDone || !msg.text) && (
                 <LogicEventDisplay 
                    event={msg.logicEvent} 
                    confirmed={msg.logicEventConfirmed}
                    rollResult={msg.logicRollResult}
                    onConfirm={() => {
                        if (onLogicEventConfirm) onLogicEventConfirm(msg.id);
                    }}
                 />
             )}
            
             {/* Settlement Display */}
             {msg.settlement && (
                <SettlementDisplay delta={msg.settlement} />
             )}

             {/* Options Display */}
             {msg.options && msg.options.length > 0 && (typingDone || !msg.text) && (
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
