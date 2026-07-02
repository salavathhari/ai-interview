import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, MapPin, Briefcase, DollarSign, Clock, Building2,
  Filter, X, ChevronDown, Sparkles, ArrowRight, TrendingUp
} from 'lucide-react';
import { candidateApi } from '../../services/api';
import './candidate.css';

type Job = {
  id: number; title: string; description?: string; company_name?: string;
  department?: string; location?: string; employment_type?: string;
  experience_level?: string; salary_min?: number; salary_max?: number;
  salary_currency?: string; required_skills?: string[]; preferred_skills?: string[];
  education?: string; benefits?: string[]; deadline?: string;
  posted_at?: string; created_at: string; has_applied?: boolean;
  readiness_match?: number;
};

const fmtSalary = (min?: number, max?: number, currency?: string) => {
  if (!min && !max) return null;
  const c = currency || 'USD';
  const fmt = (n: number) => n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)} ${c}`;
  if (min) return `From ${fmt(min)} ${c}`;
  return `Up to ${fmt(max!)} ${c}`;
};

const timeAgo = (d?: string) => {
  if (!d) return '';
  const diff = Date.now() - new Date(d).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
};

const EMP_LABELS: Record<string, string> = {
  full_time: 'Full-time', part_time: 'Part-time', contract: 'Contract', intern: 'Internship',
};
const EXP_LABELS: Record<string, string> = {
  junior: 'Junior', mid: 'Mid-Level', senior: 'Senior', lead: 'Lead',
};

export default function CandidateJobsPage() {
  const nav = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [location, setLocation] = useState('');
  const [empType, setEmpType] = useState('');
  const [expLevel, setExpLevel] = useState('');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const fetchJobs = useCallback(() => {
    setLoading(true);
    const params: any = { page, per_page: 12 };
    if (search) params.search = search;
    if (location) params.location = location;
    if (empType) params.employment_type = empType;
    if (expLevel) params.experience_level = expLevel;
    candidateApi.getJobs(params)
      .then(r => { setJobs(r.data.jobs || []); setTotal(r.data.total || 0); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, search, location, empType, expLevel]);

  useEffect(() => { fetchJobs(); }, [page]);

  const handleSearch = () => { setPage(1); fetchJobs(); };
  const clearFilters = () => { setEmpType(''); setExpLevel(''); setLocation(''); setSearch(''); setPage(1); };
  const hasActiveFilters = empType || expLevel || location || search;

  const activeFilters: { label: string; onClear: () => void }[] = [];
  if (search) activeFilters.push({ label: `"${search}"`, onClear: () => { setSearch(''); } });
  if (location) activeFilters.push({ label: location, onClear: () => { setLocation(''); } });
  if (empType) activeFilters.push({ label: EMP_LABELS[empType] || empType, onClear: () => { setEmpType(''); } });
  if (expLevel) activeFilters.push({ label: EXP_LABELS[expLevel] || expLevel, onClear: () => { setExpLevel(''); } });

  return (
    <div className="cj-page">
      {/* Hero */}
      <div className="cj-hero">
        <div className="cj-hero-content">
          <div className="cj-hero-badge"><Sparkles size={14} /> Open Positions</div>
          <h1 className="cj-hero-title">Find Your Next Role</h1>
          <p className="cj-hero-sub">
            {total > 0
              ? `${total} ${total === 1 ? 'opportunity' : 'opportunities'} waiting for you`
              : 'Discover opportunities that match your skills and career goals'}
          </p>
        </div>

        {/* Search */}
        <div className="cj-search-container">
          <div className="cj-search-bar">
            <div className="cj-search-field">
              <Search size={18} className="cj-search-icon" />
              <input
                placeholder="Job title, keyword, or company"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div className="cj-search-divider" />
            <div className="cj-search-field">
              <MapPin size={18} className="cj-search-icon" />
              <input
                placeholder="City, state, or remote"
                value={location}
                onChange={e => setLocation(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <button className="cj-search-btn" onClick={handleSearch}>
              <Search size={18} />
              Search
            </button>
          </div>

          <div className="cj-search-actions">
            <button className="cj-filter-toggle" onClick={() => setShowFilters(!showFilters)}>
              <Filter size={15} />
              Filters
              <ChevronDown size={14} style={{ transform: showFilters ? 'rotate(180deg)' : 'none', transition: '0.2s' }} />
            </button>
            {(empType || expLevel) && (
              <button className="cj-clear-btn" onClick={clearFilters}>
                <X size={14} /> Clear all
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="cj-filter-panel">
          <div className="cj-filter-group">
            <label className="cj-filter-label">Employment Type</label>
            <div className="cj-filter-chips">
              {[
                { val: '', label: 'All' },
                { val: 'full_time', label: 'Full-time' },
                { val: 'part_time', label: 'Part-time' },
                { val: 'contract', label: 'Contract' },
                { val: 'intern', label: 'Internship' },
              ].map(opt => (
                <button key={opt.val} className={`cj-chip ${empType === opt.val ? 'cj-chip--active' : ''}`}
                  onClick={() => { setEmpType(opt.val); }}>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <div className="cj-filter-group">
            <label className="cj-filter-label">Experience Level</label>
            <div className="cj-filter-chips">
              {[
                { val: '', label: 'All' },
                { val: 'junior', label: 'Junior' },
                { val: 'mid', label: 'Mid-Level' },
                { val: 'senior', label: 'Senior' },
                { val: 'lead', label: 'Lead' },
              ].map(opt => (
                <button key={opt.val} className={`cj-chip ${expLevel === opt.val ? 'cj-chip--active' : ''}`}
                  onClick={() => { setExpLevel(opt.val); }}>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Active Filter Pills */}
      {activeFilters.length > 0 && (
        <div className="cj-active-filters">
          {activeFilters.map((f, i) => (
            <span key={i} className="cj-active-pill">
              {f.label}
              <button onClick={() => { f.onClear(); }}>
                <X size={12} />
              </button>
            </span>
          ))}
          <button className="cj-clear-link" onClick={clearFilters}>Clear all</button>
        </div>
      )}

      {/* Results Header */}
      <div className="cj-results-header">
        <span className="cj-results-count">
          {loading ? 'Searching...' : `${total} ${total === 1 ? 'job' : 'jobs'} found`}
        </span>
      </div>

      {/* Job Grid */}
      {loading ? (
        <div className="cj-grid">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="cj-skeleton-card">
              <div className="cj-skel-row"><div className="cj-skel-icon" /><div className="cj-skel-text cj-skel-text--lg" /></div>
              <div className="cj-skel-text cj-skel-text--sm" />
              <div className="cj-skel-row"><div className="cj-skel-text cj-skel-text--xs" /><div className="cj-skel-text cj-skel-text--xs" /><div className="cj-skel-text cj-skel-text--xs" /></div>
              <div className="cj-skel-row"><div className="cj-skel-tag" /><div className="cj-skel-tag" /><div className="cj-skel-tag" /></div>
            </div>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="cj-empty">
          <div className="cj-empty-icon"><Briefcase size={40} /></div>
          <h3>No jobs match your criteria</h3>
          <p>Try broadening your search or adjusting filters</p>
          {hasActiveFilters && (
            <button className="cj-btn-primary" onClick={clearFilters}>Clear all filters</button>
          )}
        </div>
      ) : (
        <div className="cj-grid">
          {jobs.map(job => (
            <div key={job.id} className="cj-card" onClick={() => nav(`/jobs/${job.id}`)}>
              <div className="cj-card-top">
                <div className="cj-card-icon">
                  <Building2 size={20} />
                </div>
                <div className="cj-card-info">
                  <h3 className="cj-card-title">{job.title}</h3>
                  <span className="cj-card-company">{job.company_name || 'Hiring Company'}</span>
                </div>
                {job.has_applied && (
                  <span className="cj-applied-badge">
                    <span className="cj-applied-dot" /> Applied
                  </span>
                )}
              </div>

              <div className="cj-card-meta">
                {job.location && <span className="cj-meta-item"><MapPin size={13} />{job.location}</span>}
                {job.employment_type && <span className="cj-meta-item"><Briefcase size={13} />{EMP_LABELS[job.employment_type] || job.employment_type}</span>}
                {job.experience_level && <span className="cj-meta-item">{EXP_LABELS[job.experience_level] || job.experience_level}</span>}
                {fmtSalary(job.salary_min, job.salary_max, job.salary_currency) && (
                  <span className="cj-meta-item cj-meta-salary">
                    <DollarSign size={13} />{fmtSalary(job.salary_min, job.salary_max, job.salary_currency)}
                  </span>
                )}
              </div>

              {job.description && (
                <p className="cj-card-desc">{job.description.slice(0, 140)}{job.description.length > 140 ? '...' : ''}</p>
              )}

              {job.required_skills && job.required_skills.length > 0 && (
                <div className="cj-card-skills">
                  {job.required_skills.slice(0, 4).map(s => (
                    <span key={s} className="cj-skill">{s}</span>
                  ))}
                  {job.required_skills.length > 4 && (
                    <span className="cj-skill cj-skill--more">+{job.required_skills.length - 4}</span>
                  )}
                </div>
              )}

              <div className="cj-card-footer">
                <span className="cj-card-time"><Clock size={12} />{timeAgo(job.posted_at || job.created_at)}</span>
                <div className="cj-card-actions">
                  {job.readiness_match != null && job.readiness_match > 0 && (
                    <span className={`cj-match-badge ${job.readiness_match >= 70 ? 'cj-match-badge--high' : job.readiness_match >= 40 ? 'cj-match-badge--mid' : 'cj-match-badge--low'}`}>
                      <TrendingUp size={12} />{job.readiness_match.toFixed(0)}% match
                    </span>
                  )}
                  <span className="cj-view-link">View <ArrowRight size={14} /></span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > 12 && (
        <div className="cj-pagination">
          <button className="cj-page-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
            Previous
          </button>
          <div className="cj-page-info">
            {Array.from({ length: Math.min(Math.ceil(total / 12), 7) }, (_, i) => {
              const totalPages = Math.ceil(total / 12);
              let pageNum: number;
              if (totalPages <= 7) {
                pageNum = i + 1;
              } else if (page <= 4) {
                pageNum = i + 1;
              } else if (page >= totalPages - 3) {
                pageNum = totalPages - 6 + i;
              } else {
                pageNum = page - 3 + i;
              }
              return (
                <button key={pageNum} className={`cj-page-num ${page === pageNum ? 'cj-page-num--active' : ''}`}
                  onClick={() => setPage(pageNum)}>
                  {pageNum}
                </button>
              );
            })}
          </div>
          <button className="cj-page-btn" disabled={page >= Math.ceil(total / 12)} onClick={() => setPage(p => p + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
