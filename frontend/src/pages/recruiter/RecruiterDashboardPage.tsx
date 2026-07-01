import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Users, BarChart3, Sparkles, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Dashboard = {
  total_jobs: number; open_jobs: number; closed_jobs: number; draft_jobs: number;
  total_applications: number; applications_in_screening: number;
  applications_in_interview: number; applications_in_coding: number;
  shortlisted: number; rejected: number; offers_released: number; hired: number;
  avg_candidate_score: number | null; avg_ats_score: number | null;
  avg_career_readiness: number | null;
  pipeline: { stage: string; count: number }[];
  recent_activities: any[];
  top_candidates: any[];
};

const fmt = (s: number | null) => s === null || s === undefined ? 'N/A' : s.toFixed(1);
const scoreCls = (s: number | null) => s === null ? '' : s >= 8 ? 'rp-score--high' : s >= 6 ? 'rp-score--mid' : 'rp-score--low';

export default function RecruiterDashboardPage() {
  const nav = useNavigate();
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    recruiterApi.getDashboard().then(r => setDash(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: '2rem' }}>{[1,2,3,4].map(i => <div key={i} className="rp-skeleton" style={{ height: 80, marginBottom: 12 }} />)}</div>;
  if (!dash) return <div className="rp-empty"><h3>Unable to load dashboard</h3></div>;

  const maxPipeline = Math.max(...dash.pipeline.map(p => p.count), 1);

  return (
    <div>
      {/* KPIs */}
      <div className="rp-metrics">
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--blue"><Briefcase size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Open Positions</span>
            <span className="rp-metric-value">{dash.open_jobs}</span>
          </div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--purple"><Users size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Total Applications</span>
            <span className="rp-metric-value">{dash.total_applications}</span>
          </div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--green"><CheckCircle size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Hired</span>
            <span className="rp-metric-value">{dash.hired}</span>
          </div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--amber"><Sparkles size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Avg Score</span>
            <span className="rp-metric-value">{fmt(dash.avg_candidate_score)}</span>
          </div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--cyan"><TrendingUp size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Avg ATS</span>
            <span className="rp-metric-value">{fmt(dash.avg_ats_score)}</span>
          </div>
        </div>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--red"><Clock size={20} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Offers Pending</span>
            <span className="rp-metric-value">{dash.offers_released}</span>
          </div>
        </div>
      </div>

      <div className="rp-grid rp-grid--sidebar">
        <div>
          {/* Pipeline Funnel */}
          <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
            <div className="rp-card-header">
              <h2 className="rp-card-title">Hiring Pipeline</h2>
            </div>
            <div className="rp-funnel">
              {dash.pipeline.filter(s => s.stage !== 'Rejected').map(s => (
                <div key={s.stage} className="rp-funnel-stage">
                  <span className="rp-funnel-label">{s.stage}</span>
                  <div className="rp-funnel-bar-wrap">
                    <div className={`rp-funnel-bar rp-funnel-bar--${s.stage.toLowerCase()}`}
                         style={{ width: `${Math.max((s.count / maxPipeline) * 100, s.count > 0 ? 8 : 0)}%` }}>
                      {s.count > 0 && s.count}
                    </div>
                  </div>
                  <span className="rp-funnel-count">{s.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Candidates */}
          <div className="rp-card">
            <div className="rp-card-header">
              <h2 className="rp-card-title">Recent Candidates</h2>
              <button className="rp-btn rp-btn--ghost rp-btn--sm" onClick={() => nav('/recruiter/applications')}>View All</button>
            </div>
            {dash.top_candidates.length === 0 ? (
              <div className="rp-empty"><p>No candidates yet</p></div>
            ) : (
              <div className="rp-table-wrap">
                <table className="rp-table">
                  <thead><tr><th>Candidate</th><th>Status</th><th>Score</th><th>Applied</th></tr></thead>
                  <tbody>
                    {dash.top_candidates.map((c: any, i: number) => (
                      <tr key={i} style={{ cursor: 'pointer' }} onClick={() => nav(`/recruiter/candidates/${c.user_id}`)}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div className="rp-avatar">{(c.user_name?.[0] || 'U').toUpperCase()}</div>
                            <div><strong>{c.user_name}</strong><br /><small style={{ color: 'var(--rp-muted)' }}>{c.user_email}</small></div>
                          </div>
                        </td>
                        <td><span className={`rp-badge rp-badge--${c.status}`}>{c.status?.replace(/_/g, ' ')}</span></td>
                        <td><span className={`rp-score ${scoreCls(c.scores?.interview_score)}`}>{fmt(c.scores?.interview_score)}</span></td>
                        <td style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>{c.applied_at ? new Date(c.applied_at).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div>
          {/* Job Summary */}
          <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
            <div className="rp-card-header">
              <h2 className="rp-card-title">Jobs Summary</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {[
                { label: 'Open', count: dash.open_jobs, color: 'var(--rp-success)' },
                { label: 'Draft', count: dash.draft_jobs, color: 'var(--rp-muted)' },
                { label: 'Closed', count: dash.closed_jobs, color: 'var(--rp-danger)' },
              ].map(j => (
                <div key={j.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--rp-border)' }}>
                  <span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>{j.label}</span>
                  <span style={{ fontWeight: 600, color: j.color }}>{j.count}</span>
                </div>
              ))}
            </div>
            <button className="rp-btn rp-btn--primary" style={{ width: '100%', marginTop: '1rem', justifyContent: 'center' }} onClick={() => nav('/recruiter/jobs')}>
              <Briefcase size={16} /> Manage Jobs
            </button>
          </div>

          {/* Recent Activity */}
          <div className="rp-card">
            <div className="rp-card-header">
              <h2 className="rp-card-title">Recent Activity</h2>
            </div>
            {dash.recent_activities.length === 0 ? (
              <p style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>No activity yet</p>
            ) : (
              <div className="rp-activity">
                {dash.recent_activities.slice(0, 6).map((a: any) => (
                  <div key={a.id} className="rp-activity-item">
                    <div className={`rp-activity-dot rp-activity-dot--${a.target_type || 'job'}`} />
                    <div>
                      <div className="rp-activity-text">{a.action?.replace(/_/g, ' ')}</div>
                      <div className="rp-activity-time">{a.created_at ? new Date(a.created_at).toLocaleString() : ''}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
