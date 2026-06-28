import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { careerApi } from '../../services/api';
import './LearningRoadmapPage.css';

interface CodingProblem {
  title: string;
  difficulty: string;
  topic: string;
  leetcode?: string;
}

interface Topic {
  name: string;
  order: number;
  prerequisites: string[];
  difficulty: string;
  estimated_hours: number;
  description: string;
  resources: {
    documentation: string[];
    videos: string[];
    practice_projects: string[];
  };
  interview_questions: string[];
  coding_problems: (string | CodingProblem)[];
}

interface Phase {
  phase_number: number;
  title: string;
  objective: string;
  priority: string;
  estimated_hours: number;
  estimated_weeks: number;
  phase_type: string;
  status: string;
  progress_percentage: number;
  topics: Topic[];
  milestone: string;
  weak_areas?: string[];
}

interface MentorTip {
  type: string;
  title: string;
  message: string;
  action?: string;
  action_url?: string;
}

interface RoadmapData {
  roadmap_id?: number;
  career_goal: string;
  total_hours: number;
  estimated_weeks: number;
  current_readiness: number;
  target_readiness: number;
  phases: Phase[];
  daily_plan: {
    today_focus: string;
    hours_today: number;
    activities: string[];
    streak_days: number;
    needs_analysis?: boolean;
  };
  mentor_tips: MentorTip[];
  skill_gap_summary: {
    matched_count: number;
    missing_count: number;
    priority_count: number;
    match_percentage: number;
  };
  interview_readiness: number;
  coding_readiness: number;
}

interface SkillGapAnalysis {
  id: number;
  match_percentage: number;
  missing_skills: string;
  priority_skills: string;
  created_at: string;
}

interface SavedRoadmap {
  id: number;
  career_goal: string | null;
  status: string;
  progress_percentage: number;
  total_hours: number;
  estimated_weeks: number;
  version: number;
  created_at: string;
}

const Icon = {
  Book: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>,
  Target: () => <svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>,
  Clock: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  Calendar: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>,
  Check: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  CheckCircle: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
  ArrowRight: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>,
  Sparkles: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L9 12l-7 3 7 3 3 10 3-10 7-3-7-3z"/></svg>,
  TrendUp: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
  Brain: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A5.5 5.5 0 004 7.5c0 1.33.47 2.55 1.26 3.5H4a3 3 0 000 6h1.5"/><path d="M14.5 2A5.5 5.5 0 0120 7.5c0 1.33-.47 2.55-1.26 3.5H20a3 3 0 010 6h-1.5"/><path d="M12 2v20"/></svg>,
  Code: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  Mic: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>,
  Loader: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lr-spin"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>,
  AlertTriangle: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  Trash: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>,
  ExternalLink: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>,
  Flame: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"/></svg>,
  Star: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  Zap: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
};

const LearningRoadmapPage: React.FC = () => {
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [savedRoadmaps, setSavedRoadmaps] = useState<SavedRoadmap[]>([]);
  const [skillGaps, setSkillGaps] = useState<SkillGapAnalysis[]>([]);
  const [selectedGapId, setSelectedGapId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activePhase, setActivePhase] = useState<number>(0);
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [completedTopics, setCompletedTopics] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<number | null>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => { loadData(); }, []);

  // Auto-generate when navigated from SkillGapPage with ?gap= and no active roadmap
  useEffect(() => {
    if (!loading && !roadmapData && !generating) {
      const urlGapId = Number(searchParams.get('gap'));
      if (urlGapId && selectedGapId === urlGapId) {
        handleGenerateEnhanced();
      }
    }
  }, [loading, selectedGapId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [currentResp, gapsResp, historyResp] = await Promise.all([
        careerApi.getCurrentRoadmap().catch(() => ({ data: { roadmap: null } })),
        careerApi.getSkillGapAnalyses(),
        careerApi.getRoadmapHistory().catch(() => ({ data: { roadmaps: [] } })),
      ]);
      const gaps = gapsResp.data.items || gapsResp.data || [];
      setSkillGaps(gaps);
      setSavedRoadmaps(historyResp.data.roadmaps || []);

      // Auto-select gap from URL query param or if there's just one
      const urlGapId = Number(searchParams.get('gap'));
      if (urlGapId && gaps.some((g: any) => g.id === urlGapId)) {
        setSelectedGapId(urlGapId);
      } else if (gaps.length === 1 && !selectedGapId) {
        setSelectedGapId(gaps[0].id);
      }

      // Load active roadmap with full metadata
      if (currentResp.data.roadmap) {
        const rm = currentResp.data;
        const roadmap = rm.roadmap;
        try {
          const completed = roadmap.completed_topics ? JSON.parse(roadmap.completed_topics) : [];
          setCompletedTopics(new Set(completed));
        } catch { setCompletedTopics(new Set()); }

        setRoadmapData({
          roadmap_id: roadmap.id,
          career_goal: roadmap.career_goal || 'Software Engineer',
          total_hours: roadmap.total_hours || 0,
          estimated_weeks: roadmap.estimated_weeks || 0,
          current_readiness: roadmap.current_readiness || 0,
          target_readiness: roadmap.target_readiness || 85,
          phases: rm.phases || [],
          daily_plan: rm.daily_plan || { today_focus: 'Continue learning', hours_today: 2, activities: [], streak_days: 0 },
          mentor_tips: rm.mentor_tips || [],
          skill_gap_summary: rm.skill_gap_summary || { matched_count: 0, missing_count: 0, priority_count: 0, match_percentage: 0 },
          interview_readiness: roadmap.interview_readiness || 0,
          coding_readiness: roadmap.coding_readiness || 0,
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally { setLoading(false); }
  };

  const handleGenerateEnhanced = async () => {
    if (!selectedGapId) return;
    try {
      setGenerating(true);
      setError(null);
      const resp = await careerApi.generateEnhancedRoadmap(selectedGapId);

      const phases = resp.data.phases || [];
      const dailyPlan = resp.data.daily_plan || {};
      const mentorTips = resp.data.mentor_tips || [];
      const gapSummary = resp.data.skill_gap_summary || {};

      setRoadmapData({
        roadmap_id: resp.data.roadmap_id,
        career_goal: resp.data.career_goal || 'Software Engineer',
        total_hours: resp.data.total_hours || 0,
        estimated_weeks: resp.data.estimated_weeks || 0,
        current_readiness: resp.data.current_readiness || 0,
        target_readiness: resp.data.target_readiness || 85,
        phases: phases,
        daily_plan: dailyPlan,
        mentor_tips: mentorTips,
        skill_gap_summary: gapSummary,
        interview_readiness: resp.data.interview_readiness || 0,
        coding_readiness: resp.data.coding_readiness || 0,
      });

      const completed = phases.flatMap((p: Phase) =>
        p.topics.filter((t: Topic) => completedTopics.has(t.name)).map((t: Topic) => t.name)
      );
      setCompletedTopics(new Set(completed));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate roadmap');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteRoadmap = async (id: number) => {
    try {
      setDeleting(id);
      await careerApi.deleteRoadmap(id);
      if (roadmapData?.roadmap_id === id) setRoadmapData(null);
      loadData();
    } catch { console.error('Failed to delete'); }
    finally { setDeleting(null); }
  };

  const toggleTopicComplete = (topicName: string) => {
    const newCompleted = new Set(completedTopics);
    if (newCompleted.has(topicName)) newCompleted.delete(topicName);
    else newCompleted.add(topicName);
    setCompletedTopics(newCompleted);
    if (roadmapData?.roadmap_id) {
      careerApi.updateRoadmapProgress(roadmapData.roadmap_id, Array.from(newCompleted)).catch(() => {});
    }
  };

  const getPhaseProgress = (phase: Phase): number => {
    if (!phase?.topics?.length) return 0;
    const done = phase.topics.filter(t => completedTopics.has(t.name)).length;
    return Math.round((done / phase.topics.length) * 100);
  };

  const getOverallProgress = (): number => {
    if (!roadmapData) return 0;
    const allTopics = (roadmapData.phases || []).flatMap(p => p.topics || []);
    if (!allTopics.length) return 0;
    const done = allTopics.filter(t => completedTopics.has(t.name)).length;
    return Math.round((done / allTopics.length) * 100);
  };

  const formatDate = (d: string) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  const getDifficultyColor = (d: string) => {
    switch (d.toLowerCase()) {
      case 'easy': case 'beginner': return '#10b981';
      case 'medium': case 'intermediate': return '#f59e0b';
      case 'hard': case 'advanced': return '#ef4444';
      default: return '#64748b';
    }
  };

  const getPriorityColor = (p: string) => {
    switch (p.toLowerCase()) {
      case 'critical': case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#64748b';
    }
  };

  const getTipIcon = (type: string) => {
    switch (type) {
      case 'priority': return <Icon.Target />;
      case 'urgent': return <Icon.Flame />;
      case 'success': return <Icon.CheckCircle />;
      case 'warning': return <Icon.AlertTriangle />;
      default: return <Icon.Sparkles />;
    }
  };

  if (loading) {
    return (
      <div className="lr-page">
        <div className="lr-loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lr-spin" style={{ width: 40, height: 40, color: '#8b5cf6' }}>
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
          </svg>
          <p>Loading your learning journey...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="lr-page">
      {/* Header */}
      <header className="lr-header">
        <div className="lr-header-left">
          <div className="lr-header-icon"><Icon.Book /></div>
          <div>
            <h1>AI Learning Planner</h1>
            <p>Your personalized career learning journey</p>
          </div>
        </div>
        <div className="lr-header-actions">
          <button type="button" className="lr-btn lr-btn-ghost" onClick={() => navigate('/career/dashboard')}>
            Dashboard
          </button>
          {savedRoadmaps.length > 0 && (
            <button type="button" className="lr-btn lr-btn-ghost lr-btn-sm" onClick={() => setRoadmapData(null)}>
              Generate New
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="lr-error">
          <Icon.AlertTriangle />
          <span>{error}</span>
        </div>
      )}

      {/* No roadmap state */}
      {!roadmapData && !generating && (
        <>
          {skillGaps.length > 0 ? (
            <section className="lr-generate">
              <div className="lr-generate-card">
                <div className="lr-generate-left">
                  <div className="lr-generate-icon"><Icon.Sparkles /></div>
                  <div>
                    <h3>Generate AI Learning Roadmap</h3>
                    <p>Create a personalized learning journey from your skill gap analysis</p>
                  </div>
                </div>
                <div className="lr-generate-right">
                  <select className="lr-select" value={selectedGapId || ''} onChange={(e) => setSelectedGapId(Number(e.target.value) || null)}>
                    <option value="">Select a skill gap analysis...</option>
                    {skillGaps.map((gap) => (
                      <option key={gap.id} value={gap.id}>
                        Analysis #{gap.id} — {gap.match_percentage != null ? `${gap.match_percentage}% match` : 'Pending'} — {formatDate(gap.created_at)}
                      </option>
                    ))}
                  </select>
                  <button type="button" className="lr-btn lr-btn-primary" onClick={handleGenerateEnhanced} disabled={!selectedGapId || generating}>
                    <Icon.Sparkles /> Generate Journey
                  </button>
                </div>
              </div>
            </section>
          ) : (
            <section className="lr-generate">
              <div className="lr-generate-card" style={{ borderLeftColor: '#2563eb' }}>
                <div className="lr-generate-left">
                  <div className="lr-generate-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Icon.Target /></div>
                  <div>
                    <h3>Run a Skill Gap Analysis First</h3>
                    <p>Generate a roadmap by first analyzing your skills against a job description</p>
                  </div>
                </div>
                <div className="lr-generate-right">
                  <button type="button" className="lr-btn lr-btn-primary" onClick={() => navigate('/career/skill-gap')}>
                    <Icon.ArrowRight /> Go to Skill Gap Analysis
                  </button>
                </div>
              </div>
            </section>
          )}

          {savedRoadmaps.length > 0 && (
            <section className="lr-saved-section">
              <div className="lr-saved-header">
                <h2>Your Learning Journeys</h2>
                <p>{savedRoadmaps.length} roadmap{savedRoadmaps.length !== 1 ? 's' : ''} created</p>
              </div>
              <div className="lr-saved-list">
                {savedRoadmaps.map((rm) => (
                  <div key={rm.id} className="lr-saved-card">
                    <div className="lr-saved-info">
                      <h4>{rm.career_goal || `Roadmap #${rm.id}`}</h4>
                      <span>{rm.total_hours}h total · {rm.estimated_weeks} weeks · {rm.status} · v{rm.version || 1}</span>
                    </div>
                    <div className="lr-saved-progress">
                      <div className="lr-mini-bar">
                        <div className="lr-mini-fill" style={{ width: `${rm.progress_percentage}%` }} />
                      </div>
                      <span>{rm.progress_percentage}%</span>
                    </div>
                    <div className="lr-saved-actions">
                      <button type="button" className="lr-btn lr-btn-ghost lr-btn-sm" onClick={async () => {
                        try {
                          const resp = await careerApi.getRoadmap(rm.id);
                          const roadmap = resp.data;
                          const phases = roadmap.phases ? JSON.parse(typeof roadmap.phases === 'string' ? roadmap.phases : JSON.stringify(roadmap.phases)) : [];
                          const dailyPlan = roadmap.daily_plan ? JSON.parse(typeof roadmap.daily_plan === 'string' ? roadmap.daily_plan : '{}') : {};
                          const tips = roadmap.mentor_tips ? JSON.parse(typeof roadmap.mentor_tips === 'string' ? roadmap.mentor_tips : '[]') : [];
                          const gapSummary = roadmap.skill_gap_summary ? JSON.parse(typeof roadmap.skill_gap_summary === 'string' ? roadmap.skill_gap_summary : '{}') : {};
                          setRoadmapData({
                            roadmap_id: rm.id,
                            career_goal: roadmap.career_goal || 'Software Engineer',
                            total_hours: roadmap.total_hours || 0,
                            estimated_weeks: roadmap.estimated_weeks || 0,
                            current_readiness: roadmap.current_readiness || 0,
                            target_readiness: roadmap.target_readiness || 85,
                            phases: phases,
                            daily_plan: dailyPlan,
                            mentor_tips: tips,
                            skill_gap_summary: gapSummary,
                            interview_readiness: roadmap.interview_readiness || 0,
                            coding_readiness: roadmap.coding_readiness || 0,
                          });
                          if (roadmap.completed_topics) {
                            setCompletedTopics(new Set(JSON.parse(roadmap.completed_topics)));
                          }
                        } catch {}
                      }}>View</button>
                      <button type="button" className="lr-btn lr-btn-danger lr-btn-sm" disabled={deleting === rm.id} onClick={() => handleDeleteRoadmap(rm.id)}>
                        {deleting === rm.id ? '...' : <Icon.Trash />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* Generating state */}
      {generating && (
        <div className="lr-loading" style={{ padding: '80px 0' }}>
          <Icon.Loader />
          <p>Building your personalized learning journey...</p>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>Analyzing skill gaps, dependencies, and career goals</span>
        </div>
      )}

      {/* Active Roadmap Dashboard */}
      {roadmapData && !generating && (
        <>
          {/* Career Goal Banner */}
          <section className="lr-goal-banner">
            <div className="lr-goal-content">
              <div className="lr-goal-icon"><Icon.Target /></div>
              <div className="lr-goal-text">
                <h2>Career Goal: {roadmapData.career_goal}</h2>
                <p>
                  {roadmapData.total_hours > 0
                    ? `${roadmapData.total_hours} hours · ${roadmapData.estimated_weeks} weeks · ${roadmapData.phases.length} phases`
                    : 'Generate a roadmap with a skill gap analysis to see estimated timeline'}
                </p>
              </div>
            </div>
            <div className="lr-goal-scores">
              <div className="lr-score-pill">
                <Icon.TrendUp />
                <span>{roadmapData.current_readiness}%</span>
                <label>Current</label>
              </div>
              <div className="lr-score-arrow">→</div>
              <div className="lr-score-pill lr-score-pill--target">
                <Icon.Star />
                <span>{roadmapData.target_readiness}%</span>
                <label>Target</label>
              </div>
            </div>
          </section>

          {/* Stats Row */}
          <section className="lr-stats-row">
            <div className="lr-stat-card">
              <div className="lr-stat-icon" style={{ background: '#eff6ff', color: '#2563eb' }}><Icon.Brain /></div>
              <div className="lr-stat-info">
                <span className="lr-stat-value">{getOverallProgress()}%</span>
                <span className="lr-stat-label">Overall Progress</span>
              </div>
              <div className="lr-stat-bar">
                <div className="lr-stat-bar-fill" style={{ width: `${getOverallProgress()}%`, background: '#2563eb' }} />
              </div>
            </div>
            <div className="lr-stat-card">
              <div className="lr-stat-icon" style={{ background: '#fef3c7', color: '#d97706' }}><Icon.Mic /></div>
              <div className="lr-stat-info">
                <span className="lr-stat-value">{roadmapData.interview_readiness}%</span>
                <span className="lr-stat-label">Interview Ready</span>
              </div>
              <div className="lr-stat-bar">
                <div className="lr-stat-bar-fill" style={{ width: `${roadmapData.interview_readiness}%`, background: '#d97706' }} />
              </div>
            </div>
            <div className="lr-stat-card">
              <div className="lr-stat-icon" style={{ background: '#f0fdf4', color: '#16a34a' }}><Icon.Code /></div>
              <div className="lr-stat-info">
                <span className="lr-stat-value">{roadmapData.coding_readiness}%</span>
                <span className="lr-stat-label">Coding Ready</span>
              </div>
              <div className="lr-stat-bar">
                <div className="lr-stat-bar-fill" style={{ width: `${roadmapData.coding_readiness}%`, background: '#16a34a' }} />
              </div>
            </div>
            <div className="lr-stat-card">
              <div className="lr-stat-icon" style={{ background: '#fdf2f8', color: '#db2777' }}><Icon.Flame /></div>
              <div className="lr-stat-info">
                <span className="lr-stat-value">{roadmapData.daily_plan?.streak_days || 0}</span>
                <span className="lr-stat-label">Day Streak</span>
              </div>
              <div className="lr-stat-bar">
                <div className="lr-stat-bar-fill" style={{ width: `${Math.min((roadmapData.daily_plan?.streak_days || 0) * 10, 100)}%`, background: '#db2777' }} />
              </div>
            </div>
          </section>

          {/* Daily Plan + Skill Gap */}
          <section className="lr-dual-row">
            <div className="lr-daily-card">
              <div className="lr-daily-header">
                <Icon.Zap />
                <h3>Today's Learning Plan</h3>
              </div>
              {roadmapData.daily_plan?.today_focus && roadmapData.daily_plan.today_focus !== 'Continue learning' && roadmapData.daily_plan?.needs_analysis !== true ? (
                <>
                  <div className="lr-daily-focus">
                    <span className="lr-daily-label">Focus Area</span>
                    <h4>{roadmapData.daily_plan.today_focus}</h4>
                  </div>
                  <div className="lr-daily-activities">
                    {(roadmapData.daily_plan?.activities || []).map((act, i) => (
                      <div key={i} className="lr-daily-activity">
                        <span className="lr-daily-num">{i + 1}</span>
                        <span>{act}</span>
                      </div>
                    ))}
                  </div>
                  <div className="lr-daily-footer">
                    <Icon.Clock />
                    <span>{roadmapData.daily_plan?.hours_today || 2} hours planned today</span>
                  </div>
                </>
              ) : (
                <div className="lr-daily-empty" style={{ padding: '20px 0', textAlign: 'center' }}>
                  <p style={{ color: 'var(--muted)', fontSize: 13, margin: '0 0 12px' }}>
                    Complete a skill gap analysis with a resume and job description to get a personalized daily plan with focus areas, activities, and time estimates.
                  </p>
                  <button type="button" className="lr-btn lr-btn-secondary" onClick={() => navigate('/career/skill-gap')} style={{ fontSize: 12, padding: '6px 14px' }}>
                    Run Skill Gap Analysis
                  </button>
                </div>
              )}
            </div>

            <div className="lr-gap-card">
              <div className="lr-gap-header">
                <Icon.Target />
                <h3>Skill Gap Summary</h3>
              </div>
              <div className="lr-gap-ring">
                <svg viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#e2e8f0" strokeWidth="8" />
                  <circle cx="60" cy="60" r="50" fill="none" stroke="#8b5cf6" strokeWidth="8"
                    strokeDasharray={314}
                    strokeDashoffset={314 - (314 * (roadmapData.skill_gap_summary?.match_percentage || 0)) / 100}
                    strokeLinecap="round" transform="rotate(-90 60 60)" />
                </svg>
                <span className="lr-gap-ring-value">{roadmapData.skill_gap_summary?.match_percentage || 0}%</span>
              </div>
              <div className="lr-gap-stats">
                <div className="lr-gap-stat">
                  <span className="lr-gap-dot" style={{ background: '#10b981' }} />
                  <span>{roadmapData.skill_gap_summary?.matched_count || 0} Matched</span>
                </div>
                <div className="lr-gap-stat">
                  <span className="lr-gap-dot" style={{ background: '#ef4444' }} />
                  <span>{roadmapData.skill_gap_summary?.missing_count || 0} Missing</span>
                </div>
                <div className="lr-gap-stat">
                  <span className="lr-gap-dot" style={{ background: '#f59e0b' }} />
                  <span>{roadmapData.skill_gap_summary?.priority_count || 0} Priority</span>
                </div>
              </div>
            </div>
          </section>

          {/* Phase Timeline */}
          <section className="lr-phases-section">
            <div className="lr-phases-header">
              <h2>Learning Phases</h2>
              <p>{(roadmapData.phases || []).length} phases · {(roadmapData.phases || []).reduce((a, p) => a + (p.topics || []).length, 0)} topics</p>
            </div>

            <div className="lr-phase-tabs">
              {(roadmapData.phases || []).map((phase, idx) => (
                <button key={idx} className={`lr-phase-tab ${activePhase === idx ? 'lr-phase-tab--active' : ''}`} onClick={() => setActivePhase(idx)}>
                  <span className="lr-phase-num">{phase.phase_number}</span>
                  <span className="lr-phase-tab-title">{phase.title}</span>
                  <div className="lr-phase-tab-bar">
                    <div className="lr-phase-tab-fill" style={{ width: `${getPhaseProgress(phase)}%` }} />
                  </div>
                </button>
              ))}
            </div>

            {(roadmapData.phases || []).length === 0 ? (
              <div className="lr-phase-empty" style={{ padding: '32px 20px', textAlign: 'center', background: 'var(--card)', borderRadius: 12, border: '1px dashed var(--border)' }}>
                <div style={{ width: 40, height: 40, margin: '0 auto 12px', color: 'var(--muted)' }}><Icon.Target /></div>
                <p style={{ color: 'var(--muted)', fontSize: 13, margin: '0 0 4px' }}>
                  No learning phases generated yet.
                </p>
                <p style={{ color: 'var(--muted)', fontSize: 12, margin: '0 0 16px' }}>
                  Upload a resume and job description, then run a skill gap analysis to generate a personalized learning roadmap with phases, topics, and resources.
                </p>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                  <button type="button" className="lr-btn lr-btn-secondary" onClick={() => navigate('/resume')} style={{ fontSize: 12, padding: '6px 14px' }}>
                    Upload Resume
                  </button>
                  <button type="button" className="lr-btn lr-btn-secondary" onClick={() => navigate('/career/job-descriptions')} style={{ fontSize: 12, padding: '6px 14px' }}>
                    Add Job Description
                  </button>
                </div>
              </div>
            ) : (
              <div className="lr-phase-detail">
                <div className="lr-phase-detail-header">
                  <div className="lr-phase-detail-info">
                    <h3>Phase {roadmapData.phases[activePhase].phase_number}: {roadmapData.phases[activePhase].title}</h3>
                    <p>{roadmapData.phases[activePhase].objective}</p>
                  </div>
                  <div className="lr-phase-detail-meta">
                    <span className="lr-badge" style={{ background: getPriorityColor(roadmapData.phases[activePhase].priority), color: '#fff' }}>
                      {roadmapData.phases[activePhase].priority}
                    </span>
                    <span className="lr-phase-meta-item"><Icon.Clock /> {roadmapData.phases[activePhase].estimated_hours}h</span>
                    <span className="lr-phase-meta-item"><Icon.Calendar /> {roadmapData.phases[activePhase].estimated_weeks}w</span>
                  </div>
                </div>

                <div className="lr-phase-progress-bar">
                  <div className="lr-phase-progress-fill" style={{ width: `${getPhaseProgress(roadmapData.phases[activePhase])}%` }} />
                  <span className="lr-phase-progress-text">{getPhaseProgress(roadmapData.phases[activePhase])}% complete</span>
                </div>

                {/* Milestone */}
                <div className="lr-milestone-banner">
                  <Icon.Star />
                  <span>Milestone: {roadmapData.phases[activePhase].milestone}</span>
                </div>

                {/* Topics */}
                <div className="lr-topics-list">
                  {(roadmapData.phases[activePhase]?.topics || []).map((topic, tIdx) => {
                    const isComplete = completedTopics.has(topic.name);
                    const isExpanded = expandedTopic === `${activePhase}-${tIdx}`;
                    return (
                      <div key={tIdx} className={`lr-topic-card ${isComplete ? 'lr-topic-card--done' : ''}`}>
                        <div className="lr-topic-header" onClick={() => setExpandedTopic(isExpanded ? null : `${activePhase}-${tIdx}`)}>
                          <button className="lr-topic-check" onClick={(e) => { e.stopPropagation(); toggleTopicComplete(topic.name); }}>
                            {isComplete ? <Icon.CheckCircle /> : <span className="lr-topic-check-empty" />}
                          </button>
                          <div className="lr-topic-info">
                            <h4>{topic.name}</h4>
                            <div className="lr-topic-tags">
                              <span className="lr-tag" style={{ background: getDifficultyColor(topic.difficulty) + '20', color: getDifficultyColor(topic.difficulty) }}>{topic.difficulty}</span>
                              <span className="lr-tag lr-tag--hours"><Icon.Clock /> {topic.estimated_hours}h</span>
                              {topic.prerequisites?.length > 0 && (
                                <span className="lr-tag lr-tag--prereq">Prereqs: {topic.prerequisites.join(', ')}</span>
                              )}
                            </div>
                          </div>
                          <span className={`lr-topic-chevron ${isExpanded ? 'lr-topic-chevron--open' : ''}`}>▼</span>
                        </div>

                        {isExpanded && (
                          <div className="lr-topic-expanded">
                            <p className="lr-topic-desc">{topic.description}</p>

                            {/* Resources */}
                            {topic.resources && (topic.resources.documentation?.length > 0 || topic.resources.videos?.length > 0) && (
                              <div className="lr-topic-section">
                                <h5>📚 Learning Resources</h5>
                                {(topic.resources.documentation || []).map((url, i) => (
                                  <a key={i} href={url.startsWith('http') ? url : '#'} target="_blank" rel="noopener noreferrer" className="lr-resource-link">
                                    <Icon.ExternalLink /> {url.split('/')[2]} — Documentation
                                  </a>
                                ))}
                                {(topic.resources.videos || []).map((vid, i) => (
                                  <div key={i} className="lr-resource-item">
                                    <Icon.Book /> {vid}
                                  </div>
                                ))}
                                {(topic.resources.practice_projects || []).map((proj, i) => (
                                  <div key={i} className="lr-resource-item lr-resource-item--project">
                                    <Icon.Code /> {proj}
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Interview Questions */}
                            {(topic.interview_questions || []).length > 0 && (
                              <div className="lr-topic-section">
                                <h5>🎤 Interview Questions</h5>
                                {(topic.interview_questions || []).map((q, i) => (
                                  <div key={i} className="lr-question-item">
                                    <span className="lr-q-num">Q{i + 1}</span>
                                    <span>{q}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Coding Problems */}
                            {(topic.coding_problems || []).length > 0 && (
                              <div className="lr-topic-section">
                                <h5>💻 Practice Problems</h5>
                                <div className="lr-coding-list">
                                  {(topic.coding_problems || []).map((p, i) => (
                                    <span key={i} className="lr-coding-chip">
                                      {typeof p === 'string' ? p : `${p.title} (${p.difficulty})`}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          {/* AI Mentor Tips */}
          {(roadmapData.mentor_tips || []).length > 0 && (
            <section className="lr-mentor-section">
              <div className="lr-mentor-header">
                <Icon.Sparkles />
                <h2>AI Mentor Recommendations</h2>
              </div>
              <div className="lr-mentor-grid">
                {(roadmapData.mentor_tips || []).map((tip, i) => (
                  <div key={i} className={`lr-mentor-card lr-mentor-card--${tip.type}`}>
                    <div className="lr-mentor-icon">{getTipIcon(tip.type)}</div>
                    <h4>{tip.title}</h4>
                    <p>{tip.message}</p>
                    {tip.action && tip.action_url && (
                      <button className="lr-btn lr-btn-ghost lr-btn-sm" onClick={() => navigate(tip.action_url!)}>
                        {tip.action} <Icon.ArrowRight />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
};

export default LearningRoadmapPage;
