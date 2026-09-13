import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { askQuestion, getChatHistory } from '../services/chatService';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await getChatHistory();
        setMessages(history);
      } catch {
        setError('Unable to load chat history.');
      } finally {
        setIsLoading(false);
      }
    };
    loadHistory();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || isAsking) return;

    setError('');
    setInput('');

    // Show the user's question immediately, before the answer arrives
    const optimisticUserMessage = { id: `temp-${Date.now()}`, role: 'user', content: question };
    setMessages((prev) => [...prev, optimisticUserMessage]);
    setIsAsking(true);

    try {
      const { answer } = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        { id: `temp-${Date.now()}-a`, role: 'assistant', content: answer },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Unable to get an answer. Please try again.');
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <div className="max-w-2xl mx-auto w-full px-6 py-10 flex flex-col flex-1">
        <header className="flex justify-between items-center pb-6 border-b border-line">
          <Link to="/dashboard" className="font-serif text-xl text-ink">
            HealthCura
          </Link>
          <Link to="/dashboard" className="text-sm text-ink-muted hover:text-ink">
            Dashboard
          </Link>
        </header>

        <h1 className="font-serif text-2xl text-ink mt-8 mb-2">Ask HealthCura</h1>
        <p className="text-sm text-ink-muted mb-6">
          Ask questions about your uploaded medical documents.
        </p>

        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {isLoading && <p className="text-ink-muted">Loading...</p>}

          {!isLoading && messages.length === 0 && (
            <p className="text-ink-muted">
              No messages yet. Ask a question about your health records below.
            </p>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[85%] rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-teal text-white ml-auto'
                  : 'bg-surface border border-line text-ink'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          ))}

          {isAsking && (
            <div className="bg-surface border border-line text-ink-muted rounded-lg px-4 py-3 max-w-[85%]">
              <p className="text-sm">Thinking...</p>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {error && <p className="text-sm text-red-700 mb-2">{error}</p>}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your lab results, medications..."
            disabled={isAsking}
            className="flex-1 px-3 py-2 border border-line rounded focus:outline-none focus:ring-2 focus:ring-teal disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isAsking || !input.trim()}
            className="bg-teal text-white px-4 py-2 rounded font-medium hover:bg-teal-deep disabled:opacity-50"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatPage;