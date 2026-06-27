import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Bell, Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';

const AdminNotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getNotifications();
      setNotifications(res.data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markRead = async (id: number) => {
    try {
      await adminApi.markNotificationRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllRead = async () => {
    try {
      await adminApi.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'info': return <Info size={16} />;
      case 'warning': return <AlertTriangle size={16} />;
      case 'error': return <XCircle size={16} />;
      case 'success': return <CheckCircle size={16} />;
      default: return <Bell size={16} />;
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Notifications...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Notifications</h2>
        <button onClick={markAllRead} style={{
          padding: '0.5rem 1rem',
          background: 'var(--admin-primary)',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '0.875rem'
        }}>
          Mark All as Read
        </button>
      </div>

      {notifications.length === 0 ? (
        <div className="admin-card">
          <p style={{ color: 'var(--admin-muted)', textAlign: 'center', padding: '2rem' }}>No notifications yet.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className="admin-card"
              style={{
                opacity: notif.is_read ? 0.6 : 1,
                borderLeft: `4px solid ${notif.is_read ? 'var(--admin-muted)' : 'var(--admin-primary)'}`,
                cursor: 'pointer',
              }}
              onClick={() => !notif.is_read && markRead(notif.id)}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                <div style={{ color: notif.is_read ? 'var(--admin-muted)' : 'var(--admin-primary)', marginTop: '2px' }}>
                  {getIcon(notif.type)}
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.25rem' }}>{notif.title}</h4>
                  <p style={{ fontSize: '0.875rem', color: 'var(--admin-muted)', margin: 0 }}>{notif.message}</p>
                  <span style={{ fontSize: '0.75rem', color: 'var(--admin-muted)', marginTop: '0.5rem', display: 'block' }}>
                    {new Date(notif.created_at).toLocaleString()}
                  </span>
                </div>
                {!notif.is_read && (
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: 'var(--admin-primary)',
                    flexShrink: 0,
                  }} />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminNotificationsPage;
