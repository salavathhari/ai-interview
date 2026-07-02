import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Briefcase, MapPin, MoreVertical, Copy, Archive, Trash2, Eye, Edit } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Job = {
  id: number; title: string; department?: string; location?: string;
  status: string; application_count: number; employment_type?: string;
  experience_level?: string; salary_min?: number; salary_max?: number;
  created_at: string; posted_at?: string;
};

const statusOrder = ['all', 'open', 'draft', 'closed', 'archived'];

export default function RecruiterJobsPage() {
  const nav = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [menuOpen, setMenuOpen] = useState<number | null>(null);

  const fetchJobs = () => {
    setLoading(true);
    const params: any = { per_page: 50 };
    if (statusFilter !== 'all') params.status = statusFilter;
    if (search) params.search = search;
    recruiterApi.getJobs(params).then(r => { setJobs(r.data.jobs); setTotal(r.data.total); }).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { fetchJobs(); }, [statusFilter, search]);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this job? This cannot be undone.')) return;
    await recruiterApi.deleteJob(id);
    fetchJobs();
    setMenuOpen(null);
  };

  const handleDuplicate = async (id: number) => {
    await recruiterApi.duplicateJob(id);
    fetchJobs();
    setMenuOpen(null);
  };

  const handleStatusChange = async (id: number, status: string) => {
    await recruiterApi.updateJobStatus(id, status);
    fetchJobs();
    setMenuOpen(null);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <p style={{ color: 'var(--rp-muted)', margin: 0, fontSize: '0.85rem' }}>{total} job posting{total !== 1 ? 's' : ''}</p>
        </div>
        <button className="rp-btn rp-btn--primary" onClick={() => nav('/recruiter/jobs/create')}>
          <Plus size={16} /> Create Job
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="rp-tabs" style={{ margin: 0, border: 'none' }}>
          {statusOrder.map(s => (
            <button key={s} className={`rp-tab ${statusFilter === s ? 'active' : ''}`} onClick={() => setStatusFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ position: 'relative', flex: 1, maxWidth: 300 }}>
          <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--rp-muted)' }} />
          <input className="rp-input" style={{ paddingLeft: 32 }} placeholder="Search jobs..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      {/* Job Cards */}
      {loading ? (
        [1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 100, marginBottom: 12 }} />)
      ) : jobs.length === 0 ? (
        <div className="rp-card rp-empty">
          <div className="rp-empty-icon"><Briefcase size={24} /></div>
          <h3>No jobs found</h3>
          <p>Create your first job posting to start hiring.</p>
          <button className="rp-btn rp-btn--primary" style={{ marginTop: '1rem' }} onClick={() => nav('/recruiter/jobs/create')}>
            <Plus size={16} /> Create Job
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {jobs.map(job => (
            <div key={job.id} className="rp-card" style={{ padding: '1rem 1.25rem', cursor: 'pointer', position: 'relative' }}
                 onClick={() => nav(`/recruiter/jobs/${job.id}`)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>{job.title}</h3>
                    <span className={`rp-badge rp-badge--${job.status}`}>{job.status}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--rp-muted)' }}>
                    {job.department && <span>{job.department}</span>}
                    {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><MapPin size={13} /> {job.location}</span>}
                    {job.employment_type && <span>{job.employment_type.replace(/_/g, ' ')}</span>}
                    {job.experience_level && <span>{job.experience_level}</span>}
                    {job.salary_min && <span>${job.salary_min.toLocaleString()}{job.salary_max ? ` - $${job.salary_max.toLocaleString()}` : ''}</span>}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{job.application_count}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--rp-muted)' }}>applications</div>
                  </div>
                  <div style={{ position: 'relative' }}>
                    <button className="rp-btn rp-btn--ghost rp-btn--sm" onClick={e => { e.stopPropagation(); setMenuOpen(menuOpen === job.id ? null : job.id); }}>
                      <MoreVertical size={16} />
                    </button>
                    {menuOpen === job.id && (
                      <div style={{ position: 'absolute', right: 0, top: '100%', background: 'var(--rp-surface)', border: '1px solid var(--rp-border)', borderRadius: 8, padding: '0.5rem', zIndex: 20, minWidth: 160 }}>
                        <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={e => { e.stopPropagation(); nav(`/recruiter/jobs/${job.id}`); }}><Eye size={14} /> View</button>
                        <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={e => { e.stopPropagation(); nav(`/recruiter/jobs/${job.id}/edit`); }}><Edit size={14} /> Edit</button>
                        <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={e => { e.stopPropagation(); handleDuplicate(job.id); }}><Copy size={14} /> Duplicate</button>
                        {job.status === 'open' && <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={e => { e.stopPropagation(); handleStatusChange(job.id, 'closed'); }}><Archive size={14} /> Close</button>}
                        {job.status === 'draft' && <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start', color: 'var(--rp-success)' }} onClick={e => { e.stopPropagation(); handleStatusChange(job.id, 'open'); }}>Publish</button>}
                        <button className="rp-btn rp-btn--ghost rp-btn--sm" style={{ width: '100%', justifyContent: 'flex-start', color: 'var(--rp-danger)' }} onClick={e => { e.stopPropagation(); handleDelete(job.id); }}><Trash2 size={14} /> Delete</button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
