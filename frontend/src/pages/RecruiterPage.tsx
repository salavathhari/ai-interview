import { BarChart3, BriefcaseBusiness, ClipboardList, Plus, Search, Sparkles, Users } from 'lucide-react';
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
      <div className="recruiter-shell">
        <div className="recruiter-skeleton header" />
        <div className="recruiter-skeleton grid" />
        <div className="recruiter-skeleton table" />
      </div>
    );
  }

  return (
    <div className="recruiter-shell">
      <header className="recruiter-header">
        <div>
          <p className="recruiter-eyebrow">Recruiter Dashboard</p>
          <h1>Hiring Command Center</h1>
          <span>Rank candidates, inspect interview quality, and decide next steps.</span>
        </div>
        <button type="button" className="create-role-button" onClick={() => setShowCreate((value) => !value)}>
          <Plus size={16} />
          Create Job Role
        </button>
      </header>

      {error && <div className="recruiter-alert">{error}</div>}

      {showCreate && (
        <section className="create-role-panel">
          <label>
            <span>Job title</span>
            <input value={newJob.title} onChange={(event) => setNewJob({ ...newJob, title: event.target.value })} placeholder="Senior Backend Engineer" />
          </label>
          <label>
            <span>Description</span>
            <textarea value={newJob.description} onChange={(event) => setNewJob({ ...newJob, description: event.target.value })} placeholder="Role overview and team context" />
          </label>
          <label>
            <span>Requirements</span>
            <textarea value={newJob.requirements} onChange={(event) => setNewJob({ ...newJob, requirements: event.target.value })} placeholder="Python, distributed systems, SQL, cloud infrastructure" />
          </label>
          <button type="button" onClick={createJob} disabled={saving}>
            {saving ? 'Publishing' : 'Publish Role'}
          </button>
        </section>
      )}

      <section className="recruiter-metrics">
        <article>
          <BriefcaseBusiness size={18} />
          <span>Open Roles</span>
          <strong>{dashboard?.active_jobs ?? 0}</strong>
        </article>
        <article>
          <Users size={18} />
          <span>Candidates</span>
          <strong>{dashboard?.total_applicants ?? 0}</strong>
        </article>
        <article>
          <BarChart3 size={18} />
          <span>Average Score</span>
          <strong>{formatScore(dashboard?.avg_candidate_score ?? null)}</strong>
        </article>
        <article>
          <Sparkles size={18} />
          <span>Top Candidate</span>
          <strong>{topCandidate?.user_name ?? 'Pending'}</strong>
        </article>
      </section>

      <main className="recruiter-grid">
        <section className="candidate-panel">
          <div className="panel-heading">
            <div>
              <h2>Candidate Table</h2>
              <p>Ranked by interview performance and recency.</p>
            </div>
            <label className="candidate-search">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search candidates" />
            </label>
          </div>

          <div className="candidate-table-wrap">
            <table className="candidate-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Interview Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-row">No candidates match this view.</td>
                  </tr>
                ) : (
                  filteredCandidates.map((candidate, index) => (
                    <tr key={candidate.session_id}>
                      <td>#{candidate.rank ?? index + 1}</td>
                      <td>
                        <div className="candidate-cell">
                          <span>{candidate.user_name?.charAt(0)?.toUpperCase() || 'C'}</span>
                          <div>
                            <strong>{candidate.user_name}</strong>
                            <small>{candidate.user_email}</small>
                          </div>
                        </div>
                      </td>
                      <td>{formatScore(candidate.score)}</td>
                      <td><span className={`candidate-status ${candidate.status}`}>{candidate.status}</span></td>
                      <td>{new Date(candidate.started_at).toLocaleDateString()}</td>
                      <td>
                        <button type="button" className="table-action" onClick={() => navigate(`/report/${candidate.session_id}`)}>
                          Report
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="recruiter-side">
          <section className="insight-panel">
            <div className="panel-heading compact">
              <h2>Strongest Skills</h2>
            </div>
            <div className="skill-list">
              {strongestSkills.map((skill, index) => (
                <div key={skill} className="skill-row">
                  <span>{skill}</span>
                  <div><i style={{ width: `${Math.max(42, 92 - index * 12)}%` }} /></div>
                </div>
              ))}
            </div>
          </section>

          <section className="insight-panel">
            <div className="panel-heading compact">
              <h2>Hiring Recommendations</h2>
            </div>
            <div className="recommendation-list">
              {recommendations.map((item) => (
                <article key={item}>
                  <ClipboardList size={16} />
                  <p>{item}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="insight-panel job-panel">
            <div className="panel-heading compact">
              <h2>Active Roles</h2>
            </div>
            <div className="job-list">
              {jobs.length === 0 ? <p>No active roles yet.</p> : jobs.slice(0, 5).map((job) => (
                <article key={job.id}>
                  <strong>{job.title}</strong>
                  <span>{job.invite_code ? `Invite ${job.invite_code}` : 'No invite code'}</span>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
};

export default RecruiterPage;
