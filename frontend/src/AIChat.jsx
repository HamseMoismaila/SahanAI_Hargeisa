import { useState, useRef, useEffect } from 'react';

export default function AIChat() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hello! I am the Goobta AI Assistant. I can help you analyze Hargeisa real estate trends, explain our machine learning predictions, or find the best places to invest. How can I help?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });
      const data = await response.json();
      
      setMessages(prev => [...prev, { role: 'ai', text: data.reply }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'ai', text: "Error connecting to AI API." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="sidebar right-sidebar">
      <h3>🤖 Goobta AI Assistant</h3>
      <p className="subtitle">Ask about land values, risks, and ROI.</p>
      
      <div className="chat-container">
        <div className="chat-history">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <div className="chat-bubble">
                {msg.text}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="chat-message ai">
              <div className="chat-bubble typing">AI is typing...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="chat-input-area">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about real estate..."
          />
          <button onClick={handleSend}>Send</button>
        </div>
      </div>
    </div>
  );
}
