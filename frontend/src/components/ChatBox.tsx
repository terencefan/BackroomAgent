import React, { useCallback, useEffect, useRef, useState } from 'react';

interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system';
  text: string;
  options?: string[];
}

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
}

const Typewriter = ({ text, onUpdate, onComplete }: { text: string; onUpdate: () => void; onComplete?: () => void }) => {
  const [displayLength, setDisplayLength] = useState(0);

  useEffect(() => {
    if (displayLength < text.length) {
      const timeout = setTimeout(() => {
        setDisplayLength((prev) => prev + 1);
        onUpdate();
      }, 20);
      return () => clearTimeout(timeout);
    } else {
       if (onComplete) onComplete();
    }
  }, [displayLength, text, onUpdate, onComplete]);

  return <>{text.slice(0, displayLength)}</>;
};

const MessageItem = ({ msg, onSendMessage, isLoading, onScrollRequest }: { 
    msg: Message; 
    onSendMessage: (text: string) => void;
    isLoading?: boolean;
    onScrollRequest: () => void;
}) => {
    const [typingDone, setTypingDone] = useState(msg.sender === 'player');
    const [selectedOptionIdx, setSelectedOptionIdx] = useState<number | null>(null);

    const handleTypingComplete = useCallback(() => {
        setTypingDone(true);
    }, []);

    const handleOptionClick = (option: string, idx: number) => {
        if (!isLoading) {
            setSelectedOptionIdx(idx);
            onSendMessage(option);
        }
    };

    // Scroll when options appear
    useEffect(() => {
        if (typingDone && msg.options && msg.options.length > 0) {
            // Check if options are actually being rendered (not hidden by selection)
            if (selectedOptionIdx === null) {
                onScrollRequest();
            }
        }
    }, [typingDone, msg.options, onScrollRequest, selectedOptionIdx]);

    return (
        <div className={`message-container ${msg.sender}`}>
             <div className={`message ${msg.sender}`}>
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
             {msg.options && msg.options.length > 0 && typingDone && (
                <div className="message-options">
                    {msg.options.map((option, idx) => {
                        // If an option is selected, only show that one. Hide others.
                        if (selectedOptionIdx !== null && selectedOptionIdx !== idx) {
                            return null;
                        }

                        let btnClass = "option-btn";
                        if (selectedOptionIdx === idx) {
                            btnClass += " selected";
                        }
                        
                        return (
                            <button 
                                key={idx} 
                                className={btnClass}
                                onClick={() => handleOptionClick(option, idx)}
                                disabled={isLoading || selectedOptionIdx !== null}
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

export const ChatBox: React.FC<ChatBoxProps> = ({ messages, onSendMessage, isLoading }) => {
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
