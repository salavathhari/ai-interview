import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Mail, Briefcase, BarChart3, Code2, Target, BookOpen } from 'lucide-react';
import { recruiterApi } from '../../services/api';
import './recruiter.css';

type Profile = {
  user_id: number; name: string; email: string;
  resume: any; resume_analysis: any;
  interview_scores: any[]; coding_scores: any[];
  career_readiness: any; skill_gap: any;
  applications: any[]; learning_progress: any;
};

const fmt = (v: number | null | undefined) => v == null ? 'N/A' : typeof v === 'number' ? v.toFixed(1) : String(v);

export default function RecruiterCandidateProfilePage() {
  const nav = useNavigate();
  const { userId } = useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    recruiterApi.getCandidateProfile(parseInt(userId!)).then(r => setProfile(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div>{[1, 2, 3].map(i => <div key={i} className="rp-skeleton" style={{ height: 80, marginBottom: 8 }} />)}</div>;
  if (!profile) return <div className="rp-empty"><h3>Candidate not found</h3></div>;

  const cr = profile.career_readiness;

  return (
    <div>
      <button className="rp-btn rp-btn--ghost" onClick={() => nav(-1)} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> Back
      </button>

      {/* Profile Header */}
      <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div className="rp-avatar rp-avatar--lg">{(profile.name?.[0] || 'U').toUpperCase()}</div>
          <div>
            <h2 style={{ margin: 0 }}>{profile.name}</h2>
            <p style={{ color: 'var(--rp-muted)', margin: '0.25rem 0', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}><Mail size={14} /> {profile.email}</p>
            {profile.applications.length > 0 && (
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                {profile.applications.map((a: any) => (
                  <span key={a.id} className={`rp-badge rp-badge--${a.status}`}>{a.status?.replace(/_/g, ' ')}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scores Overview */}
      {cr && (
        <div className="rp-metrics" style={{ marginBottom: '1.5rem' }}>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--blue"><BarChart3 size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">Overall Readiness</span><span className="rp-metric-value">{fmt(cr.overall_score)}</span></div></div>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--green"><Target size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">Resume Match</span><span className="rp-metric-value">{fmt(cr.resume_match_score)}</span></div></div>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--purple"><BarChart3 size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">ATS Score</span><span className="rp-metric-value">{fmt(cr.ats_score)}</span></div></div>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--amber"><Briefcase size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">Interview</span><span className="rp-metric-value">{fmt(cr.interview_score)}</span></div></div>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--cyan"><Code2 size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">Coding</span><span className="rp-metric-value">{fmt(cr.coding_score)}</span></div></div>
          <div className="rp-metric"><div className="rp-metric-icon rp-metric-icon--red"><BookOpen size={18} /></div><div className="rp-metric-body"><span className="rp-metric-label">Learning</span><span className="rp-metric-value">{fmt(cr.learning_score)}</span></div></div>
        </div>
      )}

      <div className="rp-grid rp-grid--2">
        {/* Left Column */}
        <div>
          {/* Resume */}
          {profile.resume && (
            <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem' }}>Resume</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ margin: 0, fontWeight: 500 }}>{profile.resume.filename}</p>
                  <p style={{ margin: '0.25rem 0', color: 'var(--rp-muted)', fontSize: '0.85rem' }}>
                    Skills: {profile.resume.skills || 'Not extracted'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Interview History */}
          {profile.interview_scores.length > 0 && (
            <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem' }}>Interview History</h3>
              <div className="rp-table-wrap">
                <table className="rp-table">
                  <thead><tr><th>Role</th><th>Score</th><th>Difficulty</th><th>Date</th></tr></thead>
                  <tbody>
                    {profile.interview_scores.map((s: any) => (
                      <tr key={s.id}>
                        <td>{s.role}</td>
                        <td><span className={`rp-score ${s.score >= 8 ? 'rp-score--high' : s.score >= 6 ? 'rp-score--mid' : 'rp-score--low'}`}>{fmt(s.score)}</span></td>
                        <td style={{ fontSize: '0.85rem' }}>{s.difficulty}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{s.started_at ? new Date(s.started_at).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Coding History */}
          {profile.coding_scores.length > 0 && (
            <div className="rp-card">
              <h3 style={{ margin: '0 0 1rem' }}>Coding History</h3>
              <div className="rp-table-wrap">
                <table className="rp-table">
                  <thead><tr><th>Score</th><th>Language</th><th>Date</th></tr></thead>
                  <tbody>
                    {profile.coding_scores.map((s: any) => (
                      <tr key={s.id}>
                        <td><span className={`rp-score ${s.coding_score >= 80 ? 'rp-score--high' : 'rp-score--mid'}`}>{fmt(s.coding_score)}</span></td>
                        <td style={{ fontSize: '0.85rem' }}>{s.language_used}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--rp-muted)' }}>{s.started_at ? new Date(s.started_at).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div>
          {/* Resume Analysis */}
          {profile.resume_analysis && (
            <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem' }}>Resume Analysis</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>ATS Score</span><span className={`rp-score ${(profile.resume_analysis.ats_score || 0) >= 70 ? 'rp-score--high' : 'rp-score--mid'}`}>{fmt(profile.resume_analysis.ats_score)}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>Resume Match</span><span className={`rp-score ${(profile.resume_analysis.resume_match_score || 0) >= 70 ? 'rp-score--high' : 'rp-score--mid'}`}>{fmt(profile.resume_analysis.resume_match_score)}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>Experience Level</span><span style={{ fontSize: '0.85rem' }}>{profile.resume_analysis.experience_level || 'N/A'}</span></div>
              </div>
            </div>
          )}

          {/* Skill Gap */}
          {profile.skill_gap && (
            <div className="rp-card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem' }}>Skill Gap</h3>
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--rp-muted)', fontSize: '0.85rem' }}>Match %</span>
                  <span style={{ fontWeight: 600 }}>{fmt(profile.skill_gap.match_percentage)}%</span>
                </div>
                <div style={{ height: 6, background: 'var(--rp-bg)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${profile.skill_gap.match_percentage || 0}%`, background: 'var(--rp-primary)', borderRadius: 3 }} />
                </div>
              </div>
              {profile.skill_gap.missing_skills && (
                <div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--rp-muted)', margin: '0 0 0.5rem' }}>Missing Skills</p>
                  <div className="rp-tags">
                    {(Array.isArray(profile.skill_gap.missing_skills) ? profile.skill_gap.missing_skills : []).map((s: string, i: number) => (
                      <span key={i} className="rp-tag" style={{ background: 'var(--rp-danger-bg)', color: 'var(--rp-danger)' }}>{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Applications */}
          {profile.applications.length > 0 && (
            <div className="rp-card">
              <h3 style={{ margin: '0 0 1rem' }}>Applications</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {profile.applications.map((a: any) => (
                  <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem', background: 'var(--rp-bg)', borderRadius: 6 }}>
                    <span style={{ fontSize: '0.85rem' }}>Job #{a.job_post_id}</span>
                    <span className={`rp-badge rp-badge--${a.status}`}>{a.status?.replace(/_/g, ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
