import React, { useState, useEffect, useRef, useCallback } from 'react';
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

interface ReportListResponse {
  reports: Report[];
  total: number;
  page: number;
  per_page: number;
}

const Icon = {
  FileText: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>,
  Download: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
  Trash: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>,
  Refresh: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>,
  Plus: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  AlertTriangle: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  Check: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  Loader: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="rp-spin"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>,
  Briefcase: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>,
  Code: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>,
  Target: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>,
  TrendingUp: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
  BarChart: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>,
};

const REPORT_TYPE_INFO: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  portfolio: { label: 'Portfolio Report', icon: <Icon.Briefcase />, color: '#2563eb', bg: '#eff6ff' },
  interview: { label: 'Interview Report', icon: <Icon.BarChart />, color: '#8b5cf6', bg: '#f5f3ff' },
  coding: { label: 'Coding Report', icon: <Icon.Code />, color: '#10b981', bg: '#ecfdf5' },
  ats: { label: 'ATS Report', icon: <Icon.Target />, color: '#f59e0b', bg: '#fffbeb' },
  'skill-gap': { label: 'Skill Gap Report', icon: <Icon.Target />, color: '#06b6d4', bg: '#ecfeff' },
  'career-readiness': { label: 'Career Readiness', icon: <Icon.TrendingUp />, color: '#ef4444', bg: '#fef2f2' },
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

  return (
    <div className="rp-container" ref={wrapperRef}>
      <header className="rp-header">
        <div>
          <h1>Reports</h1>
          <p className="rp-subtitle">Generate and download comprehensive career reports</p>
        </div>
        <div className="rp-header-actions">
          <div className="rp-generate-wrapper">
            <button
              className="rp-btn rp-btn-primary"
              onClick={() => setShowGenerateMenu(!showGenerateMenu)}
              disabled={generating}
            >
              {generating ? <Icon.Loader /> : <Icon.Plus />}
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
          <Icon.AlertTriangle />
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
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
            style={filterType === type ? { borderColor: info.color, color: info.color } : {}}
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
          <Icon.FileText />
          <h3>No Reports Yet</h3>
          <p>Generate your first report to get started</p>
          <button className="rp-btn rp-btn-primary" onClick={() => generateReport('portfolio')}>
            <Icon.Plus /> Generate Portfolio Report
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
                      <Icon.AlertTriangle /> Outdated
                    </span>
                  )}
                  {report.status === 'generating' && (
                    <span className="rp-badge rp-badge-generating">
                      <Icon.Loader /> Generating
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
                    <Icon.FileText /> {formatFileSize(report.file_size)}
                  </span>
                  <div className="rp-card-actions">
                    <div className="rp-download-wrapper">
                      <button
                        className="rp-btn rp-btn-icon"
                        onClick={() => setDownloadMenuId(downloadMenuId === report.id ? null : report.id)}
                        disabled={report.status !== 'ready'}
                        title="Download"
                      >
                        <Icon.Download />
                      </button>
                      {downloadMenuId === report.id && (
                        <div className="rp-download-menu">
                          <button className="rp-menu-item" onClick={() => downloadReport(report, 'pdf')}>
                            <Icon.FileText /> PDF
                          </button>
                          <button className="rp-menu-item" onClick={() => downloadReport(report, 'docx')}>
                            <Icon.FileText /> DOCX
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
                        <Icon.Refresh />
                      </button>
                    )}
                    <button
                      className="rp-btn rp-btn-icon rp-btn-danger"
                      onClick={() => deleteReport(report.id)}
                      title="Delete"
                    >
                      <Icon.Trash />
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
