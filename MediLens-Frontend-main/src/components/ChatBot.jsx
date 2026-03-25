import { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';
import "../css/ChatBot.css";

function ChatBot({ medicineName }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // We do NOT want to fetch the summary here anymore.
    // The chatbot should just be a Q&A interface.
    if (medicineName) {
      setMessages([
        { role: "assistant", content: `I'm here to help with questions about ${medicineName}.` }
      ]);
    } else {
      setMessages([
        { role: "assistant", content: "I'm here to help. Ask me anything about medicines or health." }
      ]);
    }
  }, [medicineName]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          medicine_name: medicineName,
          history: newMessages
        }),
      });

      const data = await res.json();
      const botMsg = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error connecting to assistant." }]);
    }
    setLoading(false);
  };

  return (
    <div className="tool-card chatbot-card">
      <div className="tool-header">Medical Assistant</div>

      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message ${m.role === 'assistant' ? 'bot' : 'user'}`}>
            {m.role === 'assistant' ? (
              <ReactMarkdown>{m.content}</ReactMarkdown>
            ) : (
              m.content
            )}
          </div>
        ))}
        {loading && <div className="chat-message bot">Thinking...</div>}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={medicineName ? "Ask a question about this medicine..." : "Tell me about your symptoms..."}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button onClick={sendMessage} disabled={loading}>Send</button>
      </div>
    </div>
  );
}

export default ChatBot;