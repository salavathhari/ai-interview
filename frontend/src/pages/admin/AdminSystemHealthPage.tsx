import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Activity, Server, Database, Brain, Globe, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';

const AdminSystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getSystemHealth();
      setHealth(res.data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Auto refresh every 30s
    const interval = setInterval(() => {
      fetchHealth();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  if (loading && !health) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}>Checking system health...</div>;
  }

  if (!health) {
    return <div className="admin-card"><p>Failed to load system health status.</p></div>;
  }

  const getServiceIcon = (name: string) => {
    if (name.includes('Database')) return <Database size={24} />;
    if (name.includes('AI')) return <Brain size={24} />;
    if (name.includes('API')) return <Server size={24} />;
    if (name.includes('WebSocket')) return <Globe size={24} />;
    return <Activity size={24} />;
  };

  const getStatusColor = (status: string) => {
    if (status === 'online') return 'var(--admin-success)';
    if (status === 'warning') return 'var(--admin-warning)';
    return 'var(--admin-danger)';
  };

  return (
    <div>
      <div className="admin-card admin-mb-6">
        <div className="admin-flex-between">
          <div>
            <h2 style={{ fontSize: '1.25rem', margin: '0 0 0.5rem 0' }}>Overall System Status</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ 
                width: '12px', height: '12px', borderRadius: '50%', 
                backgroundColor: getStatusColor(health.overall) 
              }} />
              <span style={{ fontWeight: 600, textTransform: 'capitalize', color: getStatusColor(health.overall) }}>
                {health.overall === 'online' ? 'All Systems Operational' : health.overall === 'warning' ? 'Degraded Performance' : 'System Outage'}
              </span>
              <span style={{ color: 'var(--admin-muted)', fontSize: '0.875rem', marginLeft: '1rem' }}>
                Last checked: {new Date(health.checked_at).toLocaleTimeString()}
              </span>
            </div>
          </div>
          <button 
            className="admin-btn outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="admin-grid-2">
        {health.services.map((service: any, idx: number) => (
          <div key={idx} className="admin-card" style={{ borderLeft: `4px solid ${getStatusColor(service.status)}` }}>
            <div className="admin-flex-between admin-mb-4">
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ color: 'var(--admin-muted)' }}>
                  {getServiceIcon(service.name)}
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.125rem' }}>{service.name}</h3>
                  <span className={`admin-badge ${service.status === 'online' ? 'success' : service.status === 'warning' ? 'warning' : 'danger'}`} style={{ marginTop: '0.25rem' }}>
                    {service.status}
                  </span>
                </div>
              </div>
              {service.latency_ms !== null && (
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--admin-text)' }}>
                    {service.latency_ms} <span style={{ fontSize: '0.875rem', color: 'var(--admin-muted)' }}>ms</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--admin-muted)' }}>Response Time</div>
                </div>
              )}
            </div>
            
            <div style={{ 
              padding: '1rem', 
              backgroundColor: 'rgba(0,0,0,0.2)', 
              borderRadius: '0.5rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              fontSize: '0.875rem',
              color: service.status === 'offline' ? 'var(--admin-danger)' : 'var(--admin-text)'
            }}>
              {service.status === 'online' ? <CheckCircle size={16} style={{ color: 'var(--admin-success)', marginTop: '2px' }} /> : <AlertTriangle size={16} style={{ marginTop: '2px' }} />}
              <span style={{ lineHeight: 1.4 }}>{service.details || 'Operating normally'}</span>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default AdminSystemHealthPage;
