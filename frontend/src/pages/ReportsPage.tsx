import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ArrowLeft,
  FileText,
  Download,
  Trash2,
  RefreshCw,
  Plus,
  AlertTriangle,
  Loader2,
  Briefcase,
  Code2,
  Target,
  TrendingUp,
  BarChart3,
  FileUp,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { reportsApi } from '../services/api';
import './ReportsPage.css';

interface Report {
  id: number;
  title: string;
  report_type: string;
  status: string;
  file_size: number | null;
  summary: string | null;
  scores_snapshot: string | null;
  is_outdated: boolean;
  outdated_reason: string | null;
  created_at: string;
  updated_at: string | null;
}

const REPORT_TYPE_INFO: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  portfolio: { label: 'Portfolio Report', icon: <Briefcase size={18} />, color: '#2563eb', bg: '#eff6ff' },
  interview: { label: 'Interview Report', icon: <BarChart3 size={18} />, color: '#8b5cf6', bg: '#f5f3ff' },
  coding: { label: 'Coding Report', icon: <Code2 size={18} />, color: '#10b981', bg: '#ecfdf5' },
  ats: { label: 'ATS Report', icon: <Target size={18} />, color: '#f59e0b', bg: '#fffbeb' },
  'skill-gap': { label: 'Skill Gap Report', icon: <Target size={18} />, color: '#06b6d4', bg: '#ecfeff' },
  'career-readiness': { label: 'Career Readiness', icon: <TrendingUp size={18} />, color: '#ef4444', bg: '#fef2f2' },
};

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatingType, setGeneratingType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [showGenerateMenu, setShowGenerateMenu] = useState(false);
  const [downloadMenuId, setDownloadMenuId] = useState<number | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
      setShowGenerateMenu(false);
      setDownloadMenuId(null);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  useEffect(() => {
    loadReports();
  }, [page, filterType]);

  const loadReports = async () => {
    try {
      setLoading(true);
      const params: any = { page, per_page: 20 };
      if (filterType) params.report_type = filterType;
      const resp = await reportsApi.list(params);
      setReports(resp.data.reports);
      setTotal(resp.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (type: string) => {
    try {
      setGenerating(true);
      setGeneratingType(type);
      setShowGenerateMenu(false);
      await reportsApi.generate(type);
      await loadReports();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
      setGeneratingType(null);
    }
  };

  const downloadReport = async (report: Report, format: 'pdf' | 'docx' = 'pdf') => {
    try {
      setDownloadMenuId(null);
      const resp = await reportsApi.download(report.id, format);
      const mimeTypes: Record<string, string> = {
        pdf: 'application/pdf',
        docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      };
      const ext = format === 'docx' ? 'docx' : 'pdf';
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: mimeTypes[format] }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.title.replace(/\s+/g, '_').toLowerCase()}.${ext}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Download failed');
    }
  };

  const deleteReport = async (reportId: number) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await reportsApi.delete(reportId);
      await loadReports();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete report');
    }
  };

  const formatFileSize = (bytes: number | null): string => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string): string => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const parseScores = (snapshot: string | null): Record<string, number> => {
    if (!snapshot) return {};
    try {
      return JSON.parse(snapshot);
    } catch {
      return {};
    }
  };

  const totalSize = reports.reduce((sum, r) => sum + (r.file_size ?? 0), 0);
  const readyCount = reports.filter(r => r.status === 'ready').length;
  const outdatedCount = reports.filter(r => r.is_outdated).length;

  return (
    <div className="rp-container" ref={wrapperRef}>
      <header className="rp-header">
        <div>
          <p className="rp-eyebrow">Document Center</p>
          <h1>Reports</h1>
          <span className="rp-subtitle">Generate and download comprehensive career reports</span>
        </div>
        <div className="rp-header-actions">
          <button className="rp-back-btn" onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={15} /> Dashboard
          </button>
          <div className="rp-generate-wrapper">
            <button
              className="rp-btn rp-btn-primary"
              onClick={() => setShowGenerateMenu(!showGenerateMenu)}
              disabled={generating}
            >
              {generating ? <Loader2 size={15} className="rp-spin" /> : <Plus size={15} />}
              {generating ? `Generating ${generatingType}...` : 'Generate Report'}
            </button>
            {showGenerateMenu && (
              <div className="rp-generate-menu">
                {Object.entries(REPORT_TYPE_INFO).map(([type, info]) => (
                  <button
                    key={type}
                    className="rp-menu-item"
                    onClick={() => generateReport(type)}
                  >
                    <span className="rp-menu-icon" style={{ color: info.color, background: info.bg }}>{info.icon}</span>
                    <span>{info.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      {error && (
        <div className="rp-alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="rp-stats-row">
          <div className="rp-stat-card">
            <div className="rp-stat-icon" style={{ color: '#2563eb', background: '#eff6ff' }}>
              <FileText size={20} />
            </div>
            <div className="rp-stat-info">
              <span>Total Reports</span>
              <strong>{total}</strong>
            </div>
          </div>
          <div className="rp-stat-card">
            <div className="rp-stat-icon" style={{ color: '#10b981', background: '#ecfdf5' }}>
              <FileUp size={20} />
            </div>
            <div className="rp-stat-info">
              <span>Ready</span>
              <strong>{readyCount}</strong>
            </div>
          </div>
          <div className="rp-stat-card">
            <div className="rp-stat-icon" style={{ color: '#f59e0b', background: '#fffbeb' }}>
              <AlertTriangle size={20} />
            </div>
            <div className="rp-stat-info">
              <span>Outdated</span>
              <strong>{outdatedCount}</strong>
            </div>
          </div>
          <div className="rp-stat-card">
            <div className="rp-stat-icon" style={{ color: '#8b5cf6', background: '#f5f3ff' }}>
              <Download size={20} />
            </div>
            <div className="rp-stat-info">
              <span>Total Size</span>
              <strong>{formatFileSize(totalSize)}</strong>
            </div>
          </div>
        </div>
      )}

      <div className="rp-filters">
        <button
          className={`rp-filter-btn ${filterType === '' ? 'active' : ''}`}
          onClick={() => { setFilterType(''); setPage(1); }}
        >
          All ({total})
        </button>
        {Object.entries(REPORT_TYPE_INFO).map(([type, info]) => (
          <button
            key={type}
            className={`rp-filter-btn ${filterType === type ? 'active' : ''}`}
            onClick={() => { setFilterType(type); setPage(1); }}
          >
            {info.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="rp-loading-grid">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rp-skeleton-card">
              <div className="rp-skeleton-line rp-skeleton-title" />
              <div className="rp-skeleton-line rp-skeleton-subtitle" />
              <div className="rp-skeleton-line rp-skeleton-body" />
            </div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="rp-empty">
          <div className="rp-empty-icon">
            <FileText size={36} />
          </div>
          <h3>No Reports Yet</h3>
          <p>Generate your first report to get started</p>
          <button className="rp-btn rp-btn-primary" onClick={() => generateReport('portfolio')}>
            <Plus size={15} /> Generate Portfolio Report
          </button>
        </div>
      ) : (
        <div className="rp-reports-grid">
          {reports.map((report) => {
            const typeInfo = REPORT_TYPE_INFO[report.report_type] || REPORT_TYPE_INFO.portfolio;
            const scores = parseScores(report.scores_snapshot);
            return (
              <div key={report.id} className={`rp-report-card ${report.is_outdated ? 'outdated' : ''}`}>
                <div className="rp-card-header">
                  <div className="rp-card-icon" style={{ color: typeInfo.color, background: typeInfo.bg }}>
                    {typeInfo.icon}
                  </div>
                  <div className="rp-card-meta">
                    <span className="rp-card-type" style={{ color: typeInfo.color }}>{typeInfo.label}</span>
                    <span className="rp-card-date">{formatDate(report.created_at)}</span>
                  </div>
                  {report.is_outdated && (
                    <span className="rp-badge rp-badge-outdated">
                      <AlertTriangle size={12} /> Outdated
                    </span>
                  )}
                  {report.status === 'generating' && (
                    <span className="rp-badge rp-badge-generating">
                      <Loader2 size={12} className="rp-spin" /> Generating
                    </span>
                  )}
                </div>

                <h3 className="rp-card-title">{report.title}</h3>

                {report.summary && (
                  <p className="rp-card-summary">{report.summary.substring(0, 150)}...</p>
                )}

                {Object.keys(scores).length > 0 && (
                  <div className="rp-card-scores">
                    {scores.resume_match !== undefined && (
                      <div className="rp-score-chip">
                        <span>Resume</span>
                        <strong>{scores.resume_match.toFixed(0)}%</strong>
                      </div>
                    )}
                    {scores.ats_score !== undefined && (
                      <div className="rp-score-chip">
                        <span>ATS</span>
                        <strong>{scores.ats_score.toFixed(0)}%</strong>
                      </div>
                    )}
                    {scores.overall_readiness !== undefined && (
                      <div className="rp-score-chip">
                        <span>Readiness</span>
                        <strong>{scores.overall_readiness.toFixed(0)}%</strong>
                      </div>
                    )}
                    {scores.interview_score !== undefined && (
                      <div className="rp-score-chip">
                        <span>Interview</span>
                        <strong>{scores.interview_score.toFixed(0)}%</strong>
                      </div>
                    )}
                    {scores.coding_score !== undefined && (
                      <div className="rp-score-chip">
                        <span>Coding</span>
                        <strong>{scores.coding_score.toFixed(0)}%</strong>
                      </div>
                    )}
                  </div>
                )}

                <div className="rp-card-footer">
                  <span className="rp-file-size">
                    <FileText size={14} /> {formatFileSize(report.file_size)}
                  </span>
                  <div className="rp-card-actions">
                    <div className="rp-download-wrapper">
                      <button
                        className="rp-btn rp-btn-icon"
                        onClick={() => setDownloadMenuId(downloadMenuId === report.id ? null : report.id)}
                        disabled={report.status !== 'ready'}
                        title="Download"
                      >
                        <Download size={15} />
                      </button>
                      {downloadMenuId === report.id && (
                        <div className="rp-download-menu">
                          <button className="rp-menu-item" onClick={() => downloadReport(report, 'pdf')}>
                            <FileText size={14} /> PDF
                          </button>
                          <button className="rp-menu-item" onClick={() => downloadReport(report, 'docx')}>
                            <FileText size={14} /> DOCX
                          </button>
                        </div>
                      )}
                    </div>
                    {report.is_outdated && (
                      <button
                        className="rp-btn rp-btn-icon"
                        onClick={() => generateReport(report.report_type)}
                        title="Regenerate"
                      >
                        <RefreshCw size={15} />
                      </button>
                    )}
                    <button
                      className="rp-btn rp-btn-icon rp-btn-danger"
                      onClick={() => deleteReport(report.id)}
                      title="Delete"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {total > 20 && (
        <div className="rp-pagination">
          <button
            className="rp-btn rp-btn-secondary"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span className="rp-page-info">Page {page} of {Math.ceil(total / 20)}</span>
          <button
            className="rp-btn rp-btn-secondary"
            onClick={() => setPage(p => p + 1)}
            disabled={page >= Math.ceil(total / 20)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
