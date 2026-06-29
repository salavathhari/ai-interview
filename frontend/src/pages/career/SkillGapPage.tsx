import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  Search,
  CheckCircle,
  XCircle,
  Loader2,
  AlertTriangle,
  Clock,
  ArrowLeft,
  FileText,
  ClipboardCheck,
  Map,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react';
import { careerApi, resumeApi } from '../../services/api';
import './SkillGapPage.css';

interface ResumeAnalysis {
  id: number;
  resume_id: number;
  summary: string;
  detected_skills: string;
  experience_level: string;
  ats_score: number | null;
  resume_match_score: number | null;
  created_at: string;
}

interface Resume {
  id: number;
  filename: string;
  created_at: string;
}

interface JobDescription {
  id: number;
  title: string;
  company: string;
}

interface SkillGapResult {
  id: number;
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  additional_skills: string[];
  priority_skills: string[];
  resume_analysis_id: number;
  job_description_id: number;
  created_at: string;
  total_estimated_hours?: number;
}

const SkillGapPage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [analyses, setAnalyses] = useState<ResumeAnalysis[]>([]);
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [selectedResume, setSelectedResume] = useState<number | null>(null);
  const [selectedJd, setSelectedJd] = useState<number | null>(null);
  const [result, setResult] = useState<SkillGapResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisPage, setAnalysisPage] = useState(1);
  const [analysisTotal, setAnalysisTotal] = useState(0);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadOptions();
  }, []);

  const loadOptions = async () => {
    try {
      setFetchingData(true);
      const [resumeResp, analysesResp, jdResp] = await Promise.all([
        resumeApi.getMyResumes(),
        careerApi.getSkillGapAnalyses(analysisPage, 20),
        careerApi.getJobDescriptions(),
      ]);
      setResumes(resumeResp.data);
      const items = analysesResp.data.items || analysesResp.data;
      setAnalyses(items);
      setAnalysisTotal(analysesResp.data.total || items.length);
      setJds(jdResp.data.items || jdResp.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setFetchingData(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedResume) return;
    try {
      setLoading(true);
      setAnalysisComplete(false);
      setError(null);
      const resp = await careerApi.analyzeCareer(selectedResume, selectedJd || undefined);
      setResult(resp.data.skill_gap || null);
      setAnalysisComplete(true);
      setTimeout(() => setAnalysisComplete(false), 2500);
      loadOptions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const parseJSON = (val: any): string[] => {
    if (!val) return [];
    if (typeof val === 'string') {
      try { return JSON.parse(val); } catch { return []; }
    }
    return Array.isArray(val) ? val : [];
  };

  const parsedMatched = result ? parseJSON(result.matched_skills) : [];
  const parsedMissing = result ? parseJSON(result.missing_skills) : [];
  const parsedAdditional = result ? parseJSON(result.additional_skills) : [];
  const parsedPriority = result ? parseJSON(result.priority_skills) : [];

  if (fetchingData) {
    return (
      <div className="sg-page">
        <div className="sg-loading">
          <Loader2 size={40} className="sg-spin" />
          <p>Loading analysis data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="sg-page">
      <header className="sg-header">
        <div className="sg-header-left">
          <div className="sg-header-icon"><Zap size={24} /></div>
          <div>
            <p className="sg-eyebrow">Career Intelligence</p>
            <h1>Skill Gap Analysis</h1>
            <p>Compare your resume against job requirements</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="button" className="sg-btn sg-btn-ghost" onClick={() => navigate('/career/dashboard')}>
            <ArrowLeft size={15} /> Dashboard
          </button>
          {result?.id && (
            <button type="button" className="sg-btn sg-btn-primary" onClick={() => navigate(`/career/learning-roadmap?gap=${result.id}`)}>
              <Map size={15} /> Generate Learning Roadmap
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="sg-error">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      <section className="sg-config">
        <div className="sg-config-card">
          <div className="sg-config-left">
            <div className="sg-config-icon"><Search size={20} /></div>
            <div>
              <h3>Configure Analysis</h3>
              <p>Select a resume and optional job description to compare</p>
            </div>
          </div>
          <div className="sg-config-right">
            <label className="sg-field">
              <span>Resume *</span>
              <select
                value={selectedResume || ''}
                onChange={(e) => setSelectedResume(Number(e.target.value) || null)}
              >
                <option value="">Select a resume</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>{r.filename} — {new Date(r.created_at).toLocaleDateString()}</option>
                ))}
              </select>
            </label>
            <label className="sg-field">
              <span>Job Description (optional)</span>
              <select
                value={selectedJd || ''}
                onChange={(e) => setSelectedJd(Number(e.target.value) || null)}
              >
                <option value="">No JD (general analysis)</option>
                {jds.map((jd) => (
                  <option key={jd.id} value={jd.id}>{jd.title}{jd.company ? ` — ${jd.company}` : ''}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className={`sg-btn sg-btn-primary ${loading ? 'btn--analyzing btn--pulse' : ''} ${analysisComplete ? 'btn--success' : ''}`}
              onClick={handleAnalyze}
              disabled={!selectedResume || loading}
            >
              {loading ? (
                <><Loader2 size={15} className="btn-spinner" /> Analyzing...</>
              ) : analysisComplete ? (
                <><CheckCircle2 size={15} /> Analysis Complete</>
              ) : (
                <><Zap size={15} /> Analyze Skills</>
              )}
            </button>
          </div>
        </div>
      </section>

      {!result && analyses.length > 0 && (
        <section className="sg-section">
          <div className="sg-card">
            <div className="sg-card-header">
              <div>
                <h2>Previous Analyses</h2>
                <p>{analysisTotal} analyses completed</p>
              </div>
              {analysisTotal > 20 && (
                <div className="sg-pagination">
                  <button
                    type="button"
                    disabled={analysisPage <= 1}
                    onClick={() => { setAnalysisPage(p => p - 1); loadOptions(); }}
                  >
                    Prev
                  </button>
                  <span>Page {analysisPage}</span>
                  <button
                    type="button"
                    disabled={analysisPage * 20 >= analysisTotal}
                    onClick={() => { setAnalysisPage(p => p + 1); loadOptions(); }}
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
            <ul className="sg-analysis-list">
              {analyses.map((a: any) => (
                <li key={a.id}>
                  <div className="sg-analysis-info">
                    <strong>Analysis #{a.id}</strong>
                    <span>{new Date(a.created_at).toLocaleDateString()}</span>
                    {a.match_percentage != null && (
                      <span className="sg-score-badge">Match: {Math.round(a.match_percentage)}%</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {result && (
        <>
          <section className="sg-section">
            <div className="sg-match-card">
              <div className="sg-ring">
                <svg viewBox="0 0 160 160">
                  <circle className="sg-ring-track" cx="80" cy="80" r="68" />
                  <circle
                    className="sg-ring-fill"
                    cx="80" cy="80" r="68"
                    style={{
                      strokeDashoffset: 427 - (427 * result.match_percentage) / 100,
                      stroke: getScoreColor(result.match_percentage)
                    }}
                  />
                </svg>
                <span className="sg-ring-value">{result.match_percentage}%</span>
              </div>
              <h3>Match Score</h3>
              <p>Skills alignment with target role</p>
              {result.total_estimated_hours != null && result.total_estimated_hours > 0 && (
                <p className="sg-estimated-hours">
                  <Clock size={14} />
                  Est. {Math.round(result.total_estimated_hours)}h to close gaps
                </p>
              )}
            </div>
          </section>

          <section className="sg-results">
            <div className="sg-card">
              <div className="sg-card-header">
                <div>
                  <h2>Matched Skills</h2>
                  <p>{parsedMatched.length} skills found</p>
                </div>
              </div>
              <ul className="sg-skill-list sg-skill-list--matched">
                {parsedMatched.map((skill: string, idx: number) => (
                  <li key={idx}>
                    <span className="sg-check"><CheckCircle size={14} /></span>
                    <span>{skill}</span>
                  </li>
                ))}
                {parsedMatched.length === 0 && <li className="sg-empty">No matched skills found.</li>}
              </ul>
            </div>

            <div className="sg-card">
              <div className="sg-card-header">
                <div>
                  <h2>Missing Skills</h2>
                  <p>{parsedMissing.length} skills needed</p>
                </div>
              </div>
              <ul className="sg-skill-list sg-skill-list--missing">
                {parsedMissing.map((skill: string, idx: number) => (
                  <li key={idx}>
                    <span className="sg-x"><XCircle size={14} /></span>
                    <span>{skill}</span>
                  </li>
                ))}
                {parsedMissing.length === 0 && <li className="sg-empty">No missing skills — great match!</li>}
              </ul>
            </div>

            <div className="sg-card">
              <div className="sg-card-header">
                <div>
                  <h2>Additional Skills</h2>
                  <p>{parsedAdditional.length} extra skills</p>
                </div>
              </div>
              <div className="sg-tags">
                {parsedAdditional.map((skill: string, idx: number) => (
                  <span key={idx} className="sg-tag sg-tag--additional">{skill}</span>
                ))}
                {parsedAdditional.length === 0 && <p className="sg-empty-text">No additional skills detected.</p>}
              </div>
            </div>

            <div className="sg-card">
              <div className="sg-card-header">
                <div>
                  <h2>Priority Skills</h2>
                  <p>{parsedPriority.length} to focus on</p>
                </div>
              </div>
              <div className="sg-tags">
                {parsedPriority.map((skill: string, idx: number) => (
                  <span key={idx} className="sg-tag sg-tag--priority">{skill}</span>
                ))}
                {parsedPriority.length === 0 && <p className="sg-empty-text">No priority skills identified.</p>}
              </div>
            </div>
          </section>

          <section className="sg-actions">
            <div className="sg-action-card">
              <div className="sg-action-icon" style={{ background: '#eff6ff', color: '#2563eb' }}>
                <FileText size={24} />
              </div>
              <h3>Optimize Resume</h3>
              <p>Improve ATS compatibility and keyword matching</p>
              <button type="button" className="sg-btn sg-btn-ghost" onClick={() => navigate('/career/resume-optimizer')}>
                Resume Optimizer <ChevronRight size={14} />
              </button>
            </div>
            <div className="sg-action-card">
              <div className="sg-action-icon" style={{ background: '#f0fdf4', color: '#16a34a' }}>
                <ClipboardCheck size={24} />
              </div>
              <h3>ATS Report</h3>
              <p>Check your resume's ATS compatibility score</p>
              <button type="button" className="sg-btn sg-btn-ghost" onClick={() => navigate('/career/ats-report')}>
                View Report <ChevronRight size={14} />
              </button>
            </div>
          </section>

          <section className="sg-cta">
            <div className="sg-cta-card">
              <div className="sg-cta-icon">
                <Map size={28} />
              </div>
              <div className="sg-cta-text">
                <h3>Ready to close your skill gaps?</h3>
                <p>Generate a personalized learning roadmap based on your missing and priority skills.</p>
              </div>
              <button type="button" className="sg-btn sg-btn-primary" onClick={() => navigate(`/career/learning-roadmap?gap=${result?.id}`)}>
                <Map size={15} /> Generate Roadmap
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default SkillGapPage;
