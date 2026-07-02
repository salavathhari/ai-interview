import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Sparkles,
  Brain,
  Target,
  Briefcase,
  Rocket,
  Link,
  Loader2,
  BarChart3,
  LayoutDashboard,
  ArrowLeft,
  CheckCircle2,
} from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { resumeApi, mlApi } from '../../services/api';
import './MLInsightsPage.css';

const Gauge: React.FC<{ value: number; max?: number; size?: number; color: string; label: string; sub?: string; suffix?: string }> = ({ value, max = 100, size = 120, color, label, sub, suffix = '' }) => {
  const r = (size - 16) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value / max, 1);
  const offset = circ * (1 - pct);
  return (
    <div className="ml-gauge-card">
      <h3>{label}</h3>
      <div className="ml-gauge-ring" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`}>
          <circle className="track" cx={size/2} cy={size/2} r={r} />
          <circle className="indicator" cx={size/2} cy={size/2} r={r} stroke={color} strokeDashoffset={offset} />
        </svg>
        <div className="ml-gauge-center">
          <span className="ml-gauge-value" style={{ color }}>{Math.round(value)}<span className="ml-gauge-unit">{suffix}</span></span>
        </div>
      </div>
      {sub && <span className="ml-gauge-sub">{sub}</span>}
    </div>
  );
};

const SkillGapBar: React.FC<{ matched: number; partial: number; missing: number }> = ({ matched, partial, missing }) => {
  const total = matched + partial + missing || 1;
  return (
    <div>
      <div className="ml-gap-bar">
        <div className="ml-gap-segment" style={{ width: `${(matched/total)*100}%`, background: '#10b981' }} />
        <div className="ml-gap-segment" style={{ width: `${(partial/total)*100}%`, background: '#f59e0b' }} />
        <div className="ml-gap-segment" style={{ width: `${(missing/total)*100}%`, background: '#ef4444' }} />
      </div>
      <div className="ml-gap-legend">
        <div className="ml-gap-legend-item"><div className="ml-gap-legend-dot" style={{ background: '#10b981' }} /> Matched ({matched})</div>
        <div className="ml-gap-legend-item"><div className="ml-gap-legend-dot" style={{ background: '#f59e0b' }} /> Partial ({partial})</div>
        <div className="ml-gap-legend-item"><div className="ml-gap-legend-dot" style={{ background: '#ef4444' }} /> Missing ({missing})</div>
      </div>
    </div>
  );
};

const SkillCatCard: React.FC<{ title: string; skills: string[]; color: string }> = ({ title, skills, color }) => (
  <div className="ml-skill-cat-card">
    <div className="ml-skill-cat-header">
      <div className="ml-skill-cat-title"><div className="ml-skill-cat-dot" style={{ background: color }} />{title}</div>
      <span className="ml-skill-cat-count">{skills.length}</span>
    </div>
    {skills.length > 0 ? (
      <div className="ml-skill-tags">
        {skills.map(s => <span key={s} className="ml-skill-tag" style={{ color, borderColor: `${color}44`, background: `${color}0d` }}>{s}</span>)}
      </div>
    ) : <p style={{ color: 'var(--muted)', fontSize: 13, margin: 0 }}>None detected</p>}
  </div>
);

const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#0f172a', color: '#e2e8f0', padding: '8px 12px', borderRadius: 8, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
      <p style={{ margin: 0, fontWeight: 600 }}>{label || payload[0].name}</p>
      <p style={{ margin: 0, color: payload[0].color || payload[0].fill }}>{payload[0].value}</p>
    </div>
  );
};

interface Resume { id: number; filename: string; skills?: string; created_at: string; }
interface Classification { predicted_role: string; confidence: number; }
interface SkillData { programming_languages?: string[]; frameworks?: string[]; databases?: string[]; cloud_platforms?: string[]; devops_tools?: string[]; ai_frameworks?: string[]; soft_skills?: string[]; operating_systems?: string[]; methodologies?: string[]; all_skills?: string[]; }
interface ATSPrediction { ats_score: number; confidence: number; }
interface JobRecommendation { role: string; score: number; }
interface CareerPathItem { role: string; path_type: string; match_score: number; gap_skills: string[]; matching_skills: string[]; }
interface SkillGapData { matched: string[]; partial: string[]; missing: string[]; match_percentage: number; }
interface QualityPrediction { quality: string; confidence: number; }

const SKILL_COLORS: Record<string, string> = {
  programming_languages: '#3b82f6', frameworks: '#8b5cf6', databases: '#10b981',
  cloud_platforms: '#f59e0b', devops_tools: '#ef4444', ai_frameworks: '#ec4899',
  soft_skills: '#06b6d4', operating_systems: '#64748b', methodologies: '#84cc16',
};

const SKILL_LABELS: Record<string, string> = {
  programming_languages: 'Languages', frameworks: 'Frameworks', databases: 'Databases',
  cloud_platforms: 'Cloud', devops_tools: 'DevOps', ai_frameworks: 'AI / ML',
  soft_skills: 'Soft Skills', operating_systems: 'OS', methodologies: 'Methodologies',
};

const PIE_COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16', '#f97316'];

const MLInsightsPage: React.FC = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'skills' | 'jobs' | 'analytics'>('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hasRun, setHasRun] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  const [classification, setClassification] = useState<Classification | null>(null);
  const [skills, setSkills] = useState<SkillData | null>(null);
  const [atsPred, setAtsPred] = useState<ATSPrediction | null>(null);
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [careerPath, setCareerPath] = useState<CareerPathItem[]>([]);
  const [quality, setQuality] = useState<QualityPrediction | null>(null);
  const [skillGap, setSkillGap] = useState<SkillGapData | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => { loadResumes(); loadAnalytics(); }, []);

  const loadResumes = async () => {
    try { const r = await resumeApi.getMyResumes(); setResumes(r.data); if (r.data.length && !selectedResumeId) setSelectedResumeId(r.data[0].id); } catch {}
  };

  const loadAnalytics = async () => {
    try { const r = await mlApi.getAnalytics(); setAnalytics(r.data); } catch {}
  };

  const runFullAnalysis = useCallback(async () => {
    if (!selectedResumeId) return;
    setLoading(true); setError(''); setAnalysisComplete(false);
    try {
      // Wait for background text extraction to finish before running ML analysis
      const pollInterval = 2000;
      const maxWait = 60000;
      let waited = 0;
      while (waited < maxWait) {
        const statusResp = await resumeApi.getStatus(selectedResumeId);
        const st = statusResp.data.status;
        if (st === 'completed') break;
        if (st === 'failed') {
          setError(statusResp.data.error || 'Resume extraction failed. Please re-upload.');
          setLoading(false);
          return;
        }
        await new Promise(r => setTimeout(r, pollInterval));
        waited += pollInterval;
      }
      if (waited >= maxWait) {
        setError('Resume extraction is taking too long. Please try again later.');
        setLoading(false);
        return;
      }

      const r = await mlApi.analyzeFull(selectedResumeId);
      const d = r.data;
      setClassification(d.classification);
      setSkills(d.skills);
      setAtsPred(d.ats_prediction);
      setJobs(d.job_recommendations || []);
      setQuality(d.quality);
      setCareerPath(d.career_path?.recommended_paths || []);
      setSkillGap(d.skill_gap);
      setHasRun(true);
      setAnalysisComplete(true);
      setTimeout(() => setAnalysisComplete(false), 2500);
      loadAnalytics();
    } catch (e: any) { setError(e.response?.data?.detail || 'Analysis failed'); }
    finally { setLoading(false); }
  }, [selectedResumeId]);

  const scoreColor = (s: number) => s >= 80 ? '#10b981' : s >= 60 ? '#3b82f6' : s >= 40 ? '#f59e0b' : '#ef4444';
  const qualityColor = (q: string) => ({ Excellent: '#10b981', Good: '#3b82f6', Average: '#f59e0b', Poor: '#ef4444' }[q] || '#6b7280');

  const rolePieData = useMemo(() => {
    if (!analytics?.role_distribution) return [];
    return Object.entries(analytics.role_distribution).map(([name, value]) => ({ name, value }));
  }, [analytics]);

  const qualityBarData = useMemo(() => {
    if (!analytics?.quality_distribution) return [];
    return Object.entries(analytics.quality_distribution).map(([name, value]) => ({ name, value }));
  }, [analytics]);

  const skillRadarData = useMemo(() => {
    if (!skills) return [];
    return Object.keys(SKILL_COLORS).map(k => ({ subject: SKILL_LABELS[k], A: ((skills as any)[k] || []).length, fullMark: 15 }));
  }, [skills]);

  const tabs = [
    { key: 'overview' as const, label: 'Overview', icon: <LayoutDashboard size={15} /> },
    { key: 'skills' as const, label: 'Skills', icon: <Target size={15} /> },
    { key: 'jobs' as const, label: 'Jobs & Career', icon: <Briefcase size={15} /> },
    { key: 'analytics' as const, label: 'Analytics', icon: <BarChart3 size={15} /> },
  ];

  return (
    <div className="ml-page">
      <div className="ml-top-bar">
        <div className="ml-top-bar-left">
          <span className="ml-badge">ML</span>
          <div>
            <h1>Resume Intelligence</h1>
            <p>AI-powered analysis, classification, and career recommendations</p>
          </div>
        </div>
        <div className="ml-top-bar-actions">
          <button className="ml-btn-primary" style={{ background: 'var(--surface)', color: 'var(--ink)', border: '1.5px solid var(--border)', boxShadow: 'none' }} onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={15} /> Dashboard
          </button>
          <select className="ml-select" value={selectedResumeId || ''} onChange={e => setSelectedResumeId(Number(e.target.value))}>
            <option value="">Select a resume...</option>
            {resumes.map(r => <option key={r.id} value={r.id}>{r.filename}</option>)}
          </select>
          <button
            className={`ml-btn-primary ${loading ? 'btn--analyzing btn--pulse' : ''} ${analysisComplete ? 'btn--success' : ''}`}
            onClick={runFullAnalysis}
            disabled={!selectedResumeId || loading}
          >
            {loading ? (
              <><Loader2 size={15} className="btn-spinner" /> Analyzing...</>
            ) : analysisComplete ? (
              <><CheckCircle2 size={15} /> Analysis Complete</>
            ) : (
              <><Sparkles size={15} /> Run Analysis</>
            )}
          </button>
        </div>
      </div>

      {error && <div className="ml-error">{error}</div>}

      <div className="ml-tabs">
        {tabs.map(t => (
          <button key={t.key} className={`ml-tab ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="ml-loading-grid">
          {[1,2,3].map(i => <div key={i} className="ml-skeleton ml-skeleton-card" />)}
        </div>
      )}

      {!loading && activeTab === 'overview' && (
        <>
          <div className="ml-gauges-row">
            <Gauge value={atsPred?.ats_score ?? 0} color={scoreColor(atsPred?.ats_score ?? 0)} label="ATS Score" sub={atsPred ? `${atsPred.confidence}% confidence` : 'Run analysis'} />
            <div className="ml-gauge-card">
              <h3>Classification</h3>
              {classification ? (
                <>
                  <div className="ml-classification-badge">
                    <Brain size={18} /> {classification.predicted_role}
                  </div>
                  <div style={{ width: '100%' }}>
                    <div className="ml-job-bar">
                      <div className="ml-job-bar-fill" style={{ width: `${classification.confidence}%`, background: scoreColor(classification.confidence) }} />
                    </div>
                    <p className="ml-gauge-sub" style={{ marginTop: 6 }}>{classification.confidence}% confidence</p>
                  </div>
                </>
              ) : <p className="ml-gauge-sub">Run analysis</p>}
            </div>
            <div className="ml-gauge-card">
              <h3>Quality</h3>
              {quality ? (
                <>
                  <span className={`ml-quality-badge ${quality.quality.toLowerCase()}`}>{quality.quality}</span>
                  <div style={{ width: '100%' }}>
                    <div className="ml-job-bar">
                      <div className="ml-job-bar-fill" style={{ width: `${quality.confidence}%`, background: qualityColor(quality.quality) }} />
                    </div>
                    <p className="ml-gauge-sub" style={{ marginTop: 6 }}>{quality.confidence}% confidence</p>
                  </div>
                </>
              ) : <p className="ml-gauge-sub">Run analysis</p>}
            </div>
          </div>

          <div className="ml-content-grid">
            <div className="ml-panel">
              <div className="ml-panel-header">
                <h2><Briefcase size={18} /> Job Recommendations</h2>
                {jobs.length > 0 && <span className="count">{jobs.length} roles</span>}
              </div>
              {jobs.length > 0 ? jobs.slice(0, 5).map((job, i) => (
                <div key={i} className="ml-job-item">
                  <div className={`ml-job-rank ${i === 0 ? 'top' : ''}`}>{i + 1}</div>
                  <div className="ml-job-info">
                    <div className="ml-job-name">{job.role}</div>
                    <div className="ml-job-bar"><div className="ml-job-bar-fill" style={{ width: `${job.score}%`, background: scoreColor(job.score) }} /></div>
                  </div>
                  <span className="ml-job-score" style={{ color: scoreColor(job.score) }}>{job.score}%</span>
                </div>
              )) : <div className="ml-empty"><Briefcase size={40} /><p>Run analysis to see recommendations</p></div>}
            </div>

            <div className="ml-panel">
              <div className="ml-panel-header">
                <h2><Rocket size={18} /> Career Progression</h2>
              </div>
              {careerPath.length > 0 ? (
                <div className="ml-timeline">
                  {careerPath.slice(0, 5).map((path, i) => (
                    <div key={i} className="ml-timeline-item">
                      <div className={`ml-timeline-dot ${path.path_type}`} />
                      <div className="ml-timeline-role">{path.role}</div>
                      <div className="ml-timeline-meta">
                        <span className={`ml-timeline-tag ${path.path_type}`}>{path.path_type}</span>
                        <span>{path.match_score}% match</span>
                      </div>
                      {path.gap_skills.length > 0 && (
                        <div style={{ marginTop: 4, fontSize: 12, color: 'var(--muted)' }}>
                          Skills needed: {path.gap_skills.slice(0, 3).join(', ')}{path.gap_skills.length > 3 ? ` +${path.gap_skills.length - 3}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : <div className="ml-empty"><Rocket size={40} /><p>Run analysis to see career path</p></div>}
            </div>
          </div>

          {skillGap && (
            <div className="ml-panel">
              <div className="ml-panel-header">
                <h2><Link size={18} /> Skill Gap Analysis</h2>
                <span className="count">{skillGap.match_percentage}% match</span>
              </div>
              <SkillGapBar matched={skillGap.matched.length} partial={skillGap.partial.length} missing={skillGap.missing.length} />
              <div className="ml-skill-gap-grid">
                {skillGap.matched.length > 0 && (
                  <div>
                    <p className="ml-skill-gap-label matched">Matched</p>
                    <div className="ml-skill-tags">{skillGap.matched.map(s => <span key={s} className="ml-skill-tag" style={{ color: '#10b981', borderColor: '#10b98144', background: '#10b9810d' }}>{s}</span>)}</div>
                  </div>
                )}
                {skillGap.partial.length > 0 && (
                  <div>
                    <p className="ml-skill-gap-label partial">Partial</p>
                    <div className="ml-skill-tags">{skillGap.partial.map(s => <span key={s} className="ml-skill-tag" style={{ color: '#f59e0b', borderColor: '#f59e0b44', background: '#f59e0b0d' }}>{s}</span>)}</div>
                  </div>
                )}
                {skillGap.missing.length > 0 && (
                  <div>
                    <p className="ml-skill-gap-label missing">Missing</p>
                    <div className="ml-skill-tags">{skillGap.missing.map(s => <span key={s} className="ml-skill-tag" style={{ color: '#ef4444', borderColor: '#ef444444', background: '#ef44440d' }}>{s}</span>)}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {!hasRun && !loading && (
            <div className="ml-panel ml-empty-panel">
              <Sparkles size={48} />
              <h2>Select a resume and run analysis</h2>
              <p>Get AI-powered classification, ATS scoring, skill extraction, and career recommendations</p>
            </div>
          )}
        </>
      )}

      {!loading && activeTab === 'skills' && (
        <>
          {skills ? (
            <div className="ml-skills-grid">
              {Object.keys(SKILL_COLORS).map(k => (
                <SkillCatCard key={k} title={SKILL_LABELS[k]} skills={(skills as any)[k] || []} color={SKILL_COLORS[k]} />
              ))}
            </div>
          ) : <div className="ml-panel"><div className="ml-empty"><Target size={40} /><p>Run analysis to see extracted skills</p></div></div>}
        </>
      )}

      {!loading && activeTab === 'jobs' && (
        <div className="ml-content-grid">
          <div className="ml-panel">
            <div className="ml-panel-header">
              <h2><Briefcase size={18} /> Job Recommendations</h2>
            </div>
            {jobs.length > 0 ? jobs.map((job, i) => (
              <div key={i} className="ml-job-item">
                <div className={`ml-job-rank ${i === 0 ? 'top' : ''}`}>{i + 1}</div>
                <div className="ml-job-info">
                  <div className="ml-job-name">{job.role}</div>
                  <div className="ml-job-bar"><div className="ml-job-bar-fill" style={{ width: `${job.score}%`, background: scoreColor(job.score) }} /></div>
                </div>
                <span className="ml-job-score" style={{ color: scoreColor(job.score) }}>{job.score}%</span>
              </div>
            )) : <div className="ml-empty"><Briefcase size={40} /><p>No recommendations</p></div>}
          </div>

          <div className="ml-panel">
            <div className="ml-panel-header">
              <h2><Rocket size={18} /> Career Path</h2>
            </div>
            {careerPath.length > 0 ? (
              <div className="ml-timeline">
                {careerPath.map((path, i) => (
                  <div key={i} className="ml-timeline-item">
                    <div className={`ml-timeline-dot ${path.path_type}`} />
                    <div className="ml-timeline-role">{path.role}</div>
                    <div className="ml-timeline-meta">
                      <span className={`ml-timeline-tag ${path.path_type}`}>{path.path_type}</span>
                      <span>{path.match_score}% match</span>
                    </div>
                    {path.gap_skills.length > 0 && (
                      <div style={{ marginTop: 4, fontSize: 12, color: 'var(--muted)' }}>
                        Gap: {path.gap_skills.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : <div className="ml-empty"><Rocket size={40} /><p>No career path data</p></div>}
          </div>
        </div>
      )}

      {!loading && activeTab === 'analytics' && (
        <>
          <div className="ml-stats-grid">
            {[
              { label: 'Classifications', value: analytics?.total_classifications || 0, color: '#8b5cf6' },
              { label: 'ATS Predictions', value: analytics?.total_ats_predictions || 0, color: '#3b82f6' },
              { label: 'Avg ATS Score', value: analytics?.average_ats_score || 0, color: '#10b981' },
              { label: 'Quality Checks', value: analytics?.total_quality_predictions || 0, color: '#f59e0b' },
            ].map(s => (
              <div key={s.label} className="ml-stat-card">
                <div className="ml-stat-value" style={{ color: s.color }}>{s.value}</div>
                <div className="ml-stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          <div className="ml-content-grid">
            <div className="ml-panel">
              <div className="ml-panel-header"><h2><BarChart3 size={18} /> Role Distribution</h2></div>
              {rolePieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={rolePieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" label={({ name, percent }: any) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}>
                      {rolePieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              ) : <div className="ml-empty"><BarChart3 size={40} /><p>No classification data</p></div>}
            </div>

            <div className="ml-panel">
              <div className="ml-panel-header"><h2><BarChart3 size={18} /> Quality Distribution</h2></div>
              {qualityBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={qualityBarData}>
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#64748b' }} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {qualityBarData.map((entry, i) => <Cell key={i} fill={qualityColor(entry.name)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : <div className="ml-empty"><BarChart3 size={40} /><p>No quality data</p></div>}
            </div>
          </div>

          <div className="ml-content-grid">
            <div className="ml-panel">
              <div className="ml-panel-header"><h2><Target size={18} /> Skill Radar</h2></div>
              {skillRadarData.some(d => d.A > 0) ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={skillRadarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <PolarRadiusAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <Radar name="Skills" dataKey="A" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.2} />
                  </RadarChart>
                </ResponsiveContainer>
              ) : <div className="ml-empty"><Target size={40} /><p>No skill data</p></div>}
            </div>

            <div className="ml-panel">
              <div className="ml-panel-header"><h2><Target size={18} /> Skill Distribution</h2></div>
              {skills ? Object.keys(SKILL_COLORS).map(k => {
                const count = ((skills as any)[k] || []).length;
                const pct = Math.min((count / 15) * 100, 100);
                return (
                  <div key={k} className="ml-hbar">
                    <span className="ml-hbar-label">{SKILL_LABELS[k]}</span>
                    <div className="ml-hbar-track"><div className="ml-hbar-fill" style={{ width: `${pct}%`, background: SKILL_COLORS[k] }} /></div>
                    <span className="ml-hbar-value">{count}</span>
                  </div>
                );
              }) : <div className="ml-empty"><Target size={40} /><p>No skill data</p></div>}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MLInsightsPage;
