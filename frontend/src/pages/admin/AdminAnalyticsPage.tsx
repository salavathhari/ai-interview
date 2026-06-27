import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Users, Video, Target, Briefcase } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

const AdminAnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await adminApi.getPlatformAnalytics();
        setAnalytics(res.data);
      } catch (error) {
        console.error('Failed to fetch platform analytics:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading Analytics...</div>;
  }

  if (!analytics) {
    return <div className="admin-card"><p>Failed to load platform analytics.</p></div>;
  }

  const kpis = [
    { title: 'New Signups', value: analytics.new_signups_this_month, subtitle: 'This month', icon: <Users size={24} />, type: 'primary' },
    { title: 'Completion Rate', value: `${analytics.interview_completion_rate}%`, subtitle: 'Interviews completed', icon: <Target size={24} />, type: 'success' },
    { title: 'Top Role', value: analytics.most_popular_role, subtitle: 'Most interviewed', icon: <Briefcase size={24} />, type: 'warning' },
    { title: 'Top Interview Type', value: analytics.most_popular_interview_type, subtitle: 'Most popular format', icon: <Video size={24} />, type: 'primary' },
  ];

  return (
    <div>
      <div className="admin-stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {kpis.map((kpi, idx) => (
          <div key={idx} className="admin-card admin-stat-card">
            <div className="admin-stat-info">
              <h3>{kpi.title}</h3>
              <p className="admin-stat-value" style={{ fontSize: '1.5rem' }}>{kpi.value}</p>
              <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--admin-muted)' }}>{kpi.subtitle}</p>
            </div>
            <div className={`admin-stat-icon ${kpi.type}`}>
              {kpi.icon}
            </div>
          </div>
        ))}
      </div>

      <div className="admin-grid-2 admin-mb-6">
        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>User Growth (12 Months)</h2>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.user_growth} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--admin-primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--admin-primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} minTickGap={20} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value: any) => [value, 'New Users']}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Area type="monotone" dataKey="count" stroke="var(--admin-primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorUsers)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Interview Volume (12 Months)</h2>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.interview_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorInterviews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--admin-success)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--admin-success)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} minTickGap={20} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value: any) => [value, 'Interviews']}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Area type="monotone" dataKey="count" stroke="var(--admin-success)" strokeWidth={3} fillOpacity={1} fill="url(#colorInterviews)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="admin-card">
        <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Score Distribution</h2>
        <div className="admin-chart-container" style={{ height: '250px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analytics.score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="range" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                formatter={(value: any) => [value, 'Candidates']}
                labelFormatter={(label) => `Score Range: ${label}`}
                cursor={{fill: 'rgba(255, 255, 255, 0.05)'}}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {
                  analytics.score_distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={
                      entry.range === '8–10' ? 'var(--admin-success)' :
                      entry.range === '6–8' ? 'var(--admin-primary)' :
                      entry.range === '4–6' ? 'var(--admin-warning)' :
                      'var(--admin-danger)'
                    } />
                  ))
                }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalyticsPage;
