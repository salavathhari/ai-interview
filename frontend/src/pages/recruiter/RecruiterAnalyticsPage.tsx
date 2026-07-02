import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Users } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Analytics = {
  applications_per_job: { job_title: string; count: number }[];
  hiring_funnel: Record<string, number>;
  avg_scores: Record<string, number>;
  acceptance_rate: number;
  offer_rate: number;
  source_breakdown: { source: string; count: number }[];
};

export default function RecruiterAnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { recruiterApi.getAnalytics().then(r => setData(r.data)).catch(() => {}).finally(() => setLoading(false)); }, []);

  if (loading) return <div>{[1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 120, marginBottom: 12 }} />)}</div>;
  if (!data) return <div className="rp-empty"><h3>Unable to load analytics</h3></div>;

  const funnelMax = Math.max(...Object.values(data.hiring_funnel), 1);
  const funnelStages = [
    { key: 'applied', label: 'Applied', color: 'var(--rp-info)' },
    { key: 'screening', label: 'Screening', color: '#8b5cf6' },
    { key: 'interview', label: 'Interview', color: 'var(--rp-warning)' },
    { key: 'coding', label: 'Coding', color: '#ec4899' },
    { key: 'selected', label: 'Selected', color: 'var(--rp-success)' },
    { key: 'offer', label: 'Offer', color: '#06b6d4' },
    { key: 'hired', label: 'Hired', color: '#059669' },
    { key: 'rejected', label: 'Rejected', color: '#64748b' },
  ];

  const jobsMax = Math.max(...data.applications_per_job.map(j => j.count), 1);

  return (
    <div>
      {/* Summary Cards */}
      <div className="rp-metrics" style={{ marginBottom: '1.5rem' }}>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--green"><TrendingUp size={18} /></div>
          <div className="rp-metric-body"><span className="rp-metric-label">Acceptance Rate</span><span className="rp-metric-value">{data.acceptance_rate}%</span></div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--blue"><Users size={18} /></div>
          <div className="rp-metric-body"><span className="rp-metric-label">Offer Rate</span><span className="rp-metric-value">{data.offer_rate}%</span></div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--purple"><BarChart3 size={18} /></div>
          <div className="rp-metric-body"><span className="rp-metric-label">Avg ATS</span><span className="rp-metric-value">{data.avg_scores.ats || 0}</span></div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--amber"><BarChart3 size={18} /></div>
          <div className="rp-metric-body"><span className="rp-metric-label">Avg Interview</span><span className="rp-metric-value">{data.avg_scores.interview || 0}</span></div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--cyan"><BarChart3 size={18} /></div>
          <div className="rp-metric-body"><span className="rp-metric-label">Avg Coding</span><span className="rp-metric-value">{data.avg_scores.coding || 0}</span></div>
        </div>
      </div>

      <div className="rp-grid rp-grid--2">
        {/* Hiring Funnel */}
        <div className="rp-card">
          <h3 style={{ margin: '0 0 1rem' }}>Hiring Funnel</h3>
          <div className="rp-funnel">
            {funnelStages.map(s => (
              <div key={s.key} className="rp-funnel-stage">
                <span className="rp-funnel-label">{s.label}</span>
                <div className="rp-funnel-bar-wrap">
                  <div style={{ height: '100%', borderRadius: 4, background: s.color, width: `${Math.max((data.hiring_funnel[s.key] || 0) / funnelMax * 100, data.hiring_funnel[s.key] > 0 ? 8 : 0)}%`, display: 'flex', alignItems: 'center', paddingLeft: 8, fontSize: '0.8rem', fontWeight: 600, color: 'white' }}>
                    {(data.hiring_funnel[s.key] || 0) > 0 && data.hiring_funnel[s.key]}
                  </div>
                </div>
                <span className="rp-funnel-count">{data.hiring_funnel[s.key] || 0}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Applications per Job */}
        <div className="rp-card">
          <h3 style={{ margin: '0 0 1rem' }}>Applications per Job</h3>
          {data.applications_per_job.length === 0 ? (
            <p style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>No data yet</p>
          ) : (
            <div>
              {data.applications_per_job.map(j => (
                <div key={j.job_title} className="rp-chart-bar-wrap">
                  <span className="rp-chart-bar-label">{j.job_title}</span>
                  <div className="rp-chart-bar-track">
                    <div className="rp-chart-bar-fill" style={{ width: `${(j.count / jobsMax) * 100}%` }} />
                  </div>
                  <span className="rp-chart-bar-value">{j.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Source Breakdown */}
        <div className="rp-card">
          <h3 style={{ margin: '0 0 1rem' }}>Source Breakdown</h3>
          {data.source_breakdown.length === 0 ? (
            <p style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>No data yet</p>
          ) : (
            <div>
              {data.source_breakdown.map(s => (
                <div key={s.source} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--rp-border)' }}>
                  <span style={{ fontSize: '0.85rem', textTransform: 'capitalize' }}>{s.source}</span>
                  <span style={{ fontWeight: 600 }}>{s.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Score Averages */}
        <div className="rp-card">
          <h3 style={{ margin: '0 0 1rem' }}>Score Averages</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(data.avg_scores).map(([key, val]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--rp-muted)', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: 120, height: 6, background: 'var(--rp-bg)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.min(val || 0, 100)}%`, background: 'var(--rp-primary)', borderRadius: 3 }} />
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.85rem', minWidth: 32, textAlign: 'right' }}>{val || 0}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
