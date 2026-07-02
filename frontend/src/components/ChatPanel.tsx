import { useEffect, useState, useRef } from 'react';
import { Send, MessageCircle } from 'lucide-react';
import { chatApi } from '../services/api';
import './ChatPanel.css';

type Message = {
  id: number;
  application_id: number;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  content: string;
  is_read: boolean;
  created_at: string;
};

function fmtTime(d: string) {
  const date = new Date(d);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  if (isToday) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

export default function ChatPanel({ applicationId, currentUserId }: { applicationId: number; currentUserId: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMsg, setNewMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchMessages = () => {
    chatApi.getMessages(applicationId)
      .then(r => setMessages(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, [applicationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!newMsg.trim() || sending) return;
    setSending(true);
    try {
      const res = await chatApi.sendMessage(applicationId, newMsg.trim());
      setMessages(prev => [...prev, res.data]);
      setNewMsg('');
    } catch {
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="cp-panel">
        <div className="cp-header">
          <MessageCircle size={16} />
          <span>Messages</span>
        </div>
        <div className="cp-body cp-loading">
          <div className="cp-skel-msg" style={{ width: '60%' }} />
          <div className="cp-skel-msg cp-skel-msg--right" style={{ width: '40%' }} />
          <div className="cp-skel-msg" style={{ width: '50%' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="cp-panel">
      <div className="cp-header">
        <MessageCircle size={16} />
        <span>Messages</span>
        <span className="cp-count">{messages.length}</span>
      </div>

      <div className="cp-body">
        {messages.length === 0 ? (
          <div className="cp-empty">
            <p>No messages yet. Start a conversation with the recruiter.</p>
          </div>
        ) : (
          messages.map(msg => {
            const isMine = msg.sender_id === currentUserId;
            return (
              <div key={msg.id} className={`cp-msg ${isMine ? 'cp-msg--mine' : 'cp-msg--theirs'}`}>
                {!isMine && <span className="cp-msg-sender">{msg.sender_name}</span>}
                <div className="cp-msg-bubble">
                  <p className="cp-msg-text">{msg.content}</p>
                </div>
                <span className="cp-msg-time">{fmtTime(msg.created_at)}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className="cp-input-area">
        <textarea
          className="cp-input"
          placeholder="Type a message..."
          value={newMsg}
          onChange={e => setNewMsg(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <button
          className="cp-send-btn"
          disabled={!newMsg.trim() || sending}
          onClick={handleSend}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
