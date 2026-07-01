import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Users } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type App = { id: number; job_post_id: number; user_id: number; user_name: string; user_email: string; status: string; ats_score?: number; interview_score?: number; coding_score?: number; career_readiness?: number; source?: string; applied_at: string; };

export default function RecruiterApplicationsPage() {
  const nav = useNavigate();
  const [apps, setApps] = useState<App[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [jobFilter, setJobFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    recruiterApi.getJobs({ per_page: 100 }).then(r => setJobs(r.data.jobs)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const fetchAll = async () => {
      const allApps: App[] = [];
      const jobList = jobFilter ? jobs.filter(j => j.id === parseInt(jobFilter)) : jobs;
      for (const job of jobList) {
        try {
          const r = await recruiterApi.getApplications(job.id, { stage: stageFilter || undefined, search: search || undefined, per_page: 100 });
          allApps.push(...r.data.applications.map((a: any) => ({ ...a, _jobTitle: job.title })));
        } catch {}
      }
      setApps(allApps);
      setLoading(false);
    };
    if (jobs.length > 0) fetchAll();
    else setLoading(false);
  }, [jobs, jobFilter, stageFilter, search]);

  const STAGES = ['applied', 'screening', 'interview_scheduled', 'interview_completed', 'coding_round', 'selected', 'rejected', 'offer_released', 'hired'];

  return (
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select className="rp-select" style={{ width: 200 }} value={jobFilter} onChange={e => setJobFilter(e.target.value)}>
          <option value="">All Jobs</option>
          {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
        </select>
        <select className="rp-select" style={{ width: 200 }} value={stageFilter} onChange={e => setStageFilter(e.target.value)}>
          <option value="">All Stages</option>
          {STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <div style={{ position: 'relative', flex: 1, maxWidth: 300 }}>
          <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--rp-muted)' }} />
          <input className="rp-input" style={{ paddingLeft: 32 }} placeholder="Search candidates..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>{apps.length} application{apps.length !== 1 ? 's' : ''}</span>
      </div>

      {loading ? (
        [1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 60, marginBottom: 8 }} />)
      ) : apps.length === 0 ? (
        <div className="rp-card rp-empty"><div className="rp-empty-icon"><Users size={24} /></div><h3>No applications found</h3></div>
      ) : (
        <div className="rp-card">
          <div className="rp-table-wrap">
            <table className="rp-table">
              <thead>
                <tr><th>Candidate</th><th>Job</th><th>Stage</th><th>ATS</th><th>Interview</th><th>Coding</th><th>Readiness</th><th>Source</th><th>Applied</th></tr>
              </thead>
              <tbody>
                {apps.map(app => (
                  <tr key={app.id} style={{ cursor: 'pointer' }} onClick={() => nav(`/recruiter/candidates/${app.user_id}`)}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div className="rp-avatar">{(app.user_name?.[0] || 'U').toUpperCase()}</div>
                        <div><strong>{app.user_name}</strong><br /><small style={{ color: 'var(--rp-muted)' }}>{app.user_email}</small></div>
                      </div>
                    </td>
                    <td style={{ fontSize: '0.85rem' }}>{(app as any)._jobTitle || '-'}</td>
                    <td><span className={`rp-badge rp-badge--${app.status}`}>{app.status?.replace(/_/g, ' ')}</span></td>
                    <td><span className={`rp-score ${app.ats_score != null ? (app.ats_score >= 70 ? 'rp-score--high' : 'rp-score--mid') : ''}`}>{app.ats_score != null ? app.ats_score.toFixed(0) : '-'}</span></td>
                    <td><span className={`rp-score ${app.interview_score != null ? (app.interview_score >= 8 ? 'rp-score--high' : app.interview_score >= 6 ? 'rp-score--mid' : 'rp-score--low') : ''}`}>{app.interview_score != null ? app.interview_score.toFixed(1) : '-'}</span></td>
                    <td><span className={`rp-score ${app.coding_score != null ? (app.coding_score >= 80 ? 'rp-score--high' : 'rp-score--mid') : ''}`}>{app.coding_score != null ? app.coding_score.toFixed(0) : '-'}</span></td>
                    <td><span className={`rp-score ${app.career_readiness != null ? (app.career_readiness >= 70 ? 'rp-score--high' : 'rp-score--mid') : ''}`}>{app.career_readiness != null ? app.career_readiness.toFixed(0) : '-'}</span></td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{app.source || '-'}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{app.applied_at ? new Date(app.applied_at).toLocaleDateString() : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
