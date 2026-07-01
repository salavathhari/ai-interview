import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Zap,
  Briefcase,
  Rocket,
  GraduationCap,
  Ruler,
  BookOpen,
  Key,
  Loader2,
  Download,
  Sparkles,
  FileDown,
  CheckCircle2,
  File,
  CheckCircle,
  X,
} from 'lucide-react';
import { careerApi, resumeApi } from '../../services/api';
import './ATSReportPage.css';

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

interface ATSReport {
  id: number;
  overall_score: number;
  keyword_score: number;
  skills_score: number;
  experience_score: number;
  projects_score: number;
  education_score: number;
  formatting_score: number;
  readability_score: number;
  resume_parsed: any;
  jd_parsed: any;
  keyword_analysis: any;
  formatting_analysis: any;
  experience_analysis: any;
  projects_analysis: any;
  education_analysis: any;
  readability_analysis: any;
  matched_skills: any;
  missing_skills: any;
  additional_skills: any;
  recommendations: any;
  created_at: string;
}

interface OptimizedResume {
  id: number;
  optimized_text: string;
  improvements: string;
  professional_summary: string;
  optimized_skills: string;
  optimized_keywords: string;
  format: string;
  created_at: string;
}

const ATSReportPage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [selectedResume, setSelectedResume] = useState<number | null>(null);
  const [selectedJd, setSelectedJd] = useState<number | null>(null);
  const [report, setReport] = useState<ATSReport | null>(null);
  const [history, setHistory] = useState<ATSReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [optimizing, setOptimizing] = useState(false);
  const [optimized, setOptimized] = useState<OptimizedResume | null>(null);
  const [showOptimized, setShowOptimized] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      setFetchingData(true);
      const [resumeResp, jdResp, histResp] = await Promise.all([
        resumeApi.getMyResumes(),
        careerApi.getJobDescriptions(),
        careerApi.getATSHistory().catch(() => ({ data: [] })),
      ]);
      setResumes(resumeResp.data);
      setJds(jdResp.data.items || jdResp.data);
      setHistory(histResp.data);
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
      setOptimized(null);
      setShowOptimized(false);
      const resp = await careerApi.analyzeATS(selectedResume, selectedJd || undefined);
      setReport(resp.data);
      setAnalysisComplete(true);
      setTimeout(() => setAnalysisComplete(false), 2500);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!selectedResume) return;
    try {
      setOptimizing(true);
      setError(null);
      const resp = await careerApi.optimizeATS(selectedResume, selectedJd || undefined);
      setOptimized(resp.data);
      setShowOptimized(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const handleOptimizeDocx = async () => {
    if (!selectedResume) return;
    try {
      setOptimizing(true);
      setError(null);
      const resp = await careerApi.optimizeATSDocx(selectedResume, selectedJd || undefined);
      // Response is JSON with optimize_id, download the DOCX
      const optimizeId = resp.data.optimize_id;
      const docxResp = await careerApi.downloadOptimizedDocx(optimizeId);
      const blob = new Blob([docxResp.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `optimized_resume_${optimizeId}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      // Also show the optimized text in the UI
      setOptimized({
        id: optimizeId,
        optimized_text: resp.data.optimized_text,
        improvements: JSON.stringify(resp.data.improvements),
        professional_summary: '',
        optimized_skills: '',
        optimized_keywords: '',
        format: 'docx',
        created_at: new Date().toISOString(),
      });
      setShowOptimized(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'DOCX optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const handleOptimizePdf = async () => {
    if (!selectedResume) return;
    try {
      setOptimizing(true);
      setError(null);
      const resp = await careerApi.optimizeATSPdf(selectedResume, selectedJd || undefined);
      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'optimized_resume.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'PDF optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!report) return;
    try {
      const resp = await careerApi.downloadATSReport(report.id);
      const blob = new Blob([resp.data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ats_report_${report.id}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download report');
    }
  };

  const handleDownloadOptimized = async () => {
    if (!optimized) return;
    try {
      const resp = await careerApi.downloadOptimizedResume(optimized.id);
      const blob = new Blob([resp.data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `optimized_resume_${optimized.id}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download optimized resume');
    }
  };

  const handleDownloadOptimizedDocx = async () => {
    if (!optimized) return;
    try {
      const resp = await careerApi.downloadOptimizedDocx(optimized.id);
      const blob = new Blob([resp.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `optimized_resume_${optimized.id}.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download DOCX');
    }
  };

  const handleDownloadOptimizedPdf = async () => {
    if (!optimized) return;
    try {
      const resp = await careerApi.downloadOptimizedPdf(optimized.id);
      const blob = new Blob([resp.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `optimized_resume_${optimized.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download PDF');
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

  const parseJSON = (val: any): any => {
    if (!val) return null;
    if (typeof val === 'string') {
      try { return JSON.parse(val); } catch { return null; }
    }
    return val;
  };

  const parsedRecommendations = parseJSON(report?.recommendations) || [];
  const parsedKeywordAnalysis = parseJSON(report?.keyword_analysis);
  const parsedFormatting = parseJSON(report?.formatting_analysis);
  const parsedExperience = parseJSON(report?.experience_analysis);
  const parsedProjects = parseJSON(report?.projects_analysis);
  const parsedResumeParsed = parseJSON(report?.resume_parsed);
  const parsedMatchedSkills = parseJSON(report?.matched_skills) || [];
  const parsedMissingSkills = parseJSON(report?.missing_skills) || [];
  const parsedAdditionalSkills = parseJSON(report?.additional_skills) || [];

  const breakdownItems = report ? [
    { label: 'Keyword Match', score: report.keyword_score, weight: '35%', icon: <Key size={20} /> },
    { label: 'Skills Match', score: report.skills_score, weight: '20%', icon: <Zap size={20} /> },
    { label: 'Experience', score: report.experience_score, weight: '15%', icon: <Briefcase size={20} /> },
    { label: 'Projects', score: report.projects_score, weight: '10%', icon: <Rocket size={20} /> },
    { label: 'Education', score: report.education_score, weight: '5%', icon: <GraduationCap size={20} /> },
    { label: 'Formatting', score: report.formatting_score, weight: '10%', icon: <Ruler size={20} /> },
    { label: 'Readability', score: report.readability_score, weight: '5%', icon: <BookOpen size={20} /> },
  ] : [];

  if (fetchingData) {
    return (
      <div className="ats-report-page">
        <div className="loading-state"><div className="spinner" /><p>Loading ATS data...</p></div>
      </div>
    );
  }

  return (
    <div className="ats-report-page">
      <header className="career-header">
        <div>
          <p className="cd-eyebrow">ATS Analysis</p>
          <h1>ATS Resume Analysis</h1>
          <p>Comprehensive Applicant Tracking System compatibility analysis</p>
        </div>
        <div className="header-actions">
          <button type="button" className="ghost" onClick={() => navigate('/career/dashboard')}><ArrowLeft size={15} /> Dashboard</button>
          <button type="button" className="solid" onClick={() => navigate('/career/resume-optimizer')}>Resume Optimizer</button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="analysis-controls">
        <div className="panel">
          <div className="panel-header">
            <h2>Run ATS Analysis</h2>
            <p>Select a resume and optionally a job description to compare against</p>
          </div>
          <div className="controls-form">
            <label className="input-field">
              <span>Resume *</span>
              <select value={selectedResume || ''} onChange={(e) => setSelectedResume(Number(e.target.value) || null)}>
                <option value="">Select a resume</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>{r.filename} - {new Date(r.created_at).toLocaleDateString()}</option>
                ))}
              </select>
            </label>
            <label className="input-field">
              <span>Job Description (optional)</span>
              <select value={selectedJd || ''} onChange={(e) => setSelectedJd(Number(e.target.value) || null)}>
                <option value="">No JD (general ATS check)</option>
                {jds.map((jd) => (
                  <option key={jd.id} value={jd.id}>{jd.title}{jd.company ? ` - ${jd.company}` : ''}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className={`solid ${loading ? 'btn--analyzing btn--pulse' : ''} ${analysisComplete ? 'btn--success' : ''}`}
              onClick={handleAnalyze}
              disabled={!selectedResume || loading}
            >
              {loading ? (
                <><Loader2 size={15} className="btn-spinner" /> Analyzing...</>
              ) : analysisComplete ? (
                <><CheckCircle2 size={15} /> Analysis Complete</>
              ) : (
                'Analyze Resume'
              )}
            </button>
          </div>
        </div>
      </section>

      {report && (
        <>
          <section className="ats-score-hero">
            <div className="score-hero-card">
              <div className="circular-progress xlarge" style={{ '--progress': report.overall_score, '--color': getScoreColor(report.overall_score) } as React.CSSProperties}>
                <svg viewBox="0 0 200 200">
                  <circle className="track" cx="100" cy="100" r="90" />
                  <circle className="indicator" cx="100" cy="100" r="90"
                    style={{ strokeDashoffset: 565 - (565 * report.overall_score) / 100, stroke: getScoreColor(report.overall_score) }} />
                </svg>
                <div className="score-center">
                  <span className="score-value">{report.overall_score}</span>
                  <span className="score-label">{getScoreLabel(report.overall_score)}</span>
                </div>
              </div>
              <h2>ATS Score</h2>
              <p>Overall applicant tracking system compatibility</p>
              <div className="hero-actions">
                <button type="button" className="solid" onClick={handleOptimize} disabled={optimizing}>
                  {optimizing ? <><Loader2 size={15} className="cd-spin" /> Optimizing...</> : <><Sparkles size={15} /> Quick Optimize</>}
                </button>
                <button type="button" className="solid" onClick={handleOptimizeDocx} disabled={optimizing} style={{ background: '#6366f1' }}>
                  {optimizing ? <><Loader2 size={15} className="cd-spin" /> Generating...</> : <><FileDown size={15} /> Optimize as DOCX</>}
                </button>
                <button type="button" className="solid" onClick={handleOptimizePdf} disabled={optimizing} style={{ background: '#8b5cf6' }}>
                  {optimizing ? <><Loader2 size={15} className="cd-spin" /> Generating...</> : <><File size={15} /> Optimize as PDF</>}
                </button>
                <button type="button" className="ghost" onClick={handleDownloadReport}>
                  <Download size={15} /> Download Report
                </button>
              </div>
            </div>
          </section>

          <nav className="ats-tabs">
            {['overview', 'keywords', 'formatting', 'experience', 'projects', 'skills', 'recommendations'].map(tab => (
              <button key={tab} type="button" className={`tab ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}>
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>

          {activeTab === 'overview' && (
            <section className="ats-overview">
              <div className="breakdown-grid">
                {breakdownItems.map((item, idx) => (
                  <div key={idx} className="breakdown-card">
                    <div className="breakdown-header">
                      <span className="breakdown-icon" style={{ color: getScoreColor(item.score) }}>{item.icon}</span>
                      <div>
                        <h3>{item.label}</h3>
                        <span className="breakdown-weight">Weight: {item.weight}</span>
                      </div>
                      <span className="breakdown-score" style={{ color: getScoreColor(item.score) }}>{item.score.toFixed(1)}</span>
                    </div>
                    <div className="progress-bar-track">
                      <div className="progress-bar-fill" style={{ width: `${item.score}%`, background: getScoreColor(item.score) }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="overview-stats">
                {parsedResumeParsed && (
                  <div className="panel">
                    <div className="panel-header"><h2>Resume Summary</h2></div>
                    <div className="stat-grid">
                      <div className="stat-item"><span className="stat-value">{parsedResumeParsed.skill_count || 0}</span><span className="stat-label">Skills Found</span></div>
                      <div className="stat-item"><span className="stat-value">{parsedResumeParsed.project_count || 0}</span><span className="stat-label">Projects</span></div>
                      <div className="stat-item"><span className="stat-value">{parsedResumeParsed.experience_level || 'N/A'}</span><span className="stat-label">Level</span></div>
                      <div className="stat-item"><span className="stat-value">{parsedResumeParsed.education_count || 0}</span><span className="stat-label">Education Items</span></div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'keywords' && parsedKeywordAnalysis && (
            <section className="ats-keywords">
              <div className="keyword-stats panel">
                <div className="panel-header"><h2>Keyword Analysis</h2></div>
                <div className="stat-grid">
                  <div className="stat-item"><span className="stat-value" style={{ color: '#10b981' }}>{parsedKeywordAnalysis.matched_count || 0}</span><span className="stat-label">Matched</span></div>
                  <div className="stat-item"><span className="stat-value" style={{ color: '#ef4444' }}>{parsedKeywordAnalysis.missing_count || 0}</span><span className="stat-label">Missing</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedKeywordAnalysis.keyword_density || 0}%</span><span className="stat-label">Keyword Density</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedKeywordAnalysis.total_jd_keywords || 0}</span><span className="stat-label">Total JD Keywords</span></div>
                </div>
              </div>

              <div className="keyword-grid">
                <div className="panel">
                  <div className="panel-header"><h2>Matched Keywords</h2><p>{parsedKeywordAnalysis.matched?.length || 0} found</p></div>
                  <div className="keyword-list matched">
                    {parsedKeywordAnalysis.matched?.map((k: any, i: number) => (
                      <span key={i} className="keyword-tag matched">{k.keyword} <small>({k.count}x)</small></span>
                    ))}
                  </div>
                </div>
                <div className="panel">
                  <div className="panel-header"><h2>Missing Keywords</h2><p>{parsedKeywordAnalysis.missing?.length || 0} needed</p></div>
                  <div className="keyword-list missing">
                    {parsedKeywordAnalysis.missing?.map((k: any, i: number) => (
                      <span key={i} className={`keyword-tag ${k.importance === 'required' ? 'missing-required' : 'missing-preferred'}`}>
                        {k.keyword} {k.importance === 'required' && <small>(Required)</small>}
                      </span>
                    ))}
                  </div>
                </div>
                {parsedKeywordAnalysis.repeated?.length > 0 && (
                  <div className="panel">
                    <div className="panel-header"><h2>Over-Used Keywords</h2><p>May appear as keyword stuffing</p></div>
                    <div className="keyword-list repeated">
                      {parsedKeywordAnalysis.repeated?.map((k: any, i: number) => (
                        <span key={i} className="keyword-tag repeated">{k.keyword} <small>({k.count}x)</small></span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'formatting' && parsedFormatting && (
            <section className="ats-formatting">
              <div className="panel">
                <div className="panel-header"><h2>Formatting Analysis</h2><p>Score: {parsedFormatting.score}/100</p></div>
                <div className="progress-bar-track large"><div className="progress-bar-fill" style={{ width: `${parsedFormatting.score}%`, background: getScoreColor(parsedFormatting.score) }} /></div>
                <div className="format-checks">
                  <div className={`check-item ${parsedFormatting.has_tables ? 'fail' : 'pass'}`}>
                    <span className="check-icon">{parsedFormatting.has_tables ? <X size={12} /> : <CheckCircle size={12} />}</span>
                    <span>Tables: {parsedFormatting.has_tables ? 'Detected (ATS may not parse)' : 'None detected'}</span>
                  </div>
                  <div className={`check-item ${parsedFormatting.has_bullets ? 'pass' : 'fail'}`}>
                    <span className="check-icon">{parsedFormatting.has_bullets ? <CheckCircle size={12} /> : <X size={12} />}</span>
                    <span>Bullet Points: {parsedFormatting.has_bullets ? 'Found' : 'Not found'}</span>
                  </div>
                </div>
                {parsedFormatting.issues?.length > 0 && (
                  <div className="issues-list">
                    <h3>Issues Found</h3>
                    {parsedFormatting.issues.map((issue: string, i: number) => (
                      <div key={i} className="issue-item">{issue}</div>
                    ))}
                  </div>
                )}
                {parsedFormatting.suggestions?.length > 0 && (
                  <div className="suggestions-list">
                    <h3>Suggestions</h3>
                    {parsedFormatting.suggestions.map((s: string, i: number) => (
                      <div key={i} className="suggestion-item">{s}</div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'experience' && parsedExperience && (
            <section className="ats-experience">
              <div className="panel">
                <div className="panel-header"><h2>Experience Analysis</h2><p>Score: {parsedExperience.score}/100</p></div>
                <div className="progress-bar-track large"><div className="progress-bar-fill" style={{ width: `${parsedExperience.score}%`, background: getScoreColor(parsedExperience.score) }} /></div>
                <div className="exp-stats">
                  <div className="stat-item"><span className="stat-value">{parsedExperience.detected_years || 0}</span><span className="stat-label">Years Detected</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedExperience.required_years || 0}</span><span className="stat-label">Years Required</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedExperience.action_verb_count || 0}</span><span className="stat-label">Action Verbs</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedExperience.quantifiable_achievements || 0}</span><span className="stat-label">Quantified Achievements</span></div>
                </div>
                {parsedExperience.action_verbs_found?.length > 0 && (
                  <div className="verb-tags">
                    <h3>Action Verbs Found</h3>
                    <div className="skill-tags">{parsedExperience.action_verbs_found.map((v: string, i: number) => <span key={i} className="skill-tag">{v}</span>)}</div>
                  </div>
                )}
                {parsedExperience.suggestions?.length > 0 && (
                  <div className="suggestions-list">
                    <h3>Suggestions</h3>
                    {parsedExperience.suggestions.map((s: string, i: number) => <div key={i} className="suggestion-item">{s}</div>)}
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'projects' && parsedProjects && (
            <section className="ats-projects">
              <div className="panel">
                <div className="panel-header"><h2>Projects Analysis</h2><p>Score: {parsedProjects.score}/100</p></div>
                <div className="progress-bar-track large"><div className="progress-bar-fill" style={{ width: `${parsedProjects.score}%`, background: getScoreColor(parsedProjects.score) }} /></div>
                <div className="exp-stats">
                  <div className="stat-item"><span className="stat-value">{parsedProjects.project_count || 0}</span><span className="stat-label">Projects Found</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedProjects.relevant_projects || 0}</span><span className="stat-label">Relevant to JD</span></div>
                  <div className="stat-item"><span className="stat-value">{parsedProjects.has_metrics ? 'Yes' : 'No'}</span><span className="stat-label">Has Metrics</span></div>
                </div>
                {parsedProjects.suggestions?.length > 0 && (
                  <div className="suggestions-list">
                    <h3>Suggestions</h3>
                    {parsedProjects.suggestions.map((s: string, i: number) => <div key={i} className="suggestion-item">{s}</div>)}
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'skills' && (
            <section className="ats-skills">
              <div className="skills-grid">
                <div className="panel">
                  <div className="panel-header"><h2>Matched Skills</h2><p>{parsedMatchedSkills.length} found</p></div>
                  <div className="skill-tags">{parsedMatchedSkills.map((s: string, i: number) => <span key={i} className="skill-tag matched">{s}</span>)}</div>
                </div>
                <div className="panel">
                  <div className="panel-header"><h2>Missing Skills</h2><p>{parsedMissingSkills.length} needed</p></div>
                  <div className="skill-tags">{parsedMissingSkills.map((s: string, i: number) => <span key={i} className="skill-tag missing">{s}</span>)}</div>
                </div>
                {parsedAdditionalSkills.length > 0 && (
                  <div className="panel">
                    <div className="panel-header"><h2>Additional Skills</h2><p>{parsedAdditionalSkills.length} extra</p></div>
                    <div className="skill-tags">{parsedAdditionalSkills.map((s: string, i: number) => <span key={i} className="skill-tag additional">{s}</span>)}</div>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'recommendations' && (
            <section className="ats-recommendations">
              {['high', 'medium', 'low'].map(priority => {
                const items = parsedRecommendations.filter((r: any) => r.priority === priority);
                if (items.length === 0) return null;
                return (
                  <div key={priority} className="panel">
                    <div className="panel-header">
                      <h2>{priority.charAt(0).toUpperCase() + priority.slice(1)} Priority</h2>
                      <p>{items.length} recommendations</p>
                    </div>
                    <div className="rec-list">
                      {items.map((rec: any, i: number) => (
                        <div key={i} className={`rec-item rec-${priority}`}>
                          <div className="rec-header">
                            <span className="rec-category">{rec.category}</span>
                            <span className="rec-priority-badge">{rec.priority}</span>
                          </div>
                          <p className="rec-message">{rec.message}</p>
                          {rec.impact && <span className="rec-impact">Impact: {rec.impact}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}

              <div className="rec-actions">
                <button type="button" className="solid" onClick={handleOptimize} disabled={optimizing}>
                  {optimizing ? <><Loader2 size={15} className="cd-spin" /> Optimizing...</> : <><Sparkles size={15} /> Quick Optimize</>}
                </button>
                <button type="button" className="solid" onClick={handleOptimizeDocx} disabled={optimizing} style={{ background: '#6366f1' }}>
                  {optimizing ? <><Loader2 size={15} className="cd-spin" /> Generating...</> : <><FileDown size={15} /> Optimize as DOCX</>}
                </button>
                <button type="button" className="ghost" onClick={() => navigate('/career/skill-gap')}>
                  View Skill Gap
                </button>
              </div>
            </section>
          )}

          {showOptimized && optimized && (
            <section className="ats-optimized">
              <div className="panel">
                <div className="panel-header">
                  <h2>Optimized Resume</h2>
                  <p>ATS-optimized version of your resume</p>
                </div>
                {optimized.professional_summary && (
                  <div className="optimized-summary">
                    <h3>Professional Summary</h3>
                    <p>{optimized.professional_summary}</p>
                  </div>
                )}
                <div className="optimized-text">
                  <h3>Optimized Content</h3>
                  <pre>{optimized.optimized_text}</pre>
                </div>
                {optimized.improvements && (() => {
                  const improvements = parseJSON(optimized.improvements);
                  if (Array.isArray(improvements) && improvements.length > 0) {
                    return (
                      <div className="improvements-list">
                        <h3>Improvements Made</h3>
                        <ul>
                          {improvements.map((imp: string, i: number) => (
                            <li key={i}>{imp}</li>
                          ))}
                        </ul>
                      </div>
                    );
                  }
                  return null;
                })()}
                <div className="optimized-actions">
                  {optimized?.format === 'docx' ? (
                    <button type="button" className="solid" onClick={handleDownloadOptimizedDocx}>
                      <FileDown size={15} /> Download DOCX
                    </button>
                  ) : optimized?.format === 'pdf' ? (
                    <button type="button" className="solid" onClick={handleDownloadOptimizedPdf}>
                      <File size={15} /> Download PDF
                    </button>
                  ) : (
                    <>
                      <button type="button" className="solid" onClick={handleDownloadOptimized}>
                        <Download size={15} /> Download TXT
                      </button>
                      <button type="button" className="solid" onClick={handleDownloadOptimizedDocx} style={{ background: '#6366f1' }}>
                        <FileDown size={15} /> Download DOCX
                      </button>
                      <button type="button" className="solid" onClick={handleDownloadOptimizedPdf} style={{ background: '#8b5cf6' }}>
                        <File size={15} /> Download PDF
                      </button>
                    </>
                  )}
                  <button type="button" className="ghost" onClick={() => setShowOptimized(false)}>
                    Close Preview
                  </button>
                </div>
              </div>
            </section>
          )}
        </>
      )}

      {!report && history.length > 0 && (
        <section className="ats-history">
          <div className="panel">
            <div className="panel-header"><h2>Previous Analyses</h2><p>{history.length} reports</p></div>
            <ul className="history-list">
              {history.slice(0, 10).map((h) => (
                <li key={h.id} onClick={() => setReport(h)}>
                  <div className="history-info">
                    <strong>Report #{h.id}</strong>
                    <span>{new Date(h.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className="history-score" style={{ color: getScoreColor(h.overall_score) }}>{h.overall_score}%</span>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
};

export default ATSReportPage;
