import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types';

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (text: string, hidden?: boolean) => void;
  isLoading?: boolean;
  onOptionSelect?: (msgId: number, option: string) => void;
}

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

const MessageItem = ({ msg, onSendMessage, isLoading, onScrollRequest, onOptionSelect }: { 
    msg: Message; 
    onSendMessage: (text: string, hidden?: boolean) => void;
    isLoading?: boolean;
    onScrollRequest: () => void;
    onOptionSelect?: (msgId: number, option: string) => void;
}) => {
    const [typingDone, setTypingDone] = useState(msg.sender === 'player');

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

             {msg.logicEvent && (
                <div className="logic-event-container message-bubble system">
                    <div className="logic-event-header">
                        <strong>事件判定: {msg.logicEvent.name}</strong> 
                        <span className="die-badge">{msg.logicEvent.die_type}</span>
                    </div>
                    <ul className="logic-event-outcomes">
                        {msg.logicEvent.outcomes.map((outcome, i) => (
                            <li key={i} className="outcome-item">
                                <span className="outcome-range">[{outcome.range[0]}-{outcome.range[1]}]</span>
                                <span className="outcome-content">{outcome.result.content}</span>
                            </li>
                        ))}
                    </ul>
                </div>
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

export const ChatBox: React.FC<ChatBoxProps> = ({ messages, onSendMessage, isLoading, onOptionSelect }) => {
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
          />
        ))}

        {isLoading && (
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
