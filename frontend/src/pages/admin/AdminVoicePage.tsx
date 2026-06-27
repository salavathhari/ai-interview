import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';

const AdminVoicePage: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchVoiceSessions = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getVoiceSessions({ status: statusFilter || undefined, limit: 50 });
      setSessions(res.data);
    } catch (error) {
      console.error('Failed to fetch voice sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVoiceSessions();
  }, [statusFilter]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Voice Sessions...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Voice Interview Sessions</h2>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: '0.5rem 1rem',
            background: 'var(--admin-card-bg)',
            color: 'var(--admin-text)',
            border: '1px solid var(--admin-border)',
            borderRadius: '6px',
            fontSize: '0.875rem',
          }}
        >
          <option value="">All Statuses</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="abandoned">Abandoned</option>
        </select>
      </div>

      {sessions.length === 0 ? (
        <div className="admin-card">
          <p style={{ color: 'var(--admin-muted)', textAlign: 'center', padding: '2rem' }}>No voice sessions found.</p>
        </div>
      ) : (
        <div className="admin-card" style={{ overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--admin-border)' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Session ID</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Candidate</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Role</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Status</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Started</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} style={{ borderBottom: '1px solid var(--admin-border)' }}>
                  <td style={{ padding: '0.75rem' }}>{session.id}</td>
                  <td style={{ padding: '0.75rem' }}>{session.user_email || 'N/A'}</td>
                  <td style={{ padding: '0.75rem' }}>{session.role || 'N/A'}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      background: session.status === 'completed' ? 'rgba(34,197,94,0.1)' :
                                  session.status === 'in_progress' ? 'rgba(59,130,246,0.1)' :
                                  'rgba(239,68,68,0.1)',
                      color: session.status === 'completed' ? '#22c55e' :
                             session.status === 'in_progress' ? '#3b82f6' :
                             '#ef4444',
                    }}>
                      {session.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>{new Date(session.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminVoicePage;
