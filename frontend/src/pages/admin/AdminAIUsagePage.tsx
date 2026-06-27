import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Cpu, DollarSign, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

const AdminAIUsagePage: React.FC = () => {
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchUsage = async () => {
      setLoading(true);
      try {
        const res = await adminApi.getAIUsageDetail({ days });
        setUsage(res.data);
      } catch (error) {
        console.error('Failed to fetch AI usage:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchUsage();
  }, [days]);

  if (loading && !usage) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Loading AI Usage data...</div>;
  }

  if (!usage) {
    return <div className="admin-card"><p>Failed to load AI usage statistics.</p></div>;
  }

  const kpis = [
    { title: 'Total AI Requests', value: usage.total_requests, icon: <Activity size={24} />, type: 'primary' },
    { title: 'Token Consumption', value: (usage.total_tokens / 1000).toFixed(1) + 'k', icon: <Cpu size={24} />, type: 'warning' },
    { title: 'Estimated Cost', value: `$${usage.total_cost.toFixed(2)}`, icon: <DollarSign size={24} />, type: 'success' },
  ];

  return (
    <div>
      <div className="admin-flex-between admin-mb-6">
        <h2 style={{ fontSize: '1.25rem', margin: 0 }}>AI Token & Cost Analytics</h2>
        <select 
          className="admin-input" 
          style={{ width: '150px' }}
          value={days} 
          onChange={(e) => setDays(Number(e.target.value))}
        >
          <option value={7}>Last 7 Days</option>
          <option value={30}>Last 30 Days</option>
          <option value={90}>Last 90 Days</option>
        </select>
      </div>

      <div className="admin-stat-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        {kpis.map((kpi, idx) => (
          <div key={idx} className="admin-card admin-stat-card">
            <div className="admin-stat-info">
              <h3>{kpi.title}</h3>
              <p className="admin-stat-value">{kpi.value}</p>
            </div>
            <div className={`admin-stat-icon ${kpi.type}`}>
              {kpi.icon}
            </div>
          </div>
        ))}
      </div>

      <div className="admin-grid-2">
        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Daily Token Usage</h2>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usage.daily_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} minTickGap={20} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(val) => `${(val/1000).toFixed(0)}k`} />
                <Tooltip 
                  formatter={(value: any) => [`${value} tokens`, 'Tokens']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Bar dataKey="tokens" fill="var(--admin-primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="admin-card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Daily API Cost ($)</h2>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={usage.daily_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} tickMargin={10} minTickGap={20} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(val) => `$${val}`} />
                <Tooltip 
                  formatter={(value: any) => [`$${Number(value).toFixed(4)}`, 'Cost']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Line type="monotone" dataKey="cost" stroke="var(--admin-success)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: '1.5rem' }}>
        <h2 style={{ fontSize: '1.125rem', marginBottom: '1.5rem', fontWeight: 600 }}>Usage by Feature</h2>
        <div className="admin-table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Requests</th>
                <th>Tokens Consumed</th>
                <th>Estimated Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(usage.usage_by_feature).map(([feature, data]: [string, any]) => (
                <tr key={feature}>
                  <td style={{ textTransform: 'capitalize' }}>{feature.replace(/-/g, ' ')}</td>
                  <td>{data.requests}</td>
                  <td>{data.tokens.toLocaleString()}</td>
                  <td>${data.cost.toFixed(4)}</td>
                </tr>
              ))}
              {Object.keys(usage.usage_by_feature).length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center' }}>No feature usage data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminAIUsagePage;
