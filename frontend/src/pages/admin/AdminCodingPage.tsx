import React, { useEffect, useState } from 'react';
import {
  Code2,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle2,
  Zap,
  MemoryStick,
  Sparkles,
  BarChart3,
  Trophy,
  Loader2,
  X,
  FileCode,
} from 'lucide-react';
import { adminApi } from '../../services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

type CodingSubmission = {
  id: number;
  candidate_email: string;
  challenge_title: string;
  language: string;
  status: string;
  correctness_score: number | null;
  ai_score: number | null;
  runtime_ms: number | null;
  memory_kb: number | null;
  is_final: boolean;
  created_at: string;
};

type CodingAnalytics = {
  total_submissions: number;
  total_sessions: number;
  avg_correctness_score: number;
  avg_ai_score: number;
  language_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  difficulty_breakdown: Record<string, number>;
};

type SubmissionDetail = CodingSubmission & {
  code: string;
  ai_feedback: string | null;
  time_complexity: string | null;
  space_complexity: string | null;
  test_results: any[];
  hidden_passed: number;
  hidden_total: number;
};

// ─── Component ────────────────────────────────────────────────────────────────

const AdminCodingPage: React.FC = () => {
  const [submissions, setSubmissions] = useState<CodingSubmission[]>([]);
  const [analytics, setAnalytics] = useState<CodingAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterLanguage, setFilterLanguage] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedSubmission, setSelectedSubmission] = useState<SubmissionDetail | null>(null);
  const [, setDetailLoading] = useState(false);

  // ─── Fetch ─────────────────────────────────────────────────────────────────

  const fetchData = async () => {
    setLoading(true);
    try {
      const [subsRes, analyticsRes] = await Promise.all([
        adminApi.getCodingSubmissions({ page, per_page: 20, language: filterLanguage || undefined, status: filterStatus || undefined, search: search || undefined }),
        adminApi.getCodingAnalytics(),
      ]);
      setSubmissions(subsRes.data.submissions || []);
      setTotalPages(subsRes.data.total_pages || 1);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      console.error('Failed to fetch coding data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, filterLanguage, filterStatus]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const viewSubmission = async (id: number) => {
    setDetailLoading(true);
    try {
      const res = await adminApi.getCodingSubmissionDetail(id);
      setSelectedSubmission(res.data);
    } catch { /* silent */ }
    finally { setDetailLoading(false); }
  };

  // ─── Helpers ───────────────────────────────────────────────────────────────

  const statusColor = (s: string) => {
    if (s === 'Accepted') return 'admin-badge-green';
    if (s === 'Wrong Answer' || s === 'Runtime Error' || s === 'Compilation Error') return 'admin-badge-red';
    return 'admin-badge-yellow';
  };

  const langColor = (l: string) => {
    const map: Record<string, string> = { python: '#3572A5', java: '#b07219', cpp: '#f34b7d', javascript: '#f1e05a' };
    return map[l] || '#8b949e';
  };

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="admin-page-header">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Code2 size={22} /> Coding Module
          </h2>
          <p className="admin-muted">Monitor submissions, scores, and coding analytics</p>
        </div>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          <div className="admin-stat-card">
            <div className="admin-stat-icon" style={{ background: 'rgba(31,111,235,0.15)', color: '#1f6feb' }}>
              <FileCode size={20} />
            </div>
            <div className="admin-stat-info">
              <span className="admin-stat-label">Total Submissions</span>
              <span className="admin-stat-value">{analytics.total_submissions}</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon" style={{ background: 'rgba(163,113,247,0.15)', color: '#a371f7' }}>
              <BarChart3 size={20} />
            </div>
            <div className="admin-stat-info">
              <span className="admin-stat-label">Coding Sessions</span>
              <span className="admin-stat-value">{analytics.total_sessions}</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon" style={{ background: 'rgba(63,185,80,0.15)', color: '#3fb950' }}>
              <CheckCircle2 size={20} />
            </div>
            <div className="admin-stat-info">
              <span className="admin-stat-label">Avg Correctness</span>
              <span className="admin-stat-value">{analytics.avg_correctness_score?.toFixed(1)}%</span>
            </div>
          </div>
          <div className="admin-stat-card">
            <div className="admin-stat-icon" style={{ background: 'rgba(210,153,34,0.15)', color: '#d29922' }}>
              <Sparkles size={20} />
            </div>
            <div className="admin-stat-info">
              <span className="admin-stat-label">Avg AI Score</span>
              <span className="admin-stat-value">{analytics.avg_ai_score?.toFixed(1)}/10</span>
            </div>
          </div>
        </div>
      )}

      {/* Language & Status Breakdown */}
      {analytics && (
        <div className="admin-stats-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 16, gap: 16 }}>
          {/* Language Pie */}
          <div className="admin-card">
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700 }}>Language Distribution</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {Object.entries(analytics.language_distribution || {}).map(([lang, count]) => (
                <div key={lang} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: langColor(lang), display: 'inline-block' }} />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{lang}</span>
                  <span className="admin-muted" style={{ fontSize: 12 }}>({count})</span>
                </div>
              ))}
            </div>
          </div>
          {/* Status Breakdown */}
          <div className="admin-card">
            <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700 }}>Status Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {Object.entries(analytics.status_distribution || {}).map(([status, count]) => {
                const total = analytics.total_submissions || 1;
                const pct = ((count as number) / total * 100).toFixed(1);
                return (
                  <div key={status} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, width: 120 }}>{status}</span>
                    <div style={{ flex: 1, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.05)' }}>
                      <div style={{
                        width: `${pct}%`,
                        height: '100%',
                        borderRadius: 3,
                        background: status === 'Accepted' ? '#3fb950' : status === 'Wrong Answer' ? '#f85149' : '#d29922',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                    <span className="admin-muted" style={{ fontSize: 11, width: 40, textAlign: 'right' }}>{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Filters & Search */}
      <div className="admin-card" style={{ marginTop: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 200 }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#8b949e' }} />
              <input
                type="text"
                placeholder="Search by email or challenge…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="admin-input"
                style={{ paddingLeft: 32, width: '100%' }}
              />
            </div>
            <button type="submit" className="admin-btn admin-btn-primary" style={{ padding: '8px 14px' }}>Search</button>
          </form>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Filter size={14} style={{ color: '#8b949e' }} />
            <select
              className="admin-input"
              value={filterLanguage}
              onChange={e => { setFilterLanguage(e.target.value); setPage(1); }}
              style={{ width: 130, padding: '6px 10px', fontSize: 13 }}
            >
              <option value="">All Languages</option>
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
              <option value="javascript">JavaScript</option>
            </select>
            <select
              className="admin-input"
              value={filterStatus}
              onChange={e => { setFilterStatus(e.target.value); setPage(1); }}
              style={{ width: 150, padding: '6px 10px', fontSize: 13 }}
            >
              <option value="">All Statuses</option>
              <option value="Accepted">Accepted</option>
              <option value="Wrong Answer">Wrong Answer</option>
              <option value="Runtime Error">Runtime Error</option>
              <option value="Time Limit Exceeded">TLE</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Loader2 size={24} className="admin-spin" />
          </div>
        ) : submissions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#8b949e' }}>No submissions found.</div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Challenge</th>
                    <th>Language</th>
                    <th>Status</th>
                    <th>Correctness</th>
                    <th>AI Score</th>
                    <th>Runtime</th>
                    <th>Memory</th>
                    <th>Time</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map(sub => (
                    <tr key={sub.id}>
                      <td style={{ fontWeight: 600 }}>{sub.candidate_email}</td>
                      <td>{sub.challenge_title}</td>
                      <td>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 5,
                          background: 'rgba(255,255,255,0.05)', borderRadius: 4, padding: '2px 8px',
                          fontSize: 12, fontWeight: 600,
                        }}>
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: langColor(sub.language) }} />
                          {sub.language}
                        </span>
                      </td>
                      <td><span className={`admin-badge ${statusColor(sub.status)}`}>{sub.status}</span></td>
                      <td>{sub.correctness_score != null ? `${sub.correctness_score}%` : '—'}</td>
                      <td>{sub.ai_score != null ? `${sub.ai_score}/10` : '—'}</td>
                      <td>{sub.runtime_ms != null ? `${sub.runtime_ms}ms` : '—'}</td>
                      <td>{sub.memory_kb != null ? `${(sub.memory_kb / 1024).toFixed(1)}MB` : '—'}</td>
                      <td style={{ fontSize: 12, color: '#8b949e' }}>{new Date(sub.created_at).toLocaleString()}</td>
                      <td>
                        <button
                          className="admin-btn"
                          style={{ padding: '4px 8px', fontSize: 12 }}
                          onClick={() => viewSubmission(sub.id)}
                        >
                          <Eye size={13} /> View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 16 }}>
              <button
                className="admin-btn"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                style={{ padding: '6px 10px' }}
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <span style={{ fontSize: 13, color: '#8b949e' }}>Page {page} of {totalPages}</span>
              <button
                className="admin-btn"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                style={{ padding: '6px 10px' }}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedSubmission && (
        <div className="admin-modal-overlay" onClick={() => setSelectedSubmission(null)}>
          <div className="admin-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 800 }}>
            <div className="admin-modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Code2 size={18} /> Submission #{selectedSubmission.id}
              </h3>
              <button onClick={() => setSelectedSubmission(null)} className="admin-icon-btn"><X size={18} /></button>
            </div>
            <div className="admin-modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              {/* Meta */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 16 }}>
                <div className="admin-stat-card" style={{ padding: 12 }}>
                  <CheckCircle2 size={16} style={{ color: '#3fb950' }} />
                  <div>
                    <span className="admin-muted" style={{ fontSize: 11 }}>Correctness</span>
                    <div style={{ fontWeight: 700 }}>{selectedSubmission.correctness_score ?? '—'}%</div>
                  </div>
                </div>
                <div className="admin-stat-card" style={{ padding: 12 }}>
                  <Sparkles size={16} style={{ color: '#a371f7' }} />
                  <div>
                    <span className="admin-muted" style={{ fontSize: 11 }}>AI Score</span>
                    <div style={{ fontWeight: 700 }}>{selectedSubmission.ai_score ?? '—'}/10</div>
                  </div>
                </div>
                <div className="admin-stat-card" style={{ padding: 12 }}>
                  <Zap size={16} style={{ color: '#1f6feb' }} />
                  <div>
                    <span className="admin-muted" style={{ fontSize: 11 }}>Runtime</span>
                    <div style={{ fontWeight: 700 }}>{selectedSubmission.runtime_ms ?? '—'}ms</div>
                  </div>
                </div>
                <div className="admin-stat-card" style={{ padding: 12 }}>
                  <MemoryStick size={16} style={{ color: '#d29922' }} />
                  <div>
                    <span className="admin-muted" style={{ fontSize: 11 }}>Memory</span>
                    <div style={{ fontWeight: 700 }}>{selectedSubmission.memory_kb ? `${(selectedSubmission.memory_kb / 1024).toFixed(1)}MB` : '—'}</div>
                  </div>
                </div>
              </div>

              {/* Complexity */}
              {(selectedSubmission.time_complexity || selectedSubmission.space_complexity) && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                  {selectedSubmission.time_complexity && (
                    <div className="admin-badge admin-badge-blue" style={{ padding: '4px 10px' }}>
                      <Zap size={12} /> Time: {selectedSubmission.time_complexity}
                    </div>
                  )}
                  {selectedSubmission.space_complexity && (
                    <div className="admin-badge admin-badge-blue" style={{ padding: '4px 10px' }}>
                      <MemoryStick size={12} /> Space: {selectedSubmission.space_complexity}
                    </div>
                  )}
                </div>
              )}

              {/* Code */}
              <div style={{ marginBottom: 16 }}>
                <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: '#8b949e' }}>Submitted Code ({selectedSubmission.language})</h4>
                <pre style={{
                  background: '#1e1e1e',
                  border: '1px solid #30363d',
                  borderRadius: 8,
                  padding: 14,
                  fontSize: 12,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: '#e6edf3',
                  overflow: 'auto',
                  maxHeight: 300,
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.6,
                }}>
                  {selectedSubmission.code}
                </pre>
              </div>

              {/* AI Feedback */}
              {selectedSubmission.ai_feedback && (
                <div style={{
                  background: 'rgba(163,113,247,0.08)',
                  border: '1px solid rgba(163,113,247,0.2)',
                  borderRadius: 8,
                  padding: 14,
                  marginBottom: 16,
                }}>
                  <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: '#a371f7', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Sparkles size={14} /> AI Code Review
                  </h4>
                  <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: '#8b949e' }}>
                    {selectedSubmission.ai_feedback}
                  </p>
                </div>
              )}

              {/* Hidden TC Summary */}
              {selectedSubmission.hidden_total > 0 && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 12px', borderRadius: 6,
                  background: selectedSubmission.hidden_passed === selectedSubmission.hidden_total
                    ? 'rgba(63,185,80,0.1)' : 'rgba(248,81,73,0.1)',
                  border: `1px solid ${selectedSubmission.hidden_passed === selectedSubmission.hidden_total ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`,
                  fontSize: 13, fontWeight: 700,
                  color: selectedSubmission.hidden_passed === selectedSubmission.hidden_total ? '#3fb950' : '#f85149',
                }}>
                  <Trophy size={14} />
                  Hidden Tests: {selectedSubmission.hidden_passed} / {selectedSubmission.hidden_total} passed
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCodingPage;
