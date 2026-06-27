import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Users, Video, Mic, Cpu, Briefcase, FileText, CheckCircle, BarChart } from 'lucide-react';

const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await adminApi.getDashboard();
        setStats(res.data);
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Dashboard...</div>;
  }

  if (!stats) {
    return <div className="admin-card"><p>Failed to load dashboard statistics.</p></div>;
  }

  const kpis = [
    { title: 'Total Users', value: stats.total_users, subtitle: `${stats.active_users} active`, icon: <Users size={24} />, type: 'primary' },
    { title: 'Interviews', value: stats.total_interviews, subtitle: `${stats.interviews_today} today`, icon: <Video size={24} />, type: 'primary' },
    { title: 'Recruiters', value: stats.total_recruiters, subtitle: 'Total approved', icon: <Briefcase size={24} />, type: 'primary' },
    { title: 'Avg Score', value: `${stats.avg_score_platform.toFixed(1)}%`, subtitle: 'Platform-wide', icon: <BarChart size={24} />, type: 'success' },
    { title: 'Reports', value: stats.total_reports, subtitle: 'Generated', icon: <FileText size={24} />, type: 'primary' },
    { title: 'Active Voice', value: stats.active_voice_sessions, subtitle: 'Live sessions', icon: <Mic size={24} />, type: stats.active_voice_sessions > 0 ? 'warning' : 'primary' },
    { title: 'API Requests', value: stats.api_requests_today, subtitle: 'Today', icon: <Cpu size={24} />, type: 'primary' },
    { title: 'API Cost', value: `$${stats.total_api_cost.toFixed(2)}`, subtitle: 'Total estimated', icon: <CheckCircle size={24} />, type: 'primary' },
  ];

  return (
    <div>
      <div className="admin-stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {kpis.map((kpi, idx) => (
          <div key={idx} className="admin-card admin-stat-card">
            <div className="admin-stat-info">
              <h3>{kpi.title}</h3>
              <p className="admin-stat-value">{kpi.value}</p>
              <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--admin-muted)' }}>{kpi.subtitle}</p>
            </div>
            <div className={`admin-stat-icon ${kpi.type}`}>
              {kpi.icon}
            </div>
          </div>
        ))}
      </div>

      <div className="admin-grid-2">
        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Recent Interview Sessions</h2>
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Role</th>
                  <th>Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_activity.length > 0 ? (
                  stats.recent_activity.map((session: any) => (
                    <tr key={session.id}>
                      <td>
                        <div style={{ fontWeight: 500 }}>{session.user}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>{session.email}</div>
                      </td>
                      <td>{session.role}</td>
                      <td>{session.score !== null ? session.score.toFixed(1) : '-'}</td>
                      <td>
                        <span className={`admin-badge ${session.status === 'completed' ? 'success' : session.status === 'pending' ? 'warning' : 'neutral'}`}>
                          {session.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center' }}>No recent sessions found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Role Distribution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {Object.entries(stats.interviews_by_role).map(([role, count]: [string, any]) => {
              const max = Math.max(...Object.values(stats.interviews_by_role) as number[]);
              const percent = (count / max) * 100;
              return (
                <div key={role}>
                  <div className="admin-flex-between" style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                    <span>{role}</span>
                    <span style={{ fontWeight: 600 }}>{count}</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${percent}%`, height: '100%', backgroundColor: 'var(--admin-primary)', borderRadius: '4px' }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
