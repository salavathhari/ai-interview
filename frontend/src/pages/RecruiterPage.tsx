import { Briefcase, Users, BarChart3, Sparkles, Plus, Search, ClipboardList, ArrowRight, Loader2, Eye } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { getAccessToken } from '../services/api';
import './RecruiterPage.css';

type Candidate = {
  session_id: number;
  user_email: string;
  user_name: string;
  score: number | null;
  status: string;
  started_at: string;
  rank?: number;
};

type JobRole = {
  id: number;
  title: string;
  description: string;
  requirements: string;
  invite_code?: string;
  is_active: boolean;
};

type RecruiterDashboard = {
  active_jobs: number;
  total_applicants: number;
  avg_candidate_score: number;
  recent_candidates: Candidate[];
  strongest_skills: string[];
  hiring_recommendations: string[];
};

const formatScore = (score: number | null) => (score === null || score === undefined ? 'N/A' : `${score.toFixed(1)}/10`);

const scoreColor = (score: number | null) => {
  if (score === null) return '';
  if (score >= 8) return 'score-high';
  if (score >= 6) return 'score-mid';
  return 'score-low';
};

const RecruiterPage = () => {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<RecruiterDashboard | null>(null);
  const [jobs, setJobs] = useState<JobRole[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newJob, setNewJob] = useState({ title: '', description: '', requirements: '' });
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      const [dashboardResponse, jobsResponse] = await Promise.all([
        api.get('/recruiter/dashboard'),
        api.get('/recruiter/jobs'),
      ]);
      setDashboard(dashboardResponse.data);
      setJobs(jobsResponse.data);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Unable to load recruiter dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      navigate('/login');
      return;
    }
    fetchData();
  }, [navigate]);

  const filteredCandidates = useMemo(() => {
    const candidates = dashboard?.recent_candidates ?? [];
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return candidates;
    return candidates.filter((candidate) => (
      candidate.user_name.toLowerCase().includes(normalizedQuery)
      || candidate.user_email.toLowerCase().includes(normalizedQuery)
      || candidate.status.toLowerCase().includes(normalizedQuery)
    ));
  }, [dashboard, query]);

  const topCandidate = dashboard?.recent_candidates?.[0];
  const strongestSkills = dashboard?.strongest_skills?.length ? dashboard.strongest_skills : ['Communication', 'Problem Solving', 'Core CS'];
  const recommendations = dashboard?.hiring_recommendations?.length
    ? dashboard.hiring_recommendations
    : ['Complete more candidate interviews to generate hiring recommendations.'];

  const createJob = async () => {
    if (!newJob.title.trim()) return;
    setSaving(true);
    try {
      await api.post('/recruiter/jobs', newJob);
      setNewJob({ title: '', description: '', requirements: '' });
      setShowCreate(false);
      fetchData();
    } catch (err) {
      console.error(err);
      setError('Failed to create job role.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rp">
        <div className="rp-skeleton rp-skeleton--header" />
        <div className="rp-skeleton rp-skeleton--metrics" />
        <div className="rp-skeleton rp-skeleton--content" />
      </div>
    );
  }

  return (
    <div className="rp">
      {/* Header */}
      <div className="rp-header">
        <div>
          <p className="rp-eyebrow">Recruiter</p>
          <h1>Hiring Command Center</h1>
          <p className="rp-subtitle">Rank candidates, inspect interview quality, and decide next steps.</p>
        </div>
        <button type="button" className="rp-btn rp-btn--primary" onClick={() => setShowCreate(!showCreate)}>
          <Plus size={16} />
          Create Job Role
        </button>
      </div>

      {error && <div className="rp-alert">{error}</div>}

      {/* Create Job Panel */}
      {showCreate && (
        <div className="rp-panel rp-create">
          <div className="rp-panel-header">
            <h2>New Job Role</h2>
            <button type="button" className="rp-btn rp-btn--ghost" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
          <div className="rp-create-grid">
            <div className="rp-field">
              <label>Job Title</label>
              <input value={newJob.title} onChange={(e) => setNewJob({ ...newJob, title: e.target.value })} placeholder="Senior Backend Engineer" />
            </div>
            <div className="rp-field">
              <label>Description</label>
              <textarea value={newJob.description} onChange={(e) => setNewJob({ ...newJob, description: e.target.value })} placeholder="Role overview and team context" rows={3} />
            </div>
            <div className="rp-field">
              <label>Requirements</label>
              <textarea value={newJob.requirements} onChange={(e) => setNewJob({ ...newJob, requirements: e.target.value })} placeholder="Python, distributed systems, SQL, cloud infrastructure" rows={3} />
            </div>
          </div>
          <div className="rp-create-actions">
            <button type="button" className="rp-btn rp-btn--primary" onClick={createJob} disabled={saving || !newJob.title.trim()}>
              {saving ? <><Loader2 size={14} className="spin" /> Publishing...</> : <><Plus size={14} /> Publish Role</>}
            </button>
          </div>
        </div>
      )}

      {/* Metrics */}
      <div className="rp-metrics">
        <div className="rp-metric-card">
          <div className="rp-metric-icon rp-metric-icon--blue"><Briefcase size={18} /></div>
          <div className="rp-metric-body">
            <span>Open Roles</span>
            <strong>{dashboard?.active_jobs ?? 0}</strong>
          </div>
        </div>
        <div className="rp-metric-card">
          <div className="rp-metric-icon rp-metric-icon--green"><Users size={18} /></div>
          <div className="rp-metric-body">
            <span>Candidates</span>
            <strong>{dashboard?.total_applicants ?? 0}</strong>
          </div>
        </div>
        <div className="rp-metric-card">
          <div className="rp-metric-icon rp-metric-icon--purple"><BarChart3 size={18} /></div>
          <div className="rp-metric-body">
            <span>Average Score</span>
            <strong>{formatScore(dashboard?.avg_candidate_score ?? null)}</strong>
          </div>
        </div>
        <div className="rp-metric-card">
          <div className="rp-metric-icon rp-metric-icon--amber"><Sparkles size={18} /></div>
          <div className="rp-metric-body">
            <span>Top Candidate</span>
            <strong className="rp-metric-name">{topCandidate?.user_name ?? 'Pending'}</strong>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="rp-grid">
        {/* Candidate Table */}
        <div className="rp-panel rp-candidates">
          <div className="rp-panel-header">
            <div>
              <h2>Candidates</h2>
              <p className="rp-panel-sub">Ranked by interview performance and recency.</p>
            </div>
            <div className="rp-search">
              <Search size={15} />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search candidates..." />
            </div>
          </div>

          <div className="rp-table-wrap">
            <table className="rp-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredCandidates.length === 0 ? (
                  <tr><td colSpan={6} className="rp-empty">No candidates match this view.</td></tr>
                ) : (
                  filteredCandidates.map((candidate, index) => (
                    <tr key={candidate.session_id}>
                      <td className="rp-rank">#{candidate.rank ?? index + 1}</td>
                      <td>
                        <div className="rp-candidate">
                          <div className="rp-candidate-avatar">{(candidate.user_name?.charAt(0) || 'C').toUpperCase()}</div>
                          <div>
                            <strong>{candidate.user_name}</strong>
                            <small>{candidate.user_email}</small>
                          </div>
                        </div>
                      </td>
                      <td><span className={`rp-score ${scoreColor(candidate.score)}`}>{formatScore(candidate.score)}</span></td>
                      <td><span className={`rp-status rp-status--${candidate.status}`}>{candidate.status}</span></td>
                      <td className="rp-date">{new Date(candidate.started_at).toLocaleDateString()}</td>
                      <td>
                        <button type="button" className="rp-btn rp-btn--ghost rp-btn--sm" onClick={() => navigate(`/report/${candidate.session_id}`)}>
                          <Eye size={14} /> View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Side Panels */}
        <div className="rp-side">
          {/* Strongest Skills */}
          <div className="rp-panel">
            <div className="rp-panel-header rp-panel-header--compact">
              <h2>Strongest Skills</h2>
            </div>
            <div className="rp-skills">
              {strongestSkills.map((skill, index) => (
                <div key={skill} className="rp-skill">
                  <div className="rp-skill-info">
                    <span>{skill}</span>
                    <span className="rp-skill-pct">{Math.max(42, 92 - index * 12)}%</span>
                  </div>
                  <div className="rp-skill-bar">
                    <div className="rp-skill-fill" style={{ width: `${Math.max(42, 92 - index * 12)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="rp-panel">
            <div className="rp-panel-header rp-panel-header--compact">
              <h2>Hiring Recommendations</h2>
            </div>
            <div className="rp-recommendations">
              {recommendations.map((item) => (
                <div key={item} className="rp-recommendation">
                  <ClipboardList size={15} />
                  <p>{item}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Active Roles */}
          <div className="rp-panel">
            <div className="rp-panel-header rp-panel-header--compact">
              <h2>Active Roles</h2>
            </div>
            <div className="rp-jobs">
              {jobs.length === 0 ? (
                <p className="rp-empty-text">No active roles yet. Create one to get started.</p>
              ) : (
                jobs.slice(0, 5).map((job) => (
                  <div key={job.id} className="rp-job-card">
                    <div className="rp-job-info">
                      <strong>{job.title}</strong>
                      <span>{job.invite_code ? `Invite: ${job.invite_code}` : 'No invite code'}</span>
                    </div>
                    <ArrowRight size={14} />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecruiterPage;
