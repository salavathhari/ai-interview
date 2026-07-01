import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Clock, CheckCircle, XCircle, AlertCircle, ChevronRight,
  Briefcase, ChevronDown, MapPin, DollarSign, Send, Eye
} from 'lucide-react';
import { candidateApi } from '../../services/api';
import './candidate.css';

type TimelineEntry = {
  stage: string; label: string; timestamp?: string;
  actor?: string; note?: string; is_current: boolean;
};

type Application = {
  id: number; job_title: string; company_name?: string; status: string;
  applied_at: string; updated_at?: string; timeline?: TimelineEntry[];
  ats_score?: number; resume_match_score?: number; career_readiness_score?: number;
  interview_score?: number; coding_score?: number;
  decision?: string; decision_reason?: string;
  offer?: { id: number; salary_offered?: number; currency?: string; status: string; position_title?: string };
};

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: any; label: string }> = {
  applied:              { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',  icon: Send,      label: 'Applied' },
  screening:            { color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)', icon: Eye,       label: 'Screening' },
  interview_scheduled:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', icon: Clock,     label: 'Interview Scheduled' },
  interview_completed:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', icon: CheckCircle, label: 'Interview Completed' },
  coding_round:         { color: '#ec4899', bg: 'rgba(236,72,153,0.1)', icon: Clock,     label: 'Coding Round' },
  selected:             { color: '#10b981', bg: 'rgba(16,185,129,0.1)', icon: CheckCircle, label: 'Selected' },
  rejected:             { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  icon: XCircle,   label: 'Rejected' },
  offer_released:       { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)',  icon: AlertCircle, label: 'Offer Released' },
  hired:                { color: '#10b981', bg: 'rgba(16,185,129,0.1)', icon: CheckCircle, label: 'Hired' },
  withdrawn:            { color: '#64748b', bg: 'rgba(100,116,139,0.1)', icon: XCircle,  label: 'Withdrawn' },
};

const FILTER_TABS = [
  { value: '', label: 'All' },
  { value: 'applied', label: 'Applied' },
  { value: 'screening', label: 'Screening' },
  { value: 'interview_scheduled', label: 'Interview' },
  { value: 'coding_round', label: 'Coding' },
  { value: 'selected', label: 'Selected' },
  { value: 'offer_released', label: 'Offers' },
  { value: 'hired', label: 'Hired' },
  { value: 'rejected', label: 'Rejected' },
];

const ALL_STAGES = ['applied', 'screening', 'interview_scheduled', 'interview_completed', 'coding_round', 'selected', 'offer_released', 'hired'];

const SMALL_WORDS = new Set(['a','an','and','as','at','but','by','for','in','nor','of','on','or','so','the','to','up','yet','vs']);
function toTitleCase(str: string): string {
  if (!str) return '';
  return str.toLowerCase().split(/(\s+|-)/).map((w, i) => {
    if (/^\s+$/.test(w) || w === '-') return w;
    return (i === 0 || !SMALL_WORDS.has(w)) ? w.charAt(0).toUpperCase() + w.slice(1) : w;
  }).join('');
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function MyApplicationsPage() {
  const nav = useNavigate();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchApps = () => {
    setLoading(true);
    const params: any = { per_page: 50 };
    if (filter) params.status = filter;
    candidateApi.getMyApplications(params)
      .then(r => setApps(r.data.applications || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchApps(); }, [filter]);

  const toggleExpand = (id: number) => setExpandedId(expandedId === id ? null : id);

  const activeCount = apps.length;

  if (loading) {
    return (
      <div className="cj-ma-page">
        <div className="cj-ma-header">
          <div className="cj-skel-text cj-skel-text--xl" style={{ width: 200, height: 28 }} />
          <div className="cj-skel-text" style={{ width: 140, height: 14 }} />
        </div>
        <div className="cj-ma-filters-skel">
          {[1,2,3,4,5].map(i => <div key={i} className="cj-skel-pill" style={{ width: 70 }} />)}
        </div>
        <div className="cj-ma-list">
          {[1,2,3].map(i => (
            <div key={i} className="cj-ma-card-skel">
              <div className="cj-skel-icon" style={{ width: 40, height: 40, borderRadius: 10 }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div className="cj-skel-text" style={{ width: '45%', height: 16 }} />
                <div className="cj-skel-text" style={{ width: '25%', height: 12 }} />
              </div>
              <div className="cj-skel-pill" style={{ width: 80, height: 24 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="cj-ma-page">
      {/* Header */}
      <div className="cj-ma-header">
        <div>
          <h1 className="cj-ma-title">My Applications</h1>
          <p className="cj-ma-subtitle">
            {activeCount} application{activeCount !== 1 ? 's' : ''}
            {filter && ` · filtered by ${toTitleCase(filter.replace(/_/g, ' '))}`}
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="cj-ma-filters">
        {FILTER_TABS.map(tab => (
          <button
            key={tab.value}
            className={`cj-ma-filter-btn ${filter === tab.value ? 'cj-ma-filter-btn--active' : ''}`}
            onClick={() => setFilter(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Application List */}
      {apps.length === 0 ? (
        <div className="cj-ma-empty">
          <div className="cj-ma-empty-icon">
            <Briefcase size={32} />
          </div>
          <h3>No applications found</h3>
          <p>Browse open jobs and apply to get started</p>
          <button className="cj-ma-browse-btn" onClick={() => nav('/jobs')}>
            <Send size={16} /> Browse Jobs
          </button>
        </div>
      ) : (
        <div className="cj-ma-list">
          {apps.map(app => {
            const cfg = STATUS_CONFIG[app.status] || STATUS_CONFIG.applied;
            const Icon = cfg.icon;
            const isExpanded = expandedId === app.id;

            return (
              <div key={app.id} className={`cj-ma-card ${isExpanded ? 'cj-ma-card--expanded' : ''}`}>
                {/* Card Header */}
                <div className="cj-ma-card-row" onClick={() => toggleExpand(app.id)}>
                  <div className="cj-ma-card-left">
                    <div className="cj-ma-card-icon" style={{ background: cfg.bg, color: cfg.color }}>
                      <Icon size={18} />
                    </div>
                    <div className="cj-ma-card-info">
                      <h3 className="cj-ma-card-title">{toTitleCase(app.job_title)}</h3>
                      <div className="cj-ma-card-meta">
                        {app.company_name && (
                          <span className="cj-ma-card-meta-item">
                            <Briefcase size={13} /> {toTitleCase(app.company_name)}
                          </span>
                        )}
                        <span className="cj-ma-card-meta-item">
                          <Clock size={13} /> Applied {fmtDate(app.applied_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="cj-ma-card-right">
                    {/* Score Pills */}
                    {app.ats_score != null && (
                      <div className="cj-ma-score">
                        <span className="cj-ma-score-label">ATS</span>
                        <span className="cj-ma-score-value">{app.ats_score.toFixed(0)}</span>
                      </div>
                    )}
                    {app.interview_score != null && (
                      <div className="cj-ma-score">
                        <span className="cj-ma-score-label">Interview</span>
                        <span className="cj-ma-score-value">{app.interview_score.toFixed(0)}</span>
                      </div>
                    )}

                    {/* Status Badge */}
                    <span className="cj-ma-status" style={{ background: cfg.bg, color: cfg.color }}>
                      {cfg.label}
                    </span>

                    {/* Expand Arrow */}
                    <ChevronDown
                      size={18}
                      className={`cj-ma-expand ${isExpanded ? 'cj-ma-expand--open' : ''}`}
                    />
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="cj-ma-expanded">
                    {/* Timeline */}
                    <div className="cj-ma-timeline">
                      {ALL_STAGES.map((stage, idx) => {
                        const entry = app.timeline?.find(t => t.stage === stage);
                        const isActive = app.status === stage;
                        const isPast = !!entry?.timestamp && !entry?.is_current;
                        const isFuture = !entry?.timestamp && !isActive;
                        const stageCfg = STATUS_CONFIG[stage];

                        return (
                          <div key={stage} className={`cj-ma-tl-item ${isActive ? 'cj-ma-tl-item--active' : isPast ? 'cj-ma-tl-item--done' : ''}`}>
                            <div className={`cj-ma-tl-dot ${isPast || isActive ? 'cj-ma-tl-dot--filled' : ''}`}
                              style={isActive ? { borderColor: stageCfg?.color, boxShadow: `0 0 0 3px ${stageCfg?.bg}` } : {}}>
                              {isPast ? <CheckCircle size={11} /> : isActive ? <div className="cj-ma-tl-dot-pulse" style={{ background: stageCfg?.color }} /> : null}
                            </div>
                            {idx < ALL_STAGES.length - 1 && (
                              <div className={`cj-ma-tl-line ${isPast ? 'cj-ma-tl-line--filled' : ''}`} />
                            )}
                            <div className="cj-ma-tl-content">
                              <span className={`cj-ma-tl-label ${isActive ? 'cj-ma-tl-label--active' : isFuture ? 'cj-ma-tl-label--future' : ''}`}>
                                {stageCfg?.label || toTitleCase(stage.replace(/_/g, ' '))}
                              </span>
                              {entry?.timestamp && (
                                <span className="cj-ma-tl-time">{fmtDate(entry.timestamp)}</span>
                              )}
                              {entry?.note && (
                                <span className="cj-ma-tl-note">{entry.note}</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Offer Section */}
                    {app.offer && (
                      <div className="cj-ma-offer">
                        <div className="cj-ma-offer-header">
                          <AlertCircle size={18} />
                          <h4>Offer Details</h4>
                        </div>
                        <div className="cj-ma-offer-details">
                          {app.offer.salary_offered && (
                            <div className="cj-ma-offer-item">
                              <DollarSign size={15} />
                              <span className="cj-ma-offer-value">
                                ${app.offer.salary_offered.toLocaleString()} {app.offer.currency}
                              </span>
                            </div>
                          )}
                          {app.offer.position_title && (
                            <div className="cj-ma-offer-item">
                              <Briefcase size={15} />
                              <span>{toTitleCase(app.offer.position_title)}</span>
                            </div>
                          )}
                          <span className={`cj-ma-offer-status cj-ma-offer-status--${app.offer.status}`}>
                            {toTitleCase(app.offer.status)}
                          </span>
                        </div>
                        {app.offer.status === 'pending' && (
                          <div className="cj-ma-offer-actions">
                            <button className="cj-ma-offer-btn cj-ma-offer-btn--accept" onClick={() => {
                              candidateApi.respondToOffer(app.offer!.id, 'accepted').then(fetchApps);
                            }}>
                              <CheckCircle size={15} /> Accept Offer
                            </button>
                            <button className="cj-ma-offer-btn cj-ma-offer-btn--decline" onClick={() => {
                              candidateApi.respondToOffer(app.offer!.id, 'rejected').then(fetchApps);
                            }}>
                              <XCircle size={15} /> Decline
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Withdraw */}
                    {['applied', 'screening'].includes(app.status) && (
                      <div className="cj-ma-withdraw">
                        <button className="cj-ma-withdraw-btn" onClick={() => {
                          if (confirm('Are you sure you want to withdraw this application?')) {
                            candidateApi.withdrawApplication(app.id).then(fetchApps);
                          }
                        }}>
                          <XCircle size={14} /> Withdraw Application
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
