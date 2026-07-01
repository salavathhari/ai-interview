import { useEffect, useState } from 'react';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Notif = { id: number; title: string; message: string; type: string; is_read: boolean; created_at: string; };

export default function RecruiterNotificationsPage() {
  const [notifs, setNotifs] = useState<Notif[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const fetchN = () => { setLoading(true); recruiterApi.getNotifications(unreadOnly).then(r => setNotifs(r.data)).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { fetchN(); }, [unreadOnly]);

  const markRead = async (id: number) => { await recruiterApi.markNotificationRead(id); fetchN(); };

  const typeColor = (t: string) => {
    switch (t) { case 'success': return 'var(--rp-success)'; case 'warning': return 'var(--rp-warning)'; case 'error': return 'var(--rp-danger)'; default: return 'var(--rp-info)'; }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className={`rp-btn rp-btn--${!unreadOnly ? 'primary' : 'secondary'} rp-btn--sm`} onClick={() => setUnreadOnly(false)}>All</button>
          <button className={`rp-btn rp-btn--${unreadOnly ? 'primary' : 'secondary'} rp-btn--sm`} onClick={() => setUnreadOnly(true)}>Unread</button>
        </div>
        <span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>{notifs.length} notification{notifs.length !== 1 ? 's' : ''}</span>
      </div>

      {loading ? [1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 60, marginBottom: 8 }} />) : notifs.length === 0 ? (
        <div className="rp-card rp-empty"><div className="rp-empty-icon"><Bell size={24} /></div><h3>No notifications</h3><p>You're all caught up!</p></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {notifs.map(n => (
            <div key={n.id} className="rp-card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem', opacity: n.is_read ? 0.7 : 1, borderLeft: `3px solid ${typeColor(n.type)}` }}>
              <div style={{ marginTop: 2 }}>
                <Bell size={16} style={{ color: typeColor(n.type) }} />
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: '0.9rem' }}>{n.title}</strong>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{n.message}</p>
                <span style={{ fontSize: '0.75rem', color: 'var(--rp-muted)' }}>{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</span>
              </div>
              {!n.is_read && (
                <button className="rp-btn rp-btn--ghost rp-btn--sm" onClick={() => markRead(n.id)} title="Mark as read">
                  <Check size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
