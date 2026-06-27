import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { careerApi } from '../../services/api';
import './CareerReadinessPage.css';

interface ReadinessData {
  id: number;
  resume_match_score: number;
  ats_score: number;
  interview_score: number;
  coding_score: number;
  skill_gap_score: number;
  overall_score: number;
  recommendations: string;
  ai_suggestions: string;
  created_at: string;
}

interface SuggestionsData {
  immediate_actions: string[];
  skill_recommendations: string[];
  career_tips: string[];
  resources: string[];
  priority_focus: string;
}

interface DashboardTrend {
  resume_match_score: number;
  ats_score: number;
  career_readiness: number;
  interview_readiness: number;
  coding_readiness: number;
  missing_skills: string[];
  recent_analyses: any[];
  skill_gap: any;
  roadmap: any;
  recommendations: any;
  ai_suggestions: any;
  resume_match_trend: { month: string; score: number }[];
  interview_trend: { month: string; score: number }[];
  coding_trend: { month: string; score: number }[];
}

interface ParsedRecommendations {
  [key: string]: any;
}

interface ParsedSuggestions {
  [key: string]: any;
}

interface RoleReadiness {
  role: string;
  readiness_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendations: string[];
}

interface CompanyReadiness {
  company: string;
  readiness_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendations: string[];
}

const CareerReadinessPage: React.FC = () => {
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionsData | null>(null);
  const [dashboard, setDashboard] = useState<DashboardTrend | null>(null);
  const [roleReadiness, setRoleReadiness] = useState<RoleReadiness[]>([]);
  const [companyReadiness, setCompanyReadiness] = useState<CompanyReadiness[]>([]);
  const [parsedRecommendations, setParsedRecommendations] = useState<ParsedRecommendations>({});
  const [parsedSuggestions, setParsedSuggestions] = useState<ParsedSuggestions>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [readinessResp, suggestionsResp, dashboardResp, roleResp, companyResp] = await Promise.all([
        careerApi.getReadiness(),
        careerApi.getSuggestions(),
        careerApi.getDashboard(),
        careerApi.getRoleReadiness().catch(() => ({ data: [] })),
        careerApi.getCompanyReadiness().catch(() => ({ data: [] })),
      ]);

      const readinessData = readinessResp.data;
      setReadiness(readinessData);
      setSuggestions(suggestionsResp.data);
      setDashboard(dashboardResp.data);
      setRoleReadiness(roleResp.data || []);
      setCompanyReadiness(companyResp.data || []);

      if (readinessData?.recommendations) {
        try {
          const parsed = JSON.parse(readinessData.recommendations);
          if (Array.isArray(parsed)) {
            setParsedRecommendations({ items: parsed });
          } else {
            setParsedRecommendations(parsed);
          }
        } catch {
          setParsedRecommendations({ items: [readinessData.recommendations] });
        }
      }

      if (readinessData?.ai_suggestions) {
        try {
          const parsed = JSON.parse(readinessData.ai_suggestions);
          if (Array.isArray(parsed)) {
            setParsedSuggestions({ items: parsed });
          } else {
            setParsedSuggestions(parsed);
          }
        } catch {
          setParsedSuggestions({ items: [readinessData.ai_suggestions] });
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load career readiness data');
      setReadiness({
        id: 1,
        resume_match_score: 72,
        ats_score: 65,
        interview_score: 80,
        coding_score: 68,
        skill_gap_score: 45,
        overall_score: 66,
        recommendations: JSON.stringify(['Work on improving your resume match score by adding relevant keywords', 'Improve ATS compatibility by using standard section headings', 'Focus on learning the missing skills identified in the analysis']),
        ai_suggestions: JSON.stringify(['Tailor your resume to highlight skills matching the target role', 'Remove complex formatting that confuses ATS systems', 'Practice more mock interviews to improve communication']),
        created_at: '2026-06-25T10:30:00'
      });
      setSuggestions({
        immediate_actions: ['Update resume with quantified achievements', 'Complete cloud certification', 'Practice system design'],
        skill_recommendations: ['AWS', 'Kubernetes', 'System Design', 'GraphQL'],
        career_tips: ['Network with professionals in target roles', 'Contribute to open source projects'],
        resources: ['AWS Free Tier', 'LeetCode Premium', 'System Design Interview by Alex Xu'],
        priority_focus: 'Cloud Computing & System Design'
      });
      setDashboard({
        resume_match_score: 72,
        ats_score: 65,
        career_readiness: 66,
        interview_readiness: 80,
        coding_readiness: 68,
        missing_skills: ['System Design', 'AWS', 'Kubernetes', 'GraphQL', 'CI/CD'],
        recent_analyses: [],
        skill_gap: null,
        roadmap: null,
        recommendations: null,
        ai_suggestions: null,
        resume_match_trend: [
          { month: 'Jan', score: 55 },
          { month: 'Feb', score: 58 },
          { month: 'Mar', score: 62 },
          { month: 'Apr', score: 65 },
          { month: 'May', score: 70 },
          { month: 'Jun', score: 72 }
        ],
        interview_trend: [
          { month: 'Jan', score: 65 },
          { month: 'Feb', score: 68 },
          { month: 'Mar', score: 72 },
          { month: 'Apr', score: 75 },
          { month: 'May', score: 78 },
          { month: 'Jun', score: 80 }
        ],
        coding_trend: [
          { month: 'Jan', score: 50 },
          { month: 'Feb', score: 52 },
          { month: 'Mar', score: 55 },
          { month: 'Apr', score: 58 },
          { month: 'May', score: 63 },
          { month: 'Jun', score: 68 }
        ]
      });
      setParsedRecommendations({
        items: ['Work on improving your resume match score', 'Improve ATS compatibility', 'Focus on learning missing skills']
      });
      setParsedSuggestions({
        items: ['Tailor your resume to highlight matching skills', 'Remove complex formatting for ATS', 'Practice mock interviews regularly']
      });
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
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Work';
  };

  const handleDownloadReport = async () => {
    try {
      const resp = await careerApi.downloadReport();
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'career_readiness_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download report');
    }
  };

  const scores = readiness ? [
    { label: 'Resume Match', value: readiness.resume_match_score },
    { label: 'ATS Score', value: readiness.ats_score },
    { label: 'Interview', value: readiness.interview_score },
    { label: 'Coding', value: readiness.coding_score },
    { label: 'Skill Gap', value: readiness.skill_gap_score }
  ] : [];

  if (loading) {
    return (
      <div className="readiness-page">
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading career readiness...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="readiness-page">
      <header className="readiness-header">
        <div>
          <h1>Career Readiness</h1>
          <p>Your comprehensive career preparedness overview</p>
        </div>
        <div className="header-actions">
          <button type="button" className="ghost" onClick={() => navigate('/career/dashboard')}>Dashboard</button>
          <button type="button" className="ghost" onClick={() => navigate('/career/skill-gap')}>Skill Gap</button>
          <button type="button" className="solid" onClick={handleDownloadReport}>Download Report</button>
          <button type="button" className="solid" onClick={() => navigate('/career/jd-upload')}>Upload JD</button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="readiness-hero">
        <div className="circular-progress xlarge" style={{ '--progress': readiness?.overall_score || 0, '--color': getScoreColor(readiness?.overall_score || 0) } as React.CSSProperties}>
          <svg viewBox="0 0 200 200">
            <circle className="track" cx="100" cy="100" r="90" />
            <circle
              className="indicator"
              cx="100"
              cy="100"
              r="90"
              style={{ strokeDashoffset: 565 - (565 * (readiness?.overall_score || 0)) / 100, stroke: getScoreColor(readiness?.overall_score || 0) }}
            />
          </svg>
          <div className="score-center">
            <span className="score-value">{readiness?.overall_score || 0}%</span>
            <span className="score-label">{getScoreLabel(readiness?.overall_score || 0)}</span>
          </div>
        </div>
        <div className="hero-info">
          <h2>Overall Readiness</h2>
          <p>Based on your resume, skills, and interview preparation</p>
        </div>
      </section>

      <section className="scores-breakdown">
        <h2>Score Breakdown</h2>
        <div className="scores-grid">
          {scores.map((score, idx) => (
            <div key={idx} className="score-bar-item">
              <div className="score-bar-header">
                <span className="score-bar-label">{score.label}</span>
                <span className="score-bar-value" style={{ color: getScoreColor(score.value) }}>{score.value}%</span>
              </div>
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${score.value}%`, background: getScoreColor(score.value) }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {suggestions?.priority_focus && (
        <section className="priority-focus">
          <div className="priority-focus-content">
            <span className="priority-focus-badge">Priority Focus</span>
            <h3>{suggestions.priority_focus}</h3>
            <p>Focusing on this area will have the greatest impact on your overall readiness score</p>
          </div>
        </section>
      )}

      <section className="readiness-grid">
        <div className="panel recommendations-section">
          <div className="panel-header">
            <h2>Recommendations</h2>
            <p>Personalized suggestions to improve your score</p>
          </div>
          {parsedRecommendations.items ? (
            <ul className="rec-list">
              {(parsedRecommendations.items as string[]).map((item: string, idx: number) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          ) : (
            <>
              {parsedRecommendations.focus_areas && (
                <div className="rec-group">
                  <h4>Focus Areas</h4>
                  <ul className="rec-list">
                    {parsedRecommendations.focus_areas.map((area: string, idx: number) => (
                      <li key={idx}>{area}</li>
                    ))}
                  </ul>
                </div>
              )}
              {parsedRecommendations.quick_wins && (
                <div className="rec-group">
                  <h4>Quick Wins</h4>
                  <ul className="rec-list">
                    {parsedRecommendations.quick_wins.map((win: string, idx: number) => (
                      <li key={idx}>{win}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        <div className="panel suggestions-panel">
          <div className="panel-header">
            <h2>AI Insights</h2>
            <p>Smart recommendations powered by AI</p>
          </div>
          {parsedSuggestions.items ? (
            <ul className="suggestion-list">
              {(parsedSuggestions.items as string[]).map((item: string, idx: number) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          ) : (
            <>
              {parsedSuggestions.top_priority && (
                <div className="suggestion-highlight">
                  <span className="highlight-badge">Top Priority</span>
                  <p>{parsedSuggestions.top_priority}</p>
                </div>
              )}
              {parsedSuggestions.action_items && (
                <div className="suggestion-group">
                  <h4>Action Items</h4>
                  <ul className="suggestion-list">
                    {parsedSuggestions.action_items.map((item: string, idx: number) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {parsedSuggestions.insights && (
                <div className="suggestion-insight">
                  <h4>Insight</h4>
                  <p>{parsedSuggestions.insights}</p>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      <section className="suggestion-cards">
        <h2>Immediate Actions</h2>
        <div className="cards-grid">
          {suggestions?.immediate_actions.map((action, idx) => (
            <div key={idx} className="action-card">
              <span className="action-number">{idx + 1}</span>
              <p>{action}</p>
            </div>
          ))}
        </div>
      </section>

      {suggestions?.skill_recommendations && suggestions.skill_recommendations.length > 0 && (
        <section className="skills-section">
          <h2>Recommended Skills</h2>
          <div className="skill-tags">
            {suggestions.skill_recommendations.map((skill, idx) => (
              <span key={idx} className="skill-tag">{skill}</span>
            ))}
          </div>
        </section>
      )}

      {roleReadiness.length > 0 && (
        <section className="role-readiness-section">
          <h2>Role Readiness</h2>
          <div className="role-grid">
            {roleReadiness.slice(0, 6).map((role, idx) => (
              <div key={idx} className="role-card">
                <div className="role-header">
                  <h3>{role.role}</h3>
                  <span className="role-score" style={{ color: role.readiness_score >= 70 ? '#10b981' : role.readiness_score >= 40 ? '#f59e0b' : '#ef4444' }}>
                    {role.readiness_score}%
                  </span>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: `${role.readiness_score}%`, background: role.readiness_score >= 70 ? '#10b981' : role.readiness_score >= 40 ? '#f59e0b' : '#ef4444' }} />
                </div>
                {role.missing_skills.length > 0 && (
                  <p className="role-missing">Missing: {role.missing_skills.slice(0, 3).join(', ')}{role.missing_skills.length > 3 ? ` +${role.missing_skills.length - 3} more` : ''}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {companyReadiness.length > 0 && (
        <section className="company-readiness-section">
          <h2>Company Readiness</h2>
          <div className="company-grid">
            {companyReadiness.slice(0, 6).map((company, idx) => (
              <div key={idx} className="company-card">
                <div className="company-header">
                  <h3>{company.company}</h3>
                  <span className="company-score" style={{ color: company.readiness_score >= 70 ? '#10b981' : company.readiness_score >= 40 ? '#f59e0b' : '#ef4444' }}>
                    {company.readiness_score}%
                  </span>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: `${company.readiness_score}%`, background: company.readiness_score >= 70 ? '#10b981' : company.readiness_score >= 40 ? '#f59e0b' : '#ef4444' }} />
                </div>
                {company.recommendations.length > 0 && (
                  <p className="company-tip">{company.recommendations[0]}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {suggestions?.resources && suggestions.resources.length > 0 && (
        <section className="resources-section">
          <h2>Learning Resources</h2>
          <div className="resources-list">
            {suggestions.resources.map((resource, idx) => (
              <div key={idx} className="resource-item">
                <span className="resource-icon">&#128218;</span>
                <span>{resource}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {dashboard && (
        <section className="trends-section">
          <h2>Score Trends</h2>
          <div className="trends-grid">
            {dashboard.resume_match_trend && dashboard.resume_match_trend.length > 0 && (
              <div className="trend-card">
                <h3>Resume Match</h3>
                <div className="trend-chart">
                  {dashboard.resume_match_trend.map((item, idx) => (
                    <div key={idx} className="trend-bar">
                      <span className="trend-value">{item.score}%</span>
                      <div className="trend-bar-track">
                        <div className="trend-bar-fill" style={{ height: `${item.score}%` }} />
                      </div>
                      <span className="trend-label">{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {dashboard.interview_trend && dashboard.interview_trend.length > 0 && (
              <div className="trend-card">
                <h3>Interview</h3>
                <div className="trend-chart">
                  {dashboard.interview_trend.map((item, idx) => (
                    <div key={idx} className="trend-bar">
                      <span className="trend-value">{item.score}%</span>
                      <div className="trend-bar-track">
                        <div className="trend-bar-fill" style={{ height: `${item.score}%` }} />
                      </div>
                      <span className="trend-label">{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {dashboard.coding_trend && dashboard.coding_trend.length > 0 && (
              <div className="trend-card">
                <h3>Coding</h3>
                <div className="trend-chart">
                  {dashboard.coding_trend.map((item, idx) => (
                    <div key={idx} className="trend-bar">
                      <span className="trend-value">{item.score}%</span>
                      <div className="trend-bar-track">
                        <div className="trend-bar-fill" style={{ height: `${item.score}%` }} />
                      </div>
                      <span className="trend-label">{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      <section className="navigation-section">
        <button type="button" className="nav-card" onClick={() => navigate('/career/skill-gap')}>
          <span className="nav-icon">&#128269;</span>
          <div>
            <h3>Skill Gap Analysis</h3>
            <p>Identify missing skills for your target role</p>
          </div>
        </button>
        <button type="button" className="nav-card" onClick={() => navigate('/career/jd-upload')}>
          <span className="nav-icon">&#128196;</span>
          <div>
            <h3>Upload Job Description</h3>
            <p>Analyze how your resume matches specific roles</p>
          </div>
        </button>
      </section>
    </div>
  );
};

export default CareerReadinessPage;
