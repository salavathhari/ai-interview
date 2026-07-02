import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  MapPin, Briefcase, DollarSign, Building2,
  CheckCircle, Clock, GraduationCap, Heart,
  Share2, BookmarkPlus, ChevronRight, Zap, Trophy,
  FileText, X, Loader2
} from 'lucide-react';
import { candidateApi, resumeApi } from '../../services/api';
import './candidate.css';

type Job = {
  id: number;
  title: string;
  description?: string;
  company_name?: string;
  department?: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  education?: string;
  responsibilities?: string[];
  benefits?: string[];
  deadline?: string;
  posted_at?: string;
  has_applied?: boolean;
  readiness_match?: number;
  status?: string;
  headcount?: number;
  remote_policy?: string;
  application_count?: number;
};

type Resume = { id: number; filename: string; is_active: boolean };

const EMPLOYMENT_LABELS: Record<string, string> = {
  full_time: 'Full-time', part_time: 'Part-time', contract: 'Contract',
  internship: 'Internship', freelance: 'Freelance',
};

const EXP_LABELS: Record<string, string> = {
  entry: 'Entry Level', junior: 'Junior', mid: 'Mid Level',
  senior: 'Senior', lead: 'Lead', executive: 'Executive',
};

const SMALL_WORDS = new Set(['a','an','and','as','at','but','by','for','in','nor','of','on','or','so','the','to','up','yet','vs']);

function toTitleCase(str: string): string {
  if (!str) return '';
  return str
    .toLowerCase()
    .split(/(\s+|-)/)
    .map((word, i) => {
      if (/^\s+$/.test(word) || word === '-') return word;
      if (i === 0 || !SMALL_WORDS.has(word)) {
        return word.charAt(0).toUpperCase() + word.slice(1);
      }
      return word;
    })
    .join('');
}

export default function CandidateJobDetailPage() {
  const { jobId } = useParams();
  const nav = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<number | null>(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [showApply, setShowApply] = useState(false);
  const [applying, setApplying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [bookmarked, setBookmarked] = useState(false);
  const [showShareToast, setShowShareToast] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    candidateApi.getJobDetail(Number(jobId))
      .then(r => setJob(r.data))
      .catch(() => nav('/jobs'))
      .finally(() => setLoading(false));
    resumeApi.getMyResumes()
      .then(r => {
        const list = r.data.resumes || r.data || [];
        setResumes(list);
        const active = list.find((r: Resume) => r.is_active);
        if (active) setSelectedResume(active.id);
      })
      .catch(() => {});
  }, [jobId]);

  const handleApply = async () => {
    if (!selectedResume || !job) return;
    setApplying(true);
    try {
      await candidateApi.applyToJob(job.id, {
        resume_id: selectedResume,
        cover_letter: coverLetter || undefined,
      });
      setJob({ ...job, has_applied: true });
      setShowApply(false);
      nav('/my-applications');
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Failed to apply');
    } finally {
      setApplying(false);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setShowShareToast(true);
    setTimeout(() => setShowShareToast(false), 2000);
  };

  const fmtSalary = () => {
    if (!job?.salary_min && !job?.salary_max) return null;
    const fmt = (n: number) => n >= 1000 ? `$${(n / 1000).toFixed(0)}k` : `$${n}`;
    if (job.salary_min && job.salary_max) return `${fmt(job.salary_min)} - ${fmt(job.salary_max)}`;
    if (job.salary_min) return `From ${fmt(job.salary_min)}`;
    return `Up to ${fmt(job.salary_max!)}`;
  };

  const fmtTimeAgo = (date?: string) => {
    if (!date) return null;
    const diff = Date.now() - new Date(date).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return `${Math.floor(days / 30)} months ago`;
  };

  if (loading) {
    return (
      <div className="cj-detail-page">
        <div className="cj-detail-skeleton">
          <div className="cj-skel-back" />
          <div className="cj-skel-layout">
            <div className="cj-skel-main">
              <div className="cj-skel-hero">
                <div className="cj-skel-hero-icon" />
                <div className="cj-skel-hero-text">
                  <div className="cj-skel-text cj-skel-text--xl" />
                  <div className="cj-skel-text cj-skel-text--lg" />
                  <div className="cj-skel-pills">
                    <div className="cj-skel-pill" />
                    <div className="cj-skel-pill" />
                    <div className="cj-skel-pill" />
                  </div>
                </div>
              </div>
              <div className="cj-skel-block" />
              <div className="cj-skel-block" />
              <div className="cj-skel-block cj-skel-block--sm" />
            </div>
            <div className="cj-skel-aside">
              <div className="cj-skel-block cj-skel-block--cta" />
              <div className="cj-skel-block cj-skel-block--summary" />
              <div className="cj-skel-block cj-skel-block--small" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!job) return null;

  const matchPct = job.readiness_match ?? null;
  const matchLevel = matchPct != null ? (matchPct >= 70 ? 'high' : matchPct >= 40 ? 'mid' : 'low') : null;
  const displayTitle = toTitleCase(job.title);
  const displayLocation = job.location ? toTitleCase(job.location) : null;

  const summaryRows = [
    job.department && { label: 'Department', value: toTitleCase(job.department) },
    job.location && { label: 'Location', value: displayLocation },
    job.remote_policy && { label: 'Work Policy', value: toTitleCase(job.remote_policy) },
    job.employment_type && { label: 'Type', value: EMPLOYMENT_LABELS[job.employment_type] || job.employment_type },
    job.experience_level && { label: 'Level', value: EXP_LABELS[job.experience_level] || job.experience_level },
    fmtSalary() && { label: 'Salary', value: fmtSalary(), accent: true },
    job.posted_at && { label: 'Posted', value: fmtTimeAgo(job.posted_at) },
  ].filter(Boolean) as { label: string; value: string; accent?: boolean }[];

  return (
    <div className="cj-detail-page">
      {/* Breadcrumb */}
      <nav className="cj-breadcrumb">
        <button onClick={() => nav('/jobs')}>Job Board</button>
        <ChevronRight size={14} />
        <span>{displayTitle}</span>
      </nav>

      {/* Hero */}
      <div className="cj-detail-hero">
        <div className="cj-detail-hero-bg" />
        <div className="cj-detail-hero-content">
          <div className="cj-detail-hero-left">
            <div className="cj-detail-hero-icon">
              <Building2 size={32} />
            </div>
            <div className="cj-detail-hero-info">
              <h1 className="cj-detail-hero-title">{displayTitle}</h1>
              <div className="cj-detail-hero-company">{toTitleCase(job.company_name || 'Company')}</div>
              <div className="cj-detail-hero-meta">
                {displayLocation && (
                  <span className="cj-detail-meta-pill">
                    <MapPin size={14} /> {displayLocation}
                  </span>
                )}
                {job.employment_type && (
                  <span className="cj-detail-meta-pill">
                    <Briefcase size={14} /> {EMPLOYMENT_LABELS[job.employment_type] || job.employment_type}
                  </span>
                )}
                {job.experience_level && (
                  <span className="cj-detail-meta-pill">
                    <Trophy size={14} /> {EXP_LABELS[job.experience_level] || job.experience_level}
                  </span>
                )}
                {fmtSalary() && (
                  <span className="cj-detail-meta-pill cj-detail-meta-pill--salary">
                    <DollarSign size={14} /> {fmtSalary()}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="cj-detail-hero-actions">
            {job.has_applied ? (
              <div className="cj-detail-applied-badge">
                <CheckCircle size={18} />
                <div>
                  <div className="cj-detail-applied-title">Application Submitted</div>
                  <div className="cj-detail-applied-sub">Track progress in My Applications</div>
                </div>
              </div>
            ) : (
              <button className="cj-detail-apply-btn" onClick={() => setShowApply(true)}>
                <Zap size={18} /> Apply Now
              </button>
            )}
            <div className="cj-detail-hero-secondary">
              <button
                className={`cj-detail-icon-btn ${bookmarked ? 'cj-detail-icon-btn--active' : ''}`}
                onClick={() => setBookmarked(!bookmarked)}
                title="Save job"
              >
                <BookmarkPlus size={18} />
              </button>
              <button className="cj-detail-icon-btn" onClick={handleShare} title="Share">
                <Share2 size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="cj-detail-body">
        {/* Main Content */}
        <div className="cj-detail-main">
          {/* About the Role */}
          {job.description && (
            <section className="cj-detail-section">
              <h2 className="cj-detail-section-title">
                <FileText size={18} /> About the Role
              </h2>
              <div className="cj-detail-description">
                {job.description.split('\n').map((p, i) => <p key={i}>{p}</p>)}
              </div>
            </section>
          )}

          {/* Responsibilities */}
          {job.responsibilities && job.responsibilities.length > 0 && (
            <section className="cj-detail-section">
              <h2 className="cj-detail-section-title">
                <CheckCircle size={18} /> Key Responsibilities
              </h2>
              <ul className="cj-detail-list">
                {job.responsibilities.map((r, i) => (
                  <li key={i} className="cj-detail-list-item">
                    <span className="cj-detail-list-bullet" />
                    {toTitleCase(r)}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Requirements */}
          {job.education && (
            <section className="cj-detail-section">
              <h2 className="cj-detail-section-title">
                <GraduationCap size={18} /> Requirements
              </h2>
              <div className="cj-detail-description">
                {job.education.split('\n').map((p, i) => <p key={i}>{p}</p>)}
              </div>
            </section>
          )}

          {/* Skills */}
          {(job.required_skills && job.required_skills.length > 0) && (
            <section className="cj-detail-section">
              <h2 className="cj-detail-section-title">
                <Zap size={18} /> Required Skills
              </h2>
              <div className="cj-detail-skills">
                {job.required_skills.map(s => (
                  <span key={s} className="cj-detail-skill cj-detail-skill--required">{toTitleCase(s)}</span>
                ))}
              </div>
              {job.preferred_skills && job.preferred_skills.length > 0 && (
                <>
                  <h3 className="cj-detail-subtitle">Nice to Have</h3>
                  <div className="cj-detail-skills">
                    {job.preferred_skills.map(s => (
                      <span key={s} className="cj-detail-skill cj-detail-skill--preferred">{toTitleCase(s)}</span>
                    ))}
                  </div>
                </>
              )}
            </section>
          )}

          {/* Benefits */}
          {job.benefits && job.benefits.length > 0 && (
            <section className="cj-detail-section">
              <h2 className="cj-detail-section-title">
                <Heart size={18} /> Benefits & Perks
              </h2>
              <div className="cj-detail-benefits">
                {job.benefits.map((b, i) => (
                  <div key={i} className="cj-detail-benefit">
                    <CheckCircle size={16} className="cj-detail-benefit-icon" />
                    <span>{toTitleCase(b)}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="cj-detail-sidebar">
          {/* Apply Card — only show CTA if not already applied */}
          {job.has_applied ? (
            <div className="cj-detail-sidebar-card cj-detail-sidebar-card--cta">
              <div className="cj-sidebar-applied">
                <CheckCircle size={24} />
                <span>Applied</span>
                <button className="cj-sidebar-link" onClick={() => nav('/my-applications')}>
                  View Application
                </button>
              </div>
            </div>
          ) : (
            <div className="cj-detail-sidebar-card cj-detail-sidebar-card--sticky">
              {job.deadline && (
                <div className="cj-sidebar-deadline">
                  <Clock size={14} />
                  <span>Closes {new Date(job.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                </div>
              )}
              <button className="cj-detail-sidebar-apply" onClick={() => setShowApply(true)}>
                <Zap size={16} /> Quick Apply
              </button>
              <div className="cj-sidebar-actions-row">
                <button
                  className={`cj-sidebar-action-btn ${bookmarked ? 'cj-sidebar-action-btn--active' : ''}`}
                  onClick={() => setBookmarked(!bookmarked)}
                >
                  <BookmarkPlus size={15} />
                  <span>{bookmarked ? 'Saved' : 'Save'}</span>
                </button>
                <button className="cj-sidebar-action-btn" onClick={handleShare}>
                  <Share2 size={15} />
                  <span>Share</span>
                </button>
              </div>
            </div>
          )}

          {/* Job Summary */}
          {summaryRows.length > 0 && (
            <div className="cj-detail-sidebar-card">
              <h3 className="cj-sidebar-card-title">Job Summary</h3>
              <div className="cj-sidebar-summary">
                {summaryRows.map((row, i) => (
                  <div key={i} className="cj-sidebar-summary-row">
                    <span className="cj-sidebar-summary-label">{row.label}</span>
                    <span className={`cj-sidebar-summary-value ${row.accent ? 'cj-sidebar-summary-value--accent' : ''}`}>
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Match Score */}
          {matchPct != null && matchLevel && (
            <div className="cj-detail-sidebar-card">
              <h3 className="cj-sidebar-card-title">
                <Trophy size={16} /> Your Match
              </h3>
              <div className="cj-sidebar-match">
                <div className={`cj-sidebar-match-ring cj-sidebar-match-ring--${matchLevel}`}>
                  <span className="cj-sidebar-match-pct">{matchPct.toFixed(0)}%</span>
                </div>
                <span className="cj-sidebar-match-label">
                  {matchLevel === 'high' ? 'Strong match' : matchLevel === 'mid' ? 'Good match' : 'Partial match'}
                </span>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* Share Toast */}
      {showShareToast && (
        <div className="cj-toast">
          <CheckCircle size={16} /> Link copied to clipboard
        </div>
      )}

      {/* Apply Modal */}
      {showApply && (
        <div className="cj-apply-overlay" onClick={() => setShowApply(false)}>
          <div className="cj-apply-modal" onClick={e => e.stopPropagation()}>

            {/* Header */}
            <div className="cj-apply-header">
              <div className="cj-apply-header-left">
                <div className="cj-apply-header-icon">
                  <Zap size={20} />
                </div>
                <div>
                  <h3 className="cj-apply-title">Apply to {displayTitle}</h3>
                  <p className="cj-apply-sub">{toTitleCase(job.company_name || 'Company')}</p>
                </div>
              </div>
              <button className="cj-apply-close" onClick={() => setShowApply(false)}>
                <X size={18} />
              </button>
            </div>

            {/* Body */}
            <div className="cj-apply-body">

              {/* Resume Section */}
              <div className="cj-apply-field">
                <div className="cj-apply-label-row">
                  <label className="cj-apply-label">
                    <FileText size={15} /> Select Resume
                  </label>
                  <span className="cj-apply-required">Required</span>
                </div>
                {resumes.length === 0 ? (
                  <div className="cj-apply-empty-resume">
                    <FileText size={22} />
                    <div>
                      <p className="cj-apply-empty-title">No resumes uploaded</p>
                      <p className="cj-apply-empty-sub">Upload a resume in your profile to apply.</p>
                    </div>
                  </div>
                ) : (
                  <div className="cj-apply-resume-list">
                    {resumes.map(r => (
                      <label
                        key={r.id}
                        className={`cj-apply-resume-card ${selectedResume === r.id ? 'cj-apply-resume-card--selected' : ''}`}
                      >
                        <input
                          type="radio"
                          name="resume"
                          value={r.id}
                          checked={selectedResume === r.id}
                          onChange={() => setSelectedResume(r.id)}
                          className="cj-apply-radio"
                        />
                        <div className="cj-apply-radio-custom" />
                        <div className="cj-apply-resume-file">
                          <FileText size={18} />
                        </div>
                        <div className="cj-apply-resume-details">
                          <span className="cj-apply-resume-name">{r.filename}</span>
                          {r.is_active && (
                            <span className="cj-apply-resume-badge">
                              <CheckCircle size={12} /> Active
                            </span>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Divider */}
              <div className="cj-apply-divider" />

              {/* Cover Letter Section */}
              <div className="cj-apply-field">
                <div className="cj-apply-label-row">
                  <label className="cj-apply-label">
                    <FileText size={15} /> Cover Letter
                  </label>
                  <span className="cj-apply-optional">Optional</span>
                </div>
                <div className="cj-apply-textarea-wrap">
                  <textarea
                    className="cj-apply-textarea"
                    rows={4}
                    value={coverLetter}
                    onChange={e => setCoverLetter(e.target.value)}
                    placeholder="Tell the recruiter why you're a great fit for this role..."
                  />
                  <span className="cj-apply-textarea-count">{coverLetter.length}</span>
                </div>
                <p className="cj-apply-hint">
                  A personalized cover letter significantly increases your chances of being noticed.
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="cj-apply-footer">
              <button className="cj-apply-cancel" onClick={() => setShowApply(false)}>
                Cancel
              </button>
              <button
                className="cj-apply-submit"
                onClick={handleApply}
                disabled={!selectedResume || applying}
              >
                {applying ? (
                  <><Loader2 size={16} className="cj-spin" /> Submitting...</>
                ) : (
                  <><Zap size={16} /> Submit Application</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
