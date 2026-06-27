import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { careerApi } from '../../services/api';
import './ResumeOptimizerPage.css';

interface ResumeAnalysis {
  id: number;
  resume_id: number;
  summary: string;
  detected_skills: string[];
  experience_level: string;
  ats_score: number;
  ats_suggestions: string[];
  resume_match_score: number;
  created_at: string;
}

interface JobDescription {
  id: number;
  title: string;
  company: string;
}

interface OptimizedResume {
  id: number;
  optimized_text: string;
  improvements: string[];
  professional_summary: string;
  optimized_skills: string[];
  optimized_projects: string[];
  optimized_keywords: string[];
  optimized_experience: string[];
}

const ResumeOptimizerPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<ResumeAnalysis[]>([]);
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<number | null>(null);
  const [selectedJd, setSelectedJd] = useState<number | null>(null);
  const [result, setResult] = useState<OptimizedResume | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchingData, setFetchingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [originalText, setOriginalText] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setFetchingData(true);
      const [analysisResp, jdResp] = await Promise.all([
        careerApi.getResumeAnalyses(),
        careerApi.getJobDescriptions(),
      ]);
      setAnalyses(analysisResp.data);
      setJds(jdResp.data.items || jdResp.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setFetchingData(false);
    }
  };

  const handleOptimize = async () => {
    if (!selectedAnalysis) return;
    try {
      setLoading(true);
      setError(null);
      setShowComparison(false);
      const resp = await careerApi.optimizeResume(selectedAnalysis, selectedJd || undefined);
      const raw = resp.data;
      setResult({
        ...raw,
        improvements: typeof raw.improvements === 'string' ? JSON.parse(raw.improvements) : (raw.improvements || []),
        optimized_skills: typeof raw.optimized_skills === 'string' ? JSON.parse(raw.optimized_skills) : (raw.optimized_skills || []),
        optimized_projects: typeof raw.optimized_projects === 'string' ? JSON.parse(raw.optimized_projects) : (raw.optimized_projects || []),
        optimized_keywords: typeof raw.optimized_keywords === 'string' ? JSON.parse(raw.optimized_keywords) : (raw.optimized_keywords || []),
        optimized_experience: typeof raw.optimized_experience === 'string' ? JSON.parse(raw.optimized_experience) : (raw.optimized_experience || []),
      });
      const analysis = analyses.find((a) => a.id === selectedAnalysis);
      if (analysis) {
        setOriginalText(analysis.summary || '');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.optimized_text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'optimized_resume.txt';
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (fetchingData) {
    return (
      <div className="optimizer-page">
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading optimization data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="optimizer-page">
      <header className="career-header">
        <div>
          <h1>Resume Optimizer</h1>
          <p>AI-powered resume optimization tailored to your target role</p>
        </div>
        <div className="header-actions">
          <button type="button" className="ghost" onClick={() => navigate('/career/dashboard')}>Dashboard</button>
          <button type="button" className="ghost" onClick={() => navigate('/career/skill-gap')}>Skill Gap</button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="optimizer-layout">
        <section className="optimizer-controls">
          <div className="panel">
            <div className="panel-header">
              <h2>Configure Optimization</h2>
              <p>Select a resume analysis and optionally a job description</p>
            </div>
            <div className="controls-form">
              <label className="input-field">
                <span>Resume Analysis *</span>
                <select
                  value={selectedAnalysis || ''}
                  onChange={(e) => setSelectedAnalysis(Number(e.target.value) || null)}
                >
                  <option value="">Select a resume analysis</option>
                  {analyses.map((a) => (
                    <option key={a.id} value={a.id}>
                      Analysis #{a.id} - {new Date(a.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </label>
              <label className="input-field">
                <span>Job Description (optional)</span>
                <select
                  value={selectedJd || ''}
                  onChange={(e) => setSelectedJd(Number(e.target.value) || null)}
                >
                  <option value="">No JD (general optimization)</option>
                  {jds.map((jd) => (
                    <option key={jd.id} value={jd.id}>
                      {jd.title}{jd.company ? ` - ${jd.company}` : ''}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="solid"
                onClick={handleOptimize}
                disabled={!selectedAnalysis || loading}
              >
                {loading ? 'Optimizing...' : 'Optimize Resume'}
              </button>
            </div>
          </div>
        </section>

        {loading && (
          <div className="optimizing-overlay">
            <div className="spinner" />
            <p>Optimizing your resume with AI...</p>
          </div>
        )}

        {result && !loading && (
          <section className="optimized-result">
            <div className="result-actions">
              <button
                type="button"
                className="ghost"
                onClick={() => setShowComparison(!showComparison)}
              >
                {showComparison ? 'Hide Comparison' : 'Compare Original vs Optimized'}
              </button>
              <button
                type="button"
                className="solid"
                onClick={handleDownload}
              >
                Download Optimized Resume
              </button>
            </div>

            {showComparison && (
              <div className="comparison-grid">
                <div className="panel">
                  <div className="panel-header">
                    <h2>Original</h2>
                    <p>Before optimization</p>
                  </div>
                  <div className="text-preview">
                    {originalText || 'No original text available'}
                  </div>
                </div>
                <div className="panel">
                  <div className="panel-header">
                    <h2>Optimized</h2>
                    <p>After optimization</p>
                  </div>
                  <div className="text-preview">
                    {result.optimized_text}
                  </div>
                </div>
              </div>
            )}

            {!showComparison && (
              <div className="panel">
                <div className="panel-header">
                  <h2>Optimized Resume</h2>
                  <p>AI-enhanced resume text</p>
                </div>
                <div className="text-preview">
                  {result.optimized_text}
                </div>
              </div>
            )}

            {result.improvements.length > 0 && (
              <div className="panel">
                <div className="panel-header">
                  <h2>Improvements Made</h2>
                  <p>{result.improvements.length} changes applied</p>
                </div>
                <ol className="improvement-list">
                  {result.improvements.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ol>
              </div>
            )}

            <div className="result-grid">
              {result.professional_summary && (
                <div className="panel">
                  <div className="panel-header">
                    <h2>Professional Summary</h2>
                    <p>Enhanced summary statement</p>
                  </div>
                  <div className="text-preview">
                    {result.professional_summary}
                  </div>
                </div>
              )}

              {result.optimized_skills.length > 0 && (
                <div className="panel">
                  <div className="panel-header">
                    <h2>Optimized Skills</h2>
                    <p>{result.optimized_skills.length} skills highlighted</p>
                  </div>
                  <div className="skill-tags">
                    {result.optimized_skills.map((skill, idx) => (
                      <span key={idx} className="skill-tag optimized">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {result.optimized_keywords.length > 0 && (
                <div className="panel">
                  <div className="panel-header">
                    <h2>Keywords</h2>
                    <p>{result.optimized_keywords.length} keywords added</p>
                  </div>
                  <div className="skill-tags">
                    {result.optimized_keywords.map((kw, idx) => (
                      <span key={idx} className="skill-tag keyword">{kw}</span>
                    ))}
                  </div>
                </div>
              )}

              {result.optimized_experience.length > 0 && (
                <div className="panel">
                  <div className="panel-header">
                    <h2>Optimized Experience</h2>
                    <p>{result.optimized_experience.length} bullet points</p>
                  </div>
                  <div className="text-preview">
                    {result.optimized_experience.map((exp, idx) => (
                      <div key={idx} className="experience-item">{exp}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default ResumeOptimizerPage;
