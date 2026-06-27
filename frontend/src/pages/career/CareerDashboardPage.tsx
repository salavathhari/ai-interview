import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { careerApi } from '../../services/api';
import './CareerDashboardPage.css';

interface DashboardData {
  resume_match_score: number | null;
  ats_score: number | null;
  career_readiness: number | null;
  interview_readiness: number | null;
  coding_readiness: number | null;
  missing_skills: string[];
  recent_analyses: any[];
  skill_gap: any;
  roadmap: any;
  recommendations: string[];
  ai_suggestions: string[];
  resume_match_trend: { date: string; score: number }[];
  interview_trend: { date: string; score: number }[];
  coding_trend: { date: string; score: number }[];
}

const Icon = {
  Target: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>,
  FileText: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  Briefcase: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>,
  Mic: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>,
  Code: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  TrendingUp: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
  Zap: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  AlertTriangle: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  CheckCircle: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
  BookOpen: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>,
  Sparkles: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L9 12l-7 3 7 3 3 10 3-10 7-3-7-3z"/></svg>,
  ArrowRight: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>,
  Calendar: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>,
  Loader: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cd-spin"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>,
};

const CareerDashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const resp = await careerApi.getDashboard();
      setData(resp.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return 'Strong';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Work';
  };

  const scoreCards = [
    { label: 'Resume Match', score: data?.resume_match_score ?? 0, icon: <Icon.FileText />, color: '#2563eb', bg: '#eff6ff', description: 'How well your resume matches target roles', route: '/career/skill-gap' },
    { label: 'ATS Score', score: data?.ats_score ?? 0, icon: <Icon.Briefcase />, color: '#8b5cf6', bg: '#f5f3ff', description: 'Applicant Tracking System compatibility', route: '/career/ats-report' },
    { label: 'Career Readiness', score: data?.career_readiness ?? 0, icon: <Icon.TrendingUp />, color: '#10b981', bg: '#ecfdf5', description: 'Overall career preparedness', route: '/career/readiness' },
    { label: 'Interview Prep', score: data?.interview_readiness ?? 0, icon: <Icon.Mic />, color: '#f59e0b', bg: '#fffbeb', description: 'Interview skills and preparation', route: '/interview-setup' },
    { label: 'Coding Skills', score: data?.coding_readiness ?? 0, icon: <Icon.Code />, color: '#ef4444', bg: '#fef2f2', description: 'Technical coding skills assessment', route: '/coding' },
    { label: 'Skill Alignment', score: data?.skill_gap?.match_percentage ?? 0, icon: <Icon.Target />, color: '#06b6d4', bg: '#ecfeff', description: 'Skills alignment with job requirements', route: '/career/skill-gap' },
  ];

  if (loading) {
    return (
      <div className="cd-page">
        <div className="cd-loading">
          <Icon.Loader />
          <p>Loading career dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cd-page">
      {/* Header */}
      <header className="cd-header">
        <div className="cd-header-left">
          <div className="cd-header-icon"><Icon.Briefcase /></div>
          <div>
            <h1>Career Dashboard</h1>
            <p>Track your career readiness and identify growth opportunities</p>
          </div>
        </div>
        <div className="cd-header-actions">
          <button type="button" className="cd-btn cd-btn-ghost" onClick={() => navigate('/career/skill-gap')}>
            <Icon.Target /> Skill Gap
          </button>
          <button type="button" className="cd-btn cd-btn-primary" onClick={() => navigate('/career/jd-upload')}>
            <Icon.Zap /> Upload JD
          </button>
        </div>
      </header>

      {error && (
        <div className="cd-error">
          <Icon.AlertTriangle />
          <span>{error}</span>
        </div>
      )}

      {/* Quick Actions */}
      <section className="cd-quick-actions">
        <button type="button" className="cd-action-card" onClick={() => navigate('/career/jd-upload')}>
          <div className="cd-action-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Icon.FileText /></div>
          <div className="cd-action-text">
            <h3>Upload JD</h3>
            <p>Add a job description</p>
          </div>
          <Icon.ArrowRight />
        </button>
        <button type="button" className="cd-action-card" onClick={() => navigate('/career/ats-report')}>
          <div className="cd-action-icon" style={{ background: '#f5f3ff', color: '#8b5cf6' }}><Icon.Briefcase /></div>
          <div className="cd-action-text">
            <h3>ATS Check</h3>
            <p>Scan resume compatibility</p>
          </div>
          <Icon.ArrowRight />
        </button>
        <button type="button" className="cd-action-card" onClick={() => navigate('/career/resume-optimizer')}>
          <div className="cd-action-icon" style={{ background: '#ecfdf5', color: '#10b981' }}><Icon.Sparkles /></div>
          <div className="cd-action-text">
            <h3>Optimize</h3>
            <p>Enhance your resume</p>
          </div>
          <Icon.ArrowRight />
        </button>
        <button type="button" className="cd-action-card" onClick={() => navigate('/career/learning-roadmap')}>
          <div className="cd-action-icon" style={{ background: '#fffbeb', color: '#f59e0b' }}><Icon.BookOpen /></div>
          <div className="cd-action-text">
            <h3>Learn</h3>
            <p>View learning roadmap</p>
          </div>
          <Icon.ArrowRight />
        </button>
      </section>

      {/* Score Cards */}
      <section className="cd-scores">
        {scoreCards.map((card, idx) => (
          <article key={idx} className="cd-score-card" onClick={() => navigate(card.route)}>
            <div className="cd-score-accent" style={{ background: card.color }} />
            <div className="cd-score-top">
              <div className="cd-score-icon" style={{ background: card.bg, color: card.color }}>
                {card.icon}
              </div>
              <div className="cd-score-info">
                <span className="cd-score-label">{card.label}</span>
                <span className="cd-score-desc">{card.description}</span>
              </div>
            </div>
            <div className="cd-score-bottom">
              <div className="cd-progress-ring" style={{ '--progress': card.score, '--color': card.color } as React.CSSProperties}>
                <svg viewBox="0 0 100 100">
                  <circle className="cd-ring-track" cx="50" cy="50" r="40" />
                  <circle
                    className="cd-ring-fill"
                    cx="50" cy="50" r="40"
                    style={{ strokeDashoffset: 251.2 - (251.2 * card.score) / 100, stroke: card.color }}
                  />
                </svg>
                <div className="cd-ring-center">
                  <span className="cd-ring-value" style={{ color: card.color }}>{Math.round(card.score)}<small>%</small></span>
                  <span className="cd-ring-label">{getScoreLabel(card.score)}</span>
                </div>
              </div>
            </div>
          </article>
        ))}
      </section>

      {/* Main Grid */}
      <div className="cd-section-divider"><h2>Insights</h2></div>
      <section className="cd-grid">
        {/* Missing Skills */}
        <div className="cd-panel">
          <div className="cd-panel-header">
            <div className="cd-panel-icon" style={{ background: '#fef2f2', color: '#ef4444' }}><Icon.AlertTriangle /></div>
            <div>
              <h2>Missing Skills</h2>
              <p>Skills to develop for better job match</p>
            </div>
          </div>
          <div className="cd-skill-tags">
            {data?.missing_skills && data.missing_skills.length > 0 ? (
              data.missing_skills.slice(0, 12).map((skill, idx) => (
                <span key={idx} className="cd-skill-tag">{skill}</span>
              ))
            ) : (
              <div className="cd-empty">
                <Icon.CheckCircle />
                <p>No skill gaps detected. Run an analysis to see recommendations.</p>
              </div>
            )}
          </div>
          {data?.missing_skills && data.missing_skills.length > 12 && (
            <button type="button" className="cd-link-btn" onClick={() => navigate('/career/skill-gap')}>
              View all {data.missing_skills.length} skills <Icon.ArrowRight />
            </button>
          )}
        </div>

        {/* Recent Analyses */}
        <div className="cd-panel">
          <div className="cd-panel-header">
            <div className="cd-panel-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Icon.Calendar /></div>
            <div>
              <h2>Recent Analyses</h2>
              <p>Your latest resume analyses</p>
            </div>
          </div>
          {data?.recent_analyses && data.recent_analyses.length > 0 ? (
            <ul className="cd-analysis-list">
              {data.recent_analyses.slice(0, 5).map((item) => (
                <li key={item.id} onClick={() => navigate('/career/skill-gap')}>
                  <div className="cd-analysis-left">
                    <div className="cd-analysis-dot" style={{ background: getScoreColor(item.resume_match_score ?? item.ats_score ?? 0) }} />
                    <div>
                      <strong>Analysis #{item.id}</strong>
                      <span>{new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                    </div>
                  </div>
                  <div className="cd-analysis-right">
                    <span className="cd-analysis-score" style={{ color: getScoreColor(item.resume_match_score ?? item.ats_score ?? 0) }}>
                      {item.resume_match_score ?? item.ats_score ?? 0}%
                    </span>
                    <Icon.ArrowRight />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="cd-empty">
              <Icon.FileText />
              <p>No analyses yet. Upload a resume and JD to get started.</p>
            </div>
          )}
        </div>

        {/* AI Suggestions */}
        <div className="cd-panel">
          <div className="cd-panel-header">
            <div className="cd-panel-icon" style={{ background: '#f5f3ff', color: '#8b5cf6' }}><Icon.Sparkles /></div>
            <div>
              <h2>AI Suggestions</h2>
              <p>Personalized recommendations</p>
            </div>
          </div>
          {data?.ai_suggestions && data.ai_suggestions.length > 0 ? (
            <ul className="cd-suggestion-list">
              {data.ai_suggestions.slice(0, 5).map((text, idx) => (
                <li key={idx}>
                  <div className={`cd-priority-dot ${idx < 2 ? 'high' : idx < 4 ? 'medium' : 'low'}`} />
                  <p>{text}</p>
                </li>
              ))}
            </ul>
          ) : (
            <div className="cd-empty">
              <Icon.Sparkles />
              <p>No suggestions yet. Complete an analysis to get AI recommendations.</p>
            </div>
          )}
        </div>

        {/* Learning Roadmap */}
        <div className="cd-panel">
          <div className="cd-panel-header">
            <div className="cd-panel-icon" style={{ background: '#ecfdf5', color: '#10b981' }}><Icon.BookOpen /></div>
            <div>
              <h2>Learning Roadmap</h2>
              <p>Your personalized learning path</p>
            </div>
          </div>
          {data?.roadmap ? (
            <div className="cd-roadmap">
              <div className="cd-roadmap-stats">
                <div className="cd-roadmap-stat">
                  <div className="cd-roadmap-stat-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Icon.BookOpen /></div>
                  <div>
                    <strong>{data.roadmap.total_hours ?? 0}h</strong>
                    <span>Total Hours</span>
                  </div>
                </div>
                <div className="cd-roadmap-stat">
                  <div className="cd-roadmap-stat-icon" style={{ background: '#ecfdf5', color: '#10b981' }}><Icon.Calendar /></div>
                  <div>
                    <strong>{data.roadmap.estimated_weeks ?? 0}</strong>
                    <span>Weeks</span>
                  </div>
                </div>
              </div>
              <button type="button" className="cd-btn cd-btn-primary cd-btn-full" onClick={() => navigate('/career/learning-roadmap')}>
                <Icon.BookOpen /> View Full Roadmap
              </button>
            </div>
          ) : (
            <div className="cd-empty">
              <Icon.BookOpen />
              <p>No roadmap yet. Complete a skill gap analysis to generate one.</p>
              <button type="button" className="cd-btn cd-btn-primary" onClick={() => navigate('/career/skill-gap')} style={{ marginTop: 8 }}>
                <Icon.Target /> Start Analysis
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Trends */}
      {(data?.resume_match_trend?.length || data?.interview_trend?.length || data?.coding_trend?.length) ? (
        <>
          <div className="cd-section-divider"><h2>Score Trends</h2></div>
          <section className="cd-trends">
            {data?.resume_match_trend && data.resume_match_trend.length > 0 && (
              <div className="cd-trend-card">
                <div className="cd-trend-header">
                  <div className="cd-trend-dot" style={{ background: '#2563eb' }} />
                  <h3>Resume Match</h3>
                </div>
                <div className="cd-trend-bars">
                  {data.resume_match_trend.slice(-6).map((t, idx) => (
                    <div className="cd-trend-row" key={idx}>
                      <span className="cd-trend-label">{new Date(t.date).toLocaleDateString('en-US', { month: 'short' })}</span>
                      <div className="cd-trend-track">
                        <div className="cd-trend-fill" style={{ width: `${t.score}%`, background: 'linear-gradient(90deg, #2563eb, #3b82f6)' }} />
                      </div>
                      <span className="cd-trend-value">{Math.round(t.score)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {data?.interview_trend && data.interview_trend.length > 0 && (
              <div className="cd-trend-card">
                <div className="cd-trend-header">
                  <div className="cd-trend-dot" style={{ background: '#10b981' }} />
                  <h3>Interview</h3>
                </div>
                <div className="cd-trend-bars">
                  {data.interview_trend.slice(-6).map((t, idx) => (
                    <div className="cd-trend-row" key={idx}>
                      <span className="cd-trend-label">{new Date(t.date).toLocaleDateString('en-US', { month: 'short' })}</span>
                      <div className="cd-trend-track">
                        <div className="cd-trend-fill" style={{ width: `${t.score}%`, background: 'linear-gradient(90deg, #10b981, #34d399)' }} />
                      </div>
                      <span className="cd-trend-value">{Math.round(t.score)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {data?.coding_trend && data.coding_trend.length > 0 && (
              <div className="cd-trend-card">
                <div className="cd-trend-header">
                  <div className="cd-trend-dot" style={{ background: '#f59e0b' }} />
                  <h3>Coding</h3>
                </div>
                <div className="cd-trend-bars">
                  {data.coding_trend.slice(-6).map((t, idx) => (
                    <div className="cd-trend-row" key={idx}>
                      <span className="cd-trend-label">{new Date(t.date).toLocaleDateString('en-US', { month: 'short' })}</span>
                      <div className="cd-trend-track">
                        <div className="cd-trend-fill" style={{ width: `${t.score}%`, background: 'linear-gradient(90deg, #f59e0b, #fbbf24)' }} />
                      </div>
                      <span className="cd-trend-value">{Math.round(t.score)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </>
      ) : null}

      {/* Recommendations */}
      {data?.recommendations && data.recommendations.length > 0 && (
        <>
          <div className="cd-section-divider"><h2>Recommendations</h2></div>
          <section className="cd-panel cd-recs-panel">
            <div className="cd-recs-list">
              {data.recommendations.map((rec, idx) => (
                <div key={idx} className="cd-rec-item">
                  <div className="cd-rec-num">{idx + 1}</div>
                  <p>{rec}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default CareerDashboardPage;
