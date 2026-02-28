import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { sendChatMessage } from '../services/api';
import ReactMarkdown from 'react-markdown';

export default function ChatView() {
  const { repoId } = useParams();
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I can answer questions about this repository. Try asking about the tech stack, architecture, entry points, API endpoints, or specific components.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  const scrollToBottom = () => messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(repoId, msg);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]);
    }
    setLoading(false);
  };

  const suggestions = [
    'Analyze architecture (Ollama)',
    'Scan for secrets (Ollama)',
    'Check Python syntax (Ollama)',
    'Generate architecture diagram',
    'What tech stack does this project use?',
    'What are the entry points?',
    'Find unused files',
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-4xl mx-auto w-full px-4 py-4 flex-1 flex flex-col">
        <Link to={`/repo/${repoId}`} className="text-sm text-primary-600 hover:underline mb-3 inline-block">← Back</Link>
        <h1 className="text-xl font-bold text-gray-900 mb-4">AI Repository Assistant</h1>

        {/* Chat messages */}
        <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-y-auto p-4 mb-4" style={{ maxHeight: '60vh' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-3 rounded-xl text-sm ${msg.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-800'
                }`}>
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 px-4 py-3 rounded-xl text-sm text-gray-400">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        {/* Suggestions */}
        {messages.length <= 2 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => { setInput(s); }}
                className="text-xs px-3 py-1.5 bg-white border border-gray-200 rounded-full text-gray-600 hover:bg-gray-50">
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about the codebase..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-primary-500" />
          <button onClick={handleSend} disabled={loading || !input.trim()}
            className="bg-primary-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-primary-700 disabled:opacity-50">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}