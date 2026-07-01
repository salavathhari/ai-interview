import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Plus, Users, Edit, MapPin, Calendar, DollarSign } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Job = { id: number; title: string; description?: string; requirements?: string; department?: string; location?: string; status: string; employment_type?: string; experience_level?: string; salary_min?: number; salary_max?: number; required_skills?: string[]; preferred_skills?: string[]; education?: string; responsibilities?: string[]; benefits?: string[]; application_count?: number; invite_code?: string; created_at: string; posted_at?: string; };
type App = { id: number; user_id: number; user_name: string; user_email: string; status: string; ats_score?: number; resume_match?: number; interview_score?: number; coding_score?: number; career_readiness?: number; applied_at: string; source?: string; };

const STAGES = ['applied', 'screening', 'interview_scheduled', 'interview_completed', 'coding_round', 'selected', 'rejected', 'offer_released', 'hired'];

export default function RecruiterJobDetailPage() {
  const nav = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [apps, setApps] = useState<App[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'applications' | 'settings'>('applications');
  const [stageFilter, setStageFilter] = useState('');
  const [search, setSearch] = useState('');
  const [stageCounts, setStageCounts] = useState<Record<string, number>>({});

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      recruiterApi.getJob(parseInt(jobId!)),
      recruiterApi.getApplications(parseInt(jobId!), { stage: stageFilter || undefined, search: search || undefined, per_page: 50 }),
    ]).then(([jobRes, appsRes]) => {
      setJob(jobRes.data);
      setApps(appsRes.data.applications);
      setTotal(appsRes.data.total);
      setStageCounts(appsRes.data.stage_counts || {});
    }).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [jobId, stageFilter, search]);

  const handleStageChange = async (appId: number, newStage: string) => {
    await recruiterApi.updateStage(appId, { status: newStage });
    fetchData();
  };

  const handleStatusChange = async (status: string) => {
    if (!job) return;
    await recruiterApi.updateJobStatus(job.id, status);
    fetchData();
  };

  if (loading) return <div>{[1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 60, marginBottom: 8 }} />)}</div>;
  if (!job) return <div className="rp-empty"><h3>Job not found</h3></div>;

  return (
    <div>
      <button className="rp-btn rp-btn--ghost" onClick={() => nav('/recruiter/jobs')} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> Back to Jobs
      </button>

      {/* Job Header */}
      <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <h2 style={{ margin: 0 }}>{job.title}</h2>
              <span className={`rp-badge rp-badge--${job.status}`}>{job.status}</span>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--rp-muted)', flexWrap: 'wrap' }}>
              {job.department && <span>{job.department}</span>}
              {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={13} /> {job.location}</span>}
              {job.employment_type && <span>{job.employment_type.replace(/_/g, ' ')}</span>}
              {job.experience_level && <span>{job.experience_level}</span>}
              {job.salary_min && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><DollarSign size={13} /> ${job.salary_min.toLocaleString()}{job.salary_max ? ` - $${job.salary_max.toLocaleString()}` : ''}</span>}
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Calendar size={13} /> Created {new Date(job.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="rp-btn rp-btn--secondary rp-btn--sm" onClick={() => nav(`/recruiter/jobs/${jobId}/edit`)}><Edit size={14} /> Edit</button>
            {job.status === 'open' && <button className="rp-btn rp-btn--danger rp-btn--sm" onClick={() => handleStatusChange('closed')}>Close Job</button>}
            {job.status === 'draft' && <button className="rp-btn rp-btn--primary rp-btn--sm" onClick={() => handleStatusChange('open')}>Publish</button>}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="rp-metrics" style={{ marginBottom: '1.5rem' }}>
        <div className="rp-metric">
          <div className="rp-metric-icon rp-metric-icon--blue"><Users size={18} /></div>
          <div className="rp-metric-body">
            <span className="rp-metric-label">Applications</span>
            <span className="rp-metric-value">{total}</span>
          </div>
        </div>
        {Object.entries(stageCounts).slice(0, 4).map(([stage, count]) => (
          <div key={stage} className="rp-metric">
            <div className="rp-metric-body">
              <span className="rp-metric-label">{stage.replace(/_/g, ' ')}</span>
              <span className="rp-metric-value">{count as number}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="rp-tabs">
        <button className={`rp-tab ${tab === 'applications' ? 'active' : ''}`} onClick={() => setTab('applications')}>Applications ({total})</button>
        <button className={`rp-tab ${tab === 'settings' ? 'active' : ''}`} onClick={() => setTab('settings')}>Job Details</button>
      </div>

      {tab === 'applications' && (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <select className="rp-select" style={{ width: 200 }} value={stageFilter} onChange={e => setStageFilter(e.target.value)}>
              <option value="">All Stages</option>
              {STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
            <input className="rp-input" style={{ maxWidth: 250 }} placeholder="Search candidates..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>

          {apps.length === 0 ? (
            <div className="rp-card rp-empty"><h3>No applications yet</h3><p>Candidates will appear here once they apply.</p></div>
          ) : (
            <div className="rp-card">
              <div className="rp-table-wrap">
                <table className="rp-table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Stage</th>
                      <th>ATS</th>
                      <th>Interview</th>
                      <th>Coding</th>
                      <th>Readiness</th>
                      <th>Applied</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {apps.map(app => (
                      <tr key={app.id}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => nav(`/recruiter/candidates/${app.user_id}`)}>
                            <div className="rp-avatar">{(app.user_name?.[0] || 'U').toUpperCase()}</div>
                            <div><strong>{app.user_name}</strong><br /><small style={{ color: 'var(--rp-muted)' }}>{app.user_email}</small></div>
                          </div>
                        </td>
                        <td>
                          <select className="rp-select" style={{ width: 160, padding: '4px 8px', fontSize: '0.8rem' }} value={app.status} onChange={e => handleStageChange(app.id, e.target.value)}>
                            {STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                          </select>
                        </td>
                        <td><span className={`rp-score ${app.ats_score != null ? (app.ats_score >= 70 ? 'rp-score--high' : app.ats_score >= 40 ? 'rp-score--mid' : 'rp-score--low') : ''}`}>{app.ats_score != null ? app.ats_score.toFixed(0) : '-'}</span></td>
                        <td><span className={`rp-score ${app.interview_score != null ? (app.interview_score >= 8 ? 'rp-score--high' : app.interview_score >= 6 ? 'rp-score--mid' : 'rp-score--low') : ''}`}>{app.interview_score != null ? app.interview_score.toFixed(1) : '-'}</span></td>
                        <td><span className={`rp-score ${app.coding_score != null ? (app.coding_score >= 80 ? 'rp-score--high' : app.coding_score >= 50 ? 'rp-score--mid' : 'rp-score--low') : ''}`}>{app.coding_score != null ? app.coding_score.toFixed(0) : '-'}</span></td>
                        <td><span className={`rp-score ${app.career_readiness != null ? (app.career_readiness >= 70 ? 'rp-score--high' : app.career_readiness >= 40 ? 'rp-score--mid' : 'rp-score--low') : ''}`}>{app.career_readiness != null ? app.career_readiness.toFixed(0) : '-'}</span></td>
                        <td style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>{app.applied_at ? new Date(app.applied_at).toLocaleDateString() : '-'}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            <button className="rp-btn rp-btn--ghost rp-btn--sm" title="Shortlist" onClick={() => recruiterApi.shortlist(app.id, { action: 'shortlist' }).then(fetchData)}>S</button>
                            <button className="rp-btn rp-btn--ghost rp-btn--sm" title="Reject" style={{ color: 'var(--rp-danger)' }} onClick={() => recruiterApi.shortlist(app.id, { action: 'reject' }).then(fetchData)}>R</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'settings' && (
        <div className="rp-card">
          {job.description && <div className="rp-field"><label className="rp-label">Description</label><p>{job.description}</p></div>}
          {job.requirements && <div className="rp-field"><label className="rp-label">Requirements</label><p>{job.requirements}</p></div>}
          {job.education && <div className="rp-field"><label className="rp-label">Education</label><p>{job.education}</p></div>}
          {job.required_skills && job.required_skills.length > 0 && (
            <div className="rp-field"><label className="rp-label">Required Skills</label><div className="rp-tags">{job.required_skills.map((s, i) => <span key={i} className="rp-tag">{s}</span>)}</div></div>
          )}
          {job.preferred_skills && job.preferred_skills.length > 0 && (
            <div className="rp-field"><label className="rp-label">Preferred Skills</label><div className="rp-tags">{job.preferred_skills.map((s, i) => <span key={i} className="rp-tag">{s}</span>)}</div></div>
          )}
          {job.responsibilities && job.responsibilities.length > 0 && (
            <div className="rp-field"><label className="rp-label">Responsibilities</label><ul style={{ margin: 0, paddingLeft: '1.25rem' }}>{job.responsibilities.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
          )}
          {job.benefits && job.benefits.length > 0 && (
            <div className="rp-field"><label className="rp-label">Benefits</label><ul style={{ margin: 0, paddingLeft: '1.25rem' }}>{job.benefits.map((b, i) => <li key={i}>{b}</li>)}</ul></div>
          )}
          {job.invite_code && <div className="rp-field"><label className="rp-label">Invite Code</label><p style={{ fontFamily: 'monospace' }}>{job.invite_code}</p></div>}
        </div>
      )}
    </div>
  );
}
