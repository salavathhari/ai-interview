import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeApi, interviewApi, analyticsApi } from '../services/api';
import {
  Plus, Download, Mic, FileText, Sparkles, BarChart3, Brain,
  Users, TrendingUp, AlertTriangle, Star, Play, Upload,
  ChevronRight, Calendar, Loader2
} from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [resumes, setResumes] = useState<any[]>([]);
    const [interviews, setInterviews] = useState<any[]>([]);
    const [analytics, setAnalytics] = useState<any>(null);
    const [role, setRole] = useState('');
    const [metricsLoading, setMetricsLoading] = useState(true);
    const navigate = useNavigate();

    const performancePoints = useMemo(() => {
        const series = interviews
            .slice(0, 8)
            .map((item) => (item.score !== null ? Math.round(item.score * 10) : 0))
            .reverse();
        if (series.length === 0) return '0,120 320,120';
        const maxValue = Math.max(100, ...series);
        return series
            .map((value, index) => {
                const x = (index / Math.max(series.length - 1, 1)) * 320;
                const y = 120 - (value / maxValue) * 110;
                return `${x.toFixed(1)},${y.toFixed(1)}`;
            })
            .join(' ');
    }, [interviews]);

    const skillBreakdown = useMemo(() => {
        const defaultSkills = [
            { label: 'Python', value: 78 },
            { label: 'SQL', value: 62 },
            { label: 'DSA', value: 54 },
            { label: 'System Design', value: 46 }
        ];
        const analyticsSkills = analytics?.skill_breakdown || analytics?.skills;
        if (!analyticsSkills) return defaultSkills;
        return Object.entries(analyticsSkills)
            .slice(0, 4)
            .map(([label, value]: any) => ({ label, value: Math.round(Number(value) * 10) }))
            .filter((item: any) => !Number.isNaN(item.value));
    }, [analytics]);

    const weakestTopic = analytics?.weakest_topic || analytics?.weak_topics?.[0]?.topic || 'Communication';
    const bestSkill = analytics?.best_skill || analytics?.strong_topics?.[0]?.topic || 'Python';

    useEffect(() => {
        loadResumes();
        loadInterviews();
        loadAnalytics();
    }, []);

    const loadResumes = async () => {
        try {
            const resp = await resumeApi.getMyResumes();
            setResumes(resp.data);
        } catch (error) {
            console.error(error);
        }
    };

    const loadInterviews = async () => {
        try {
            const resp = await interviewApi.getMyInterviews();
            setInterviews(resp.data);
        } catch (error) {
            console.error(error);
        }
    };

    const loadAnalytics = async () => {
        try {
            const resp = await analyticsApi.getDashboard();
            setAnalytics(resp.data);
        } catch (error) {
            console.error(error);
        } finally {
            setMetricsLoading(false);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            await resumeApi.upload(formData);
            loadResumes();
            setFile(null);
        } catch (error) {
            console.error(error);
        }
    };

    const startInterview = async () => {
        if (!role) return;
        try {
            const resp = await interviewApi.create({ role });
            navigate(`/interview/${resp.data.id}`);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="dashboard-page">
            <header className="dashboard-header">
                <div>
                    <h1>Dashboard</h1>
                    <p>Track your interview performance and launch new sessions.</p>
                </div>
                <div className="header-actions">
                    <button type="button" className="ghost" onClick={() => navigate('/career/readiness')}>
                        <Download size={15} /> Export Report
                    </button>
                    <button type="button" className="solid" onClick={() => navigate('/interview-setup')}>
                        <Plus size={15} /> New Interview
                    </button>
                </div>
            </header>

            {/* Quick Actions */}
            <section className="quick-actions">
                <button type="button" className="quick-action-card" onClick={() => navigate('/interview-setup')}>
                    <div className="quick-action-icon"><Mic size={20} /></div>
                    <div className="quick-action-text">
                        <h3>Start Interview</h3>
                        <p>Begin a new mock session</p>
                    </div>
                </button>
                <button type="button" className="quick-action-card" onClick={() => navigate('/career/ats-report')}>
                    <div className="quick-action-icon"><FileText size={20} /></div>
                    <div className="quick-action-text">
                        <h3>ATS Analysis</h3>
                        <p>Check resume compatibility</p>
                    </div>
                </button>
                <button type="button" className="quick-action-card" onClick={() => navigate('/career/resume-optimizer')}>
                    <div className="quick-action-icon"><Sparkles size={20} /></div>
                    <div className="quick-action-text">
                        <h3>Optimize Resume</h3>
                        <p>Improve ATS compatibility</p>
                    </div>
                </button>
                <button type="button" className="quick-action-card" onClick={() => navigate('/career/skill-gap')}>
                    <div className="quick-action-icon"><BarChart3 size={20} /></div>
                    <div className="quick-action-text">
                        <h3>Skill Gap</h3>
                        <p>Identify improvement areas</p>
                    </div>
                </button>
                <button type="button" className="quick-action-card" onClick={() => navigate('/ml-insights')}>
                    <div className="quick-action-icon"><Brain size={20} /></div>
                    <div className="quick-action-text">
                        <h3>ML Insights</h3>
                        <p>AI-powered analysis</p>
                    </div>
                </button>
            </section>

            {/* Metrics */}
            <section className="metric-grid">
                {metricsLoading ? (
                    <>
                        {[1, 2, 3, 4].map((i) => (
                            <article key={i} className="metric-card metric-card--loading">
                                <div className="metric-icon"><Skeleton width={40} height={40} variant="rect" /></div>
                                <Skeleton width="55%" height={12} />
                                <Skeleton width="40%" height={32} variant="rect" />
                                <Skeleton width="70%" height={12} />
                            </article>
                        ))}
                    </>
                ) : (
                    <>
                        <article className="metric-card">
                            <div className="metric-icon"><Users size={20} /></div>
                            <p>Total Interviews</p>
                            <h3>{analytics?.total_interviews ?? interviews.length}</h3>
                            <span>Sessions completed</span>
                        </article>
                        <article className="metric-card">
                            <div className="metric-icon"><TrendingUp size={20} /></div>
                            <p>Average Score</p>
                            <h3>{analytics ? `${analytics.average_score.toFixed(1)}%` : '0.0%'}</h3>
                            <span>Across all rounds</span>
                        </article>
                        <article className="metric-card">
                            <div className="metric-icon"><AlertTriangle size={20} /></div>
                            <p>Weakest Topic</p>
                            <h3>{weakestTopic}</h3>
                            <span>Priority to improve</span>
                        </article>
                        <article className="metric-card">
                            <div className="metric-icon"><Star size={20} /></div>
                            <p>Best Skill</p>
                            <h3>{bestSkill}</h3>
                            <span>Highest confidence area</span>
                        </article>
                    </>
                )}
            </section>

            {/* Charts */}
            <section className="chart-grid">
                <div className="chart-card">
                    <div className="chart-header">
                        <h2>Performance Graph</h2>
                        <span>Interview score over time</span>
                    </div>
                    <svg viewBox="0 0 320 140" className="line-chart" aria-hidden="true">
                        <polyline points="0,120 320,120" className="chart-axis" />
                        <polyline points={performancePoints} className="chart-line" />
                    </svg>
                    <div className="chart-footer">
                        {interviews.slice(0, 4).map((item) => (
                            <span key={item.id}>{new Date(item.started_at).toLocaleDateString()}</span>
                        ))}
                    </div>
                </div>
                <div className="chart-card">
                    <div className="chart-header">
                        <h2>Skill Breakdown</h2>
                        <span>Core competency scores</span>
                    </div>
                    <div className="bar-chart">
                        {skillBreakdown.map((skill) => (
                            <div className="bar-row" key={skill.label}>
                                <span>{skill.label}</span>
                                <div className="bar">
                                    <div className="bar-fill" style={{ width: `${Math.min(skill.value, 100)}%` }} />
                                </div>
                                <strong>{Math.min(skill.value, 100)}%</strong>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Action Panels */}
            <div className="section-divider"><h2>Quick Setup</h2></div>
            <section className="dashboard-grid">
                <div className="panel">
                    <div className="panel-header">
                        <h2>Start Mock Interview</h2>
                        <p>Resume required to unlock adaptive sessions.</p>
                    </div>
                    <div className="panel-body">
                        <label className="input-field">
                            <span>Target Role</span>
                            <input
                                type="text"
                                placeholder="e.g. Frontend Developer"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && startInterview()}
                            />
                        </label>
                        <button onClick={startInterview} disabled={!role} className="solid">
                            <Play size={15} /> Start Adaptive Session
                        </button>
                        {resumes.length === 0 && (
                            <p className="alert">Upload a resume first to unlock adaptive interviews.</p>
                        )}
                    </div>
                </div>

                <div className="panel">
                    <div className="panel-header">
                        <h2>Manage Resumes</h2>
                        <p>Upload a PDF or DOCX to personalize questions.</p>
                    </div>
                    <div className="panel-body">
                        <form onSubmit={handleUpload} className="upload-row">
                            <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                            <button type="submit" disabled={!file} className="ghost"><Upload size={14} /> Upload</button>
                        </form>
                        <ul className="resume-list">
                            {resumes.map((item) => (
                                <li key={item.id}>
                                    <div>
                                        <strong>{item.filename}</strong>
                                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                                    </div>
                                    {item.skills && (
                                        <div className="tag-row">
                                            {item.skills.split(',').slice(0, 5).map((skill: string) => (
                                                <span key={skill.trim()} className="tag">{skill.trim()}</span>
                                            ))}
                                        </div>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </section>

            {/* Recent Interviews */}
            <section className="table-panel" id="recent-interviews">
                <div className="panel-header">
                    <h2>Recent Interviews</h2>
                    <p>Latest sessions and outcomes.</p>
                </div>
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th><Calendar size={12} style={{ marginRight: 6, verticalAlign: 'middle' }} /> Date</th>
                                <th>Role</th>
                                <th>Score</th>
                                <th>Status</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {interviews.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="empty">No interviews yet. Start your first session above.</td>
                                </tr>
                            ) : (
                                interviews.slice(0, 8).map((item) => (
                                    <tr key={item.id}>
                                        <td>{new Date(item.started_at).toLocaleDateString()}</td>
                                        <td style={{ fontWeight: 600 }}>{item.role}</td>
                                        <td>{item.score !== null ? `${item.score.toFixed(1)}/10` : 'N/A'}</td>
                                        <td>
                                            <span className={`status ${item.status}`}>{item.status}</span>
                                        </td>
                                        <td>
                                            {item.status === 'completed' && (
                                                <button type="button" className="link" onClick={() => navigate(`/report/${item.id}`)}>
                                                    View report <ChevronRight size={14} style={{ verticalAlign: 'middle' }} />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
};

export default DashboardPage;
