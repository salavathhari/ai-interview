import {
  Activity,
  BarChart3,
  Brain,
  Calendar,
  Code2,
  GraduationCap,
  Lightbulb,
  Target,
  TrendingUp,
  Trophy,
  Zap,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from 'recharts';
import { analyticsApi, getAccessToken } from '../services/api';
import './AnalyticsPage.css';

type TopicMetric = { topic: string; average_score: number; question_count: number };
type TrendPoint = { date: string; score: number };
type SkillHeatmap = { skill: string; category: string; proficiency: number; trend: string; evidence_count: number };
type CodingData = {
  total_sessions: number; total_submissions: number; avg_correctness: number;
  avg_runtime_ms: number; avg_ai_score: number;
  language_distribution: Record<string, number>;
  difficulty_distribution: Record<string, number>;
  topic_performance: TopicMetric[];
  recent_trends: TrendPoint[];
  improvement_rate: number;
};
type SkillData = {
  total_skills: number; skills_learned: number; skills_mastered: number;
  weak_skills: SkillHeatmap[]; strong_skills: SkillHeatmap[];
  heatmap: SkillHeatmap[]; improvement_skills: SkillHeatmap[]; declining_skills: SkillHeatmap[];
};
type LearningData = {
  total_hours: number; completed_topics: number; in_progress_topics: number;
  total_topics: number; completion_rate: number; streak_days: number;
  daily_hours: TrendPoint[]; weekly_hours: TrendPoint[]; monthly_hours: TrendPoint[];
  roadmap_completion: number; progress_trend: TrendPoint[];
};
type CareerData = {
  overall_readiness: number; resume_match: number; ats_score: number;
  interview_readiness: number; coding_readiness: number; learning_progress: number;
  skill_gap_score: number; role_readiness: Record<string, number>;
  company_readiness: Record<string, number>;
  readiness_trend: TrendPoint[]; improvement_rate: number;
};
type TopicData = {
  topic_scores: TopicMetric[]; weak_topics: TopicMetric[];
  strong_topics: TopicMetric[]; topic_trends: Record<string, TrendPoint[]>;
  improvement_topics: TopicMetric[]; declining_topics: TopicMetric[];
};
type HistoryData = {
  daily: TrendPoint[]; weekly: TrendPoint[]; monthly: TrendPoint[];
  career_timeline: TrendPoint[]; interview_timeline: TrendPoint[];
  coding_timeline: TrendPoint[]; learning_timeline: TrendPoint[];
};
type PredictionData = {
  predicted_readiness: number; predicted_interview_success: number;
  predicted_coding_success: number; estimated_time_to_target: string;
  learning_completion_forecast: string; interview_improvement_forecast: string;
  confidence: number; factors: string[];
};
type RecommendationData = {
  next_skill: string | null; next_interview_topic: string | null;
  next_coding_topic: string | null; next_mini_project: string | null;
  revision_topics: string[]; priority_actions: { action: string; reason: string; priority: string }[];
};

type AnalyticsPayload = {
  average_score: number; total_interviews: number;
  weak_topics: TopicMetric[]; strong_topics: TopicMetric[];
  progress_trends: TrendPoint[]; role_distribution: Record<string, number>;
  avg_accuracy: number; avg_communication: number; avg_confidence: number;
  avg_completeness: number; average_response_speed: number;
  hesitation_score: number; pressure_handling: number;
  confidence_estimation: number; improvement_rate: number;
  coding: CodingData; skills: SkillData; learning: LearningData;
  career: CareerData; topics: TopicData; history: HistoryData;
  predictions: PredictionData; recommendations: RecommendationData;
};

const clamp = (v: number) => Math.max(0, Math.min(100, Math.round(v)));

const TABS = [
  { key: 'overview', label: 'Overview', icon: Activity },
  { key: 'interview', label: 'Interview', icon: Brain },
  { key: 'coding', label: 'Coding', icon: Code2 },
  { key: 'skills', label: 'Skills', icon: Zap },
  { key: 'learning', label: 'Learning', icon: GraduationCap },
  { key: 'career', label: 'Career', icon: Trophy },
  { key: 'topics', label: 'Topics', icon: BarChart3 },
  { key: 'predictions', label: 'Predictions', icon: Lightbulb },
] as const;

type TabKey = typeof TABS[number]['key'];

const AnalyticsPage = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<TabKey>('overview');

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { navigate('/login'); return; }
    analyticsApi.getDashboard()
      .then(res => setAnalytics(res.data))
      .catch(() => setError('Unable to load analytics.'))
      .finally(() => setLoading(false));
  }, [navigate]);

  if (loading) return <div className="analytics-state">Loading analytics…</div>;
  if (error) return <div className="analytics-state">{error}</div>;
  if (!analytics) return <div className="analytics-state">No data available</div>;

  return (
    <div className="analytics-shell">
      <header className="analytics-header">
        <div>
          <p className="analytics-eyebrow">Business Intelligence</p>
          <h1>Career Analytics Engine</h1>
          <span>Complete performance intelligence across interviews, coding, skills, learning, and career readiness.</span>
        </div>
        <button type="button" onClick={() => navigate('/dashboard')}>Dashboard</button>
      </header>

      {/* Tab Bar */}
      <nav className="analytics-tabs">
        {TABS.map(tab => (
          <button key={tab.key} className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}>
            <tab.icon size={15} />{tab.label}
          </button>
        ))}
      </nav>

      {/* Summary Cards */}
      <section className="analytics-summary">
        <article>
          <Target size={18} />
          <span>Avg Interview</span>
          <strong>{analytics.average_score.toFixed(1)}/10</strong>
        </article>
        <article>
          <Code2 size={18} />
          <span>Coding Score</span>
          <strong>{analytics.coding?.avg_correctness?.toFixed(0) ?? 0}%</strong>
        </article>
        <article>
          <Zap size={18} />
          <span>Skills</span>
          <strong>{analytics.skills?.skills_learned ?? 0}/{analytics.skills?.total_skills ?? 0}</strong>
        </article>
        <article>
          <GraduationCap size={18} />
          <span>Learning</span>
          <strong>{analytics.learning?.total_hours?.toFixed(0) ?? 0}h</strong>
        </article>
        <article>
          <Trophy size={18} />
          <span>Readiness</span>
          <strong>{analytics.career?.overall_readiness?.toFixed(0) ?? 0}%</strong>
        </article>
        <article>
          <TrendingUp size={18} />
          <span>Improvement</span>
          <strong>{analytics.improvement_rate.toFixed(1)}%</strong>
        </article>
      </section>

      {/* Tab Content */}
      <main className="analytics-content">
        {activeTab === 'overview' && <OverviewTab data={analytics} />}
        {activeTab === 'interview' && <InterviewTab data={analytics} />}
        {activeTab === 'coding' && <CodingTab data={analytics} />}
        {activeTab === 'skills' && <SkillsTab data={analytics} />}
        {activeTab === 'learning' && <LearningTab data={analytics} />}
        {activeTab === 'career' && <CareerTab data={analytics} />}
        {activeTab === 'topics' && <TopicsTab data={analytics} />}
        {activeTab === 'predictions' && <PredictionsTab data={analytics} />}
      </main>
    </div>
  );
};

// ─── Overview Tab ─────────────────────────────────────────────────────────

const OverviewTab = ({ data }: { data: AnalyticsPayload }) => {
  const progressData = useMemo(() => {
    const trends = data.progress_trends ?? [];
    if (!trends.length) return [{ label: 'S1', score: 0 }];
    return trends.map((t, i) => ({
      label: new Date(t.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) || `S${i + 1}`,
      score: Number(t.score.toFixed(1)),
    }));
  }, [data]);

  const radarData = useMemo(() => [
    { skill: 'Accuracy', score: clamp(data.avg_accuracy * 10) },
    { skill: 'Communication', score: clamp(data.avg_communication * 10) },
    { skill: 'Confidence', score: clamp(data.avg_confidence * 10) },
    { skill: 'Completeness', score: clamp(data.avg_completeness * 10) },
    { skill: 'Pressure', score: clamp(data.pressure_handling) },
  ], [data]);

  const heatmapCells = useMemo(() => {
    const trends = data.progress_trends ?? [];
    return Array.from({ length: 35 }, (_, i) => {
      const t = trends[i % Math.max(trends.length, 1)];
      const score = t ? clamp(t.score * 10) : 0;
      return { id: i, score, level: score >= 80 ? 4 : score >= 65 ? 3 : score >= 45 ? 2 : score > 0 ? 1 : 0 };
    });
  }, [data]);

  return (
    <div className="tab-grid">
      <section className="analytics-panel progress-panel">
        <div className="panel-title"><div><h2>Progress Over Time</h2><p>Session score trend</p></div><Activity size={20} /></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={progressData} margin={{ top: 8, right: 16, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 10]} tickLine={false} axisLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel radar-panel">
        <div className="panel-title"><div><h2>Skill Distribution</h2><p>Radar view of interview dimensions</p></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} outerRadius="72%">
              <PolarGrid stroke="#dbe3ee" />
              <PolarAngleAxis dataKey="skill" tick={{ fill: '#475467', fontSize: 12 }} />
              <Radar dataKey="score" stroke="#0f766e" fill="#14b8a6" fillOpacity={0.28} strokeWidth={2} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel weak-panel">
        <div className="panel-title"><div><h2>Weak Topics</h2><p>Priority areas to practice</p></div></div>
        <div className="weak-topic-grid">
          {(data.weak_topics ?? []).slice(0, 4).map((t, i) => (
            <article key={t.topic + i} className="weak-topic-card">
              <div><h3>{t.topic}</h3></div>
              <strong>{clamp(t.average_score * 10)}%</strong>
              <div className="topic-meter"><div style={{ width: `${clamp(t.average_score * 10)}%` }} /></div>
              <p>{t.question_count} questions</p>
            </article>
          ))}
        </div>
      </section>

      <section className="analytics-panel heatmap-panel">
        <div className="panel-title"><div><h2>Activity Heatmap</h2><p>Recent performance intensity</p></div></div>
        <div className="heatmap-grid">
          {heatmapCells.map(c => (
            <span key={c.id} className={`heat-cell level-${c.level}`} title={`${c.score}%`} />
          ))}
        </div>
        <div className="heatmap-legend">
          <span>Lower</span><i className="level-1" /><i className="level-2" /><i className="level-3" /><i className="level-4" /><span>Higher</span>
        </div>
      </section>

      {/* Predictions Summary */}
      {data.predictions && (
        <section className="analytics-panel predictions-summary-panel">
          <div className="panel-title"><div><h2>AI Predictions</h2><p>Forecasted performance</p></div><Brain size={20} /></div>
          <div className="prediction-grid">
            <div className="pred-card">
              <span>Predicted Readiness</span>
              <strong>{data.predictions.predicted_readiness.toFixed(0)}%</strong>
            </div>
            <div className="pred-card">
              <span>Interview Success</span>
              <strong>{data.predictions.predicted_interview_success.toFixed(0)}%</strong>
            </div>
            <div className="pred-card">
              <span>Coding Success</span>
              <strong>{data.predictions.predicted_coding_success.toFixed(0)}%</strong>
            </div>
            <div className="pred-card">
              <span>Time to Target</span>
              <strong>{data.predictions.estimated_time_to_target}</strong>
            </div>
          </div>
        </section>
      )}

      {/* Recommendations Summary */}
      {data.recommendations?.priority_actions?.length > 0 && (
        <section className="analytics-panel recs-summary-panel">
          <div className="panel-title"><div><h2>Priority Actions</h2><p>What to do next</p></div><Lightbulb size={20} /></div>
          <div className="rec-list">
            {data.recommendations.priority_actions.map((a, i) => (
              <div key={i} className={`rec-item priority-${a.priority}`}>
                <span className={`priority-badge ${a.priority}`}>{a.priority}</span>
                <div><strong>{a.action}</strong><p>{a.reason}</p></div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

// ─── Interview Tab ────────────────────────────────────────────────────────

const InterviewTab = ({ data }: { data: AnalyticsPayload }) => {
  const topicData = useMemo(() =>
    (data.topics?.topic_scores ?? []).map(t => ({ name: t.topic, score: clamp(t.average_score * 10) })),
    [data]);

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Topic Performance</h2><p>Average score per topic</p></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topicData} margin={{ top: 8, right: 16, bottom: 0, left: -18 }}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {topicData.map((entry, i) => (
                  <Cell key={i} fill={entry.score >= 70 ? '#10b981' : entry.score >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Interview Metrics</h2><p>Quality dimensions</p></div></div>
        <div className="metric-grid-5">
          {[
            { label: 'Accuracy', value: data.avg_accuracy, max: 10 },
            { label: 'Communication', value: data.avg_communication, max: 10 },
            { label: 'Confidence', value: data.avg_confidence, max: 10 },
            { label: 'Completeness', value: data.avg_completeness, max: 10 },
            { label: 'Pressure Handling', value: data.pressure_handling, max: 100 },
          ].map(m => (
            <div key={m.label} className="metric-mini">
              <span>{m.label}</span>
              <strong>{m.value.toFixed(1)}</strong>
              <div className="mini-bar"><div style={{ width: `${clamp((m.value / m.max) * 100)}%` }} /></div>
            </div>
          ))}
        </div>
      </section>

      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>Role Distribution</h2><p>Interviews by target role</p></div></div>
        <div className="role-grid">
          {Object.entries(data.role_distribution ?? {}).map(([role, count]) => (
            <div key={role} className="role-card">
              <strong>{count}</strong>
              <span>{role}</span>
            </div>
          ))}
          {Object.keys(data.role_distribution ?? {}).length === 0 && <p className="empty-hint">No interview data yet</p>}
        </div>
      </section>
    </div>
  );
};

// ─── Coding Tab ───────────────────────────────────────────────────────────

const CodingTab = ({ data }: { data: AnalyticsPayload }) => {
  const c = data.coding;
  if (!c) return <div className="analytics-state">No coding data</div>;

  const langData = Object.entries(c.language_distribution ?? {}).map(([name, value]) => ({ name, value }));
  const diffData = Object.entries(c.difficulty_distribution ?? {}).map(([name, value]) => ({ name, value }));
  const topicData = c.topic_performance?.map(t => ({ name: t.topic, score: clamp(t.average_score) })) ?? [];

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Coding Overview</h2></div></div>
        <div className="metric-grid-3">
          <div className="metric-mini"><span>Sessions</span><strong>{c.total_sessions}</strong></div>
          <div className="metric-mini"><span>Submissions</span><strong>{c.total_submissions}</strong></div>
          <div className="metric-mini"><span>Avg Correctness</span><strong>{c.avg_correctness}%</strong></div>
          <div className="metric-mini"><span>Avg Runtime</span><strong>{c.avg_runtime_ms}ms</strong></div>
          <div className="metric-mini"><span>AI Score</span><strong>{c.avg_ai_score}/10</strong></div>
          <div className="metric-mini"><span>Improvement</span><strong>{c.improvement_rate}%</strong></div>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Language Usage</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={langData}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Topic Performance</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topicData}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {topicData.map((e, i) => (
                  <Cell key={i} fill={e.score >= 70 ? '#10b981' : e.score >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>Difficulty Distribution</h2></div></div>
        <div className="diff-grid">
          {diffData.map(d => (
            <div key={d.name} className={`diff-badge diff-${d.name.toLowerCase()}`}>
              <strong>{d.value}</strong><span>{d.name}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

// ─── Skills Tab ───────────────────────────────────────────────────────────

const SkillsTab = ({ data }: { data: AnalyticsPayload }) => {
  const s = data.skills;
  if (!s) return <div className="analytics-state">No skill data</div>;

  const COLORS = { programming: '#2563eb', framework: '#8b5cf6', database: '#0ea5e9', cloud: '#f59e0b', devops: '#10b981', tool: '#6b7280', other: '#d1d5db' };

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Skill Overview</h2></div></div>
        <div className="metric-grid-3">
          <div className="metric-mini"><span>Total Skills</span><strong>{s.total_skills}</strong></div>
          <div className="metric-mini"><span>Learned</span><strong>{s.skills_learned}</strong></div>
          <div className="metric-mini"><span>Mastered</span><strong>{s.skills_mastered}</strong></div>
        </div>
      </section>

      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>Skill Heatmap</h2><p>Proficiency by category</p></div></div>
        <div className="skill-heatmap-grid">
          {(s.heatmap ?? []).map(sk => (
            <div key={sk.skill} className="skill-heat-cell" title={`${sk.skill}: ${sk.proficiency}%`}>
              <span className="skill-name">{sk.skill}</span>
              <div className="skill-bar" style={{ backgroundColor: COLORS[sk.category as keyof typeof COLORS] ?? '#d1d5db' }}>
                <div className="skill-fill" style={{ width: `${sk.proficiency}%`, backgroundColor: COLORS[sk.category as keyof typeof COLORS] ?? '#d1d5db' }} />
              </div>
              <span className="skill-pct">{sk.proficiency.toFixed(0)}%</span>
              <span className={`trend-badge trend-${sk.trend}`}>{sk.trend}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Weak Skills</h2></div></div>
        <div className="skill-list">
          {(s.weak_skills ?? []).map(sk => (
            <div key={sk.skill} className="skill-row weak">
              <span>{sk.skill}</span><strong>{sk.proficiency.toFixed(0)}%</strong>
            </div>
          ))}
          {(!s.weak_skills || s.weak_skills.length === 0) && <p className="empty-hint">No weak skills</p>}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Strong Skills</h2></div></div>
        <div className="skill-list">
          {(s.strong_skills ?? []).map(sk => (
            <div key={sk.skill} className="skill-row strong">
              <span>{sk.skill}</span><strong>{sk.proficiency.toFixed(0)}%</strong>
            </div>
          ))}
          {(!s.strong_skills || s.strong_skills.length === 0) && <p className="empty-hint">No strong skills yet</p>}
        </div>
      </section>
    </div>
  );
};

// ─── Learning Tab ─────────────────────────────────────────────────────────

const LearningTab = ({ data }: { data: AnalyticsPayload }) => {
  const l = data.learning;
  if (!l) return <div className="analytics-state">No learning data</div>;

  const dailyData = (l.daily_hours ?? []).map(d => ({
    label: new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' }),
    hours: d.score,
  }));

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Learning Overview</h2></div></div>
        <div className="metric-grid-3">
          <div className="metric-mini"><span>Total Hours</span><strong>{l.total_hours}</strong></div>
          <div className="metric-mini"><span>Completed</span><strong>{l.completed_topics}/{l.total_topics}</strong></div>
          <div className="metric-mini"><span>In Progress</span><strong>{l.in_progress_topics}</strong></div>
          <div className="metric-mini"><span>Completion Rate</span><strong>{l.completion_rate}%</strong></div>
          <div className="metric-mini"><span>Roadmap</span><strong>{l.roadmap_completion}%</strong></div>
          <div className="metric-mini"><span>Streak</span><strong>{l.streak_days} days</strong></div>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Daily Learning Hours</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={dailyData}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="hours" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>Weekly Trend</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={(l.weekly_hours ?? []).map(w => ({
              label: new Date(w.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
              hours: w.score,
            }))}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey="hours" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
};

// ─── Career Tab ───────────────────────────────────────────────────────────

const CareerTab = ({ data }: { data: AnalyticsPayload }) => {
  const c = data.career;
  if (!c) return <div className="analytics-state">No career data</div>;

  const components = [
    { label: 'Resume Match', value: c.resume_match, weight: '20%' },
    { label: 'ATS Score', value: c.ats_score, weight: '10%' },
    { label: 'Interview', value: c.interview_readiness, weight: '15%' },
    { label: 'Coding', value: c.coding_readiness, weight: '10%' },
    { label: 'Learning', value: c.learning_progress, weight: '10%' },
    { label: 'Skill Gap', value: c.skill_gap_score, weight: '20%' },
  ];

  const roleData = Object.entries(c.role_readiness ?? {}).map(([name, value]) => ({ name, value }));
  const companyData = Object.entries(c.company_readiness ?? {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Overall Readiness</h2></div></div>
        <div className="readiness-big">
          <div className="readiness-ring">
            <svg viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle cx="60" cy="60" r="52" fill="none" stroke="#2563eb" strokeWidth="8"
                strokeDasharray={`${(c.overall_readiness / 100) * 326.7} 326.7`}
                strokeLinecap="round" transform="rotate(-90 60 60)" />
            </svg>
            <span>{c.overall_readiness.toFixed(0)}%</span>
          </div>
          <p>Career Readiness Score</p>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Component Breakdown</h2></div></div>
        <div className="component-list">
          {components.map(comp => (
            <div key={comp.label} className="comp-row">
              <span>{comp.label} <small>({comp.weight})</small></span>
              <div className="comp-bar"><div style={{ width: `${comp.value}%` }} /></div>
              <strong>{comp.value.toFixed(0)}%</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Role Readiness</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={roleData} layout="vertical">
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={100} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {roleData.map((e, i) => (
                  <Cell key={i} fill={e.value >= 70 ? '#10b981' : e.value >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Company Readiness</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={companyData} layout="vertical">
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={100} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {companyData.map((e, i) => (
                  <Cell key={i} fill={e.value >= 70 ? '#10b981' : e.value >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>Readiness Trend</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={(c.readiness_trend ?? []).map(t => ({
              date: new Date(t.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
              score: t.score,
            }))}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
};

// ─── Topics Tab ───────────────────────────────────────────────────────────

const TopicsTab = ({ data }: { data: AnalyticsPayload }) => {
  const t = data.topics;
  if (!t) return <div className="analytics-state">No topic data</div>;

  const topicData = (t.topic_scores ?? []).map(s => ({ name: s.topic, score: clamp(s.average_score * 10) }));

  return (
    <div className="tab-grid">
      <section className="analytics-panel full-width">
        <div className="panel-title"><div><h2>All Topic Scores</h2></div></div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topicData}>
              <CartesianGrid stroke="#e6ebf2" strokeDasharray="4 4" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {topicData.map((e, i) => (
                  <Cell key={i} fill={e.score >= 70 ? '#10b981' : e.score >= 50 ? '#f59e0b' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Weak Topics</h2></div></div>
        <div className="skill-list">
          {(t.weak_topics ?? []).map(s => (
            <div key={s.topic} className="skill-row weak">
              <span>{s.topic}</span><strong>{clamp(s.average_score * 10)}%</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Strong Topics</h2></div></div>
        <div className="skill-list">
          {(t.strong_topics ?? []).map(s => (
            <div key={s.topic} className="skill-row strong">
              <span>{s.topic}</span><strong>{clamp(s.average_score * 10)}%</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Improving</h2></div></div>
        <div className="skill-list">
          {(t.improvement_topics ?? []).map(s => (
            <div key={s.topic} className="skill-row improving">
              <span>{s.topic}</span><strong>{clamp(s.average_score * 10)}%</strong>
            </div>
          ))}
          {(!t.improvement_topics || t.improvement_topics.length === 0) && <p className="empty-hint">No improving topics yet</p>}
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Declining</h2></div></div>
        <div className="skill-list">
          {(t.declining_topics ?? []).map(s => (
            <div key={s.topic} className="skill-row declining">
              <span>{s.topic}</span><strong>{clamp(s.average_score * 10)}%</strong>
            </div>
          ))}
          {(!t.declining_topics || t.declining_topics.length === 0) && <p className="empty-hint">No declining topics</p>}
        </div>
      </section>
    </div>
  );
};

// ─── Predictions Tab ─────────────────────────────────────────────────────

const PredictionsTab = ({ data }: { data: AnalyticsPayload }) => {
  const p = data.predictions;
  const r = data.recommendations;
  if (!p) return <div className="analytics-state">No prediction data</div>;

  return (
    <div className="tab-grid">
      <section className="analytics-panel">
        <div className="panel-title"><div><h2>AI Predictions</h2><p>Forecasted performance based on trends</p></div><Brain size={20} /></div>
        <div className="prediction-full-grid">
          <div className="pred-card large">
            <span>Predicted Readiness</span>
            <strong>{p.predicted_readiness.toFixed(0)}%</strong>
            <small>Confidence: {p.confidence.toFixed(0)}%</small>
          </div>
          <div className="pred-card large">
            <span>Interview Success</span>
            <strong>{p.predicted_interview_success.toFixed(0)}%</strong>
          </div>
          <div className="pred-card large">
            <span>Coding Success</span>
            <strong>{p.predicted_coding_success.toFixed(0)}%</strong>
          </div>
          <div className="pred-card large">
            <span>Time to Target</span>
            <strong>{p.estimated_time_to_target}</strong>
          </div>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Forecasts</h2></div></div>
        <div className="forecast-list">
          <div className="forecast-item">
            <GraduationCap size={16} />
            <div><strong>Learning Completion</strong><p>{p.learning_completion_forecast}</p></div>
          </div>
          <div className="forecast-item">
            <Brain size={16} />
            <div><strong>Interview Improvement</strong><p>{p.interview_improvement_forecast}</p></div>
          </div>
        </div>
      </section>

      <section className="analytics-panel">
        <div className="panel-title"><div><h2>Key Factors</h2></div></div>
        <div className="factor-list">
          {(p.factors ?? []).map((f, i) => (
            <div key={i} className="factor-item"><Lightbulb size={14} /><span>{f}</span></div>
          ))}
        </div>
      </section>

      {r && (
        <section className="analytics-panel full-width">
          <div className="panel-title"><div><h2>Recommendations</h2><p>What to do next and why</p></div></div>
          <div className="rec-full-grid">
            {r.next_skill && (
              <div className="rec-card">
                <Zap size={18} />
                <h3>Next Skill</h3>
                <strong>{r.next_skill}</strong>
                <p>Missing from your target role requirements</p>
              </div>
            )}
            {r.next_interview_topic && (
              <div className="rec-card">
                <Brain size={18} />
                <h3>Interview Focus</h3>
                <strong>{r.next_interview_topic}</strong>
                <p>Weakest area from recent interviews</p>
              </div>
            )}
            {r.next_coding_topic && (
              <div className="rec-card">
                <Code2 size={18} />
                <h3>Coding Focus</h3>
                <strong>{r.next_coding_topic}</strong>
                <p>Needs more practice</p>
              </div>
            )}
            {r.next_mini_project && (
              <div className="rec-card">
                <Calendar size={18} />
                <h3>Mini Project</h3>
                <strong>{r.next_mini_project}</strong>
                <p>Build something practical</p>
              </div>
            )}
          </div>
          {r.revision_topics?.length > 0 && (
            <div className="revision-section">
              <h3>Revision Topics</h3>
              <div className="revision-tags">
                {r.revision_topics.map((t, i) => (
                  <span key={i} className="revision-tag">{t}</span>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default AnalyticsPage;
