import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Search, ShieldAlert, KeyRound, UserMinus, UserCheck, Settings, FileText, Activity } from 'lucide-react';

const AdminAuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchAction, setSearchAction] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getAuditLogs({ action: searchAction });
      setLogs(res.data.logs);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [searchAction]);

  const getActionIcon = (action: string) => {
    if (action.includes('password')) return <KeyRound size={16} color="var(--admin-warning)" />;
    if (action.includes('disabled') || action.includes('rejected')) return <UserMinus size={16} color="var(--admin-danger)" />;
    if (action.includes('enabled') || action.includes('approved')) return <UserCheck size={16} color="var(--admin-success)" />;
    if (action.includes('settings')) return <Settings size={16} color="var(--admin-primary)" />;
    if (action.includes('report')) return <FileText size={16} color="var(--admin-muted)" />;
    return <Activity size={16} />;
  };

  return (
    <div className="admin-card">
      <div className="admin-flex-between admin-mb-6">
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={20} color="var(--admin-primary)" />
          Security Audit Trail
        </h2>
        
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--admin-muted)' }} />
          <input 
            type="text" 
            placeholder="Filter by action type..." 
            className="admin-input"
            style={{ paddingLeft: '32px' }}
            value={searchAction}
            onChange={(e) => setSearchAction(e.target.value)}
          />
        </div>
      </div>

      <div className="admin-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading audit logs...</div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Admin Email</th>
                <th>Action</th>
                <th>Target</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length > 0 ? logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={{ fontWeight: 500 }}>{log.admin_email || 'System'}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {getActionIcon(log.action)}
                      <span style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{log.action}</span>
                    </div>
                  </td>
                  <td>
                    {log.target_type ? (
                      <span className="admin-badge neutral">
                        {log.target_type}: {log.target_id}
                      </span>
                    ) : '-'}
                  </td>
                  <td>
                    <div style={{ 
                      fontSize: '0.75rem', 
                      fontFamily: 'monospace',
                      backgroundColor: 'rgba(0,0,0,0.2)',
                      padding: '0.5rem',
                      borderRadius: '4px',
                      maxWidth: '300px',
                      overflowX: 'auto'
                    }}>
                      {log.details ? JSON.stringify(log.details) : 'N/A'}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center' }}>No audit logs found.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AdminAuditLogsPage;
