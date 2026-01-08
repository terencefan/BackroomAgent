import React, { useEffect, useRef, useState } from 'react';

interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system';
  text: string;
}

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ messages, onSendMessage }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-section">
      <div className="messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form className="input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your action..."
          autoFocus
        />
        <button type="submit">SEND</button>
      </form>
    </div>
  );
};
