import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { careerApi } from '../../services/api';
import { ArrowRight, Trash2, Search, FileText, Upload, Loader2, CheckCircle2 } from 'lucide-react';
import './JobDescriptionPage.css';

interface JobDescription {
  id: number;
  title: string;
  company: string | null;
  source: string;
  raw_text: string;
  required_skills: string[];
  preferred_skills: string[];
  technologies: string[];
  soft_skills: string[];
  keywords: string[];
  responsibilities: string[];
  experience_years: string | null;
  education_requirements: string | null;
  is_analyzed: boolean;
  created_at: string;
}

interface JDListResponse {
  items: JobDescription[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

const JobDescriptionPage: React.FC = () => {
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedJd, setSelectedJd] = useState<JobDescription | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [pasteAnalysisComplete, setPasteAnalysisComplete] = useState(false);
  const [reanalyzeComplete, setReanalyzeComplete] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadJDs();
  }, [page, searchTerm]);

  const loadJDs = async () => {
    try {
      setLoading(true);
      const resp = await careerApi.getJobDescriptions({
        page,
        per_page: 10,
        search: searchTerm || undefined,
      });
      const data: JDListResponse = resp.data;
      setJds(data.items);
      setTotal(data.total);
      setPages(data.pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load job descriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleFileDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      const ext = dropped.name.toLowerCase();
      if (!ext.endsWith('.pdf') && !ext.endsWith('.docx') && !ext.endsWith('.doc') && !ext.endsWith('.txt')) {
        setError('Unsupported file type. Use PDF, DOCX, or TXT.');
        return;
      }
      if (dropped.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10MB.');
        return;
      }
      setSelectedFile(dropped);
    }
  }, []);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !title.trim()) return;

    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      if (company) formData.append('company', company);

      const resp = await careerApi.uploadJobDescription(formData, (pct) => setUploadProgress(pct));
      setSelectedJd(resp.data);
      setTitle('');
      setCompany('');
      setSelectedFile(null);
      setPage(1);
      loadJDs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload JD');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handlePasteUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pasteText.trim() || !title.trim()) return;

    try {
      setUploading(true);
      setError(null);
      setPasteAnalysisComplete(false);
      const formData = new FormData();
      formData.append('raw_text', pasteText);
      formData.append('title', title);
      if (company) formData.append('company', company);

      const resp = await careerApi.uploadJobDescription(formData);
      setSelectedJd(resp.data);
      setPasteAnalysisComplete(true);
      setTimeout(() => setPasteAnalysisComplete(false), 2500);
      setTitle('');
      setCompany('');
      setPasteText('');
      setPasteMode(false);
      setPage(1);
      loadJDs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload JD');
    } finally {
      setUploading(false);
    }
  };

  const viewJD = async (jdId: number) => {
    try {
      const resp = await careerApi.getJobDescription(jdId);
      setSelectedJd(resp.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load JD details');
    }
  };

  const reanalyzeJD = async (jdId: number) => {
    try {
      setAnalyzing(jdId);
      setError(null);
      setReanalyzeComplete(null);
      const resp = await careerApi.analyzeJobDescription(jdId);
      setSelectedJd(resp.data);
      setReanalyzeComplete(jdId);
      setTimeout(() => setReanalyzeComplete(null), 2500);
      loadJDs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to re-analyze JD');
    } finally {
      setAnalyzing(null);
    }
  };

  const deleteJD = async (jdId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure? This will delete all related analyses and cannot be undone.')) return;
    try {
      await careerApi.deleteJobDescription(jdId);
      loadJDs();
      if (selectedJd?.id === jdId) setSelectedJd(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete job description');
    }
  };

  return (
    <div className="jd-page">
      <span className="jd-eyebrow">Job Descriptions</span>
      <header className="career-header">
        <div>
          <h1>Job Descriptions</h1>
          <p>Upload and analyze job descriptions to optimize your resume</p>
        </div>
        <div className="header-actions">
          <button type="button" className="ghost" onClick={() => navigate('/career/skill-gap')}><Search size={16} /> Skill Gap Analysis</button>
          <button type="button" className="ghost" onClick={() => navigate('/career/dashboard')}><ArrowRight size={16} style={{ transform: 'rotate(180deg)' }} /> Dashboard</button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          {error}
          <button type="button" onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="jd-layout">
        <section className="jd-upload-panel">
          <div className="panel">
            <div className="panel-header">
              <h2>Upload Job Description</h2>
              <p>Upload a PDF/DOCX/TXT or paste the job description text</p>
            </div>

            <div className="upload-tabs">
              <button
                type="button"
                className={`tab ${!pasteMode ? 'active' : ''}`}
                onClick={() => setPasteMode(false)}
              >
                File Upload
              </button>
              <button
                type="button"
                className={`tab ${pasteMode ? 'active' : ''}`}
                onClick={() => setPasteMode(true)}
              >
                Paste Text
              </button>
            </div>

            {!pasteMode ? (
              <form onSubmit={handleFileUpload} className="upload-form">
                <label className="input-field">
                  <span>Title *</span>
                  <input
                    type="text"
                    placeholder="e.g. Senior Frontend Developer"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </label>
                <label className="input-field">
                  <span>Company</span>
                  <input
                    type="text"
                    placeholder="e.g. Google"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                  />
                </label>
                <div
                  className={`file-drop ${isDragging ? 'dragging' : ''}`}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleFileDrop}
                >
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  />
                  {selectedFile ? (
                    <p className="file-name">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)}KB)</p>
                  ) : (
                    <p>Drag & drop a file here, or click to browse</p>
                  )}
                </div>
                {uploading && uploadProgress > 0 && (
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                    <span>{uploadProgress}%</span>
                  </div>
                )}
                <button type="submit" className="solid" disabled={!selectedFile || !title.trim() || uploading}>
                  {uploading ? <><Loader2 size={16} className="spin" /> Uploading... {uploadProgress}%</> : <><Upload size={16} /> Upload & Analyze</>}
                </button>
              </form>
            ) : (
              <form onSubmit={handlePasteUpload} className="upload-form">
                <label className="input-field">
                  <span>Title *</span>
                  <input
                    type="text"
                    placeholder="e.g. Senior Frontend Developer"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </label>
                <label className="input-field">
                  <span>Company</span>
                  <input
                    type="text"
                    placeholder="e.g. Google"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                  />
                </label>
                <label className="input-field">
                  <span>Job Description Text *</span>
                  <textarea
                    placeholder="Paste the job description here..."
                    value={pasteText}
                    onChange={(e) => setPasteText(e.target.value)}
                    rows={10}
                    required
                  />
                </label>
                <button type="submit" className={`solid ${uploading ? 'btn--analyzing btn--pulse' : ''} ${pasteAnalysisComplete ? 'btn--success' : ''}`}
                  disabled={!pasteText.trim() || !title.trim() || uploading}>
                  {uploading ? (
                    <><Loader2 size={16} className="btn-spinner" /> Analyzing...</>
                  ) : pasteAnalysisComplete ? (
                    <><CheckCircle2 size={16} /> Analysis Complete</>
                  ) : (
                    <><FileText size={16} /> Analyze JD</>
                  )}
                </button>
              </form>
            )}
          </div>

          {selectedJd && (
            <div className="panel analysis-results">
              <div className="panel-header">
                <h2>{selectedJd.title}</h2>
                <p>{selectedJd.company || 'No company specified'}</p>
                <div className="panel-header-actions">
                  {!selectedJd.is_analyzed && (
                    <button
                      type="button"
                      className={`solid small ${analyzing === selectedJd.id ? 'btn--analyzing btn--pulse' : ''} ${reanalyzeComplete === selectedJd.id ? 'btn--success' : ''}`}
                      onClick={() => reanalyzeJD(selectedJd.id)}
                      disabled={analyzing === selectedJd.id}
                    >
                      {analyzing === selectedJd.id ? (
                        <><Loader2 size={15} className="btn-spinner" /> Analyzing...</>
                      ) : reanalyzeComplete === selectedJd.id ? (
                        <><CheckCircle2 size={15} /> Complete</>
                      ) : (
                        'Analyze Now'
                      )}
                    </button>
                  )}
                  {selectedJd.is_analyzed && (
                    <button
                      type="button"
                      className={`ghost small ${analyzing === selectedJd.id ? 'btn--analyzing' : ''} ${reanalyzeComplete === selectedJd.id ? 'btn--success' : ''}`}
                      onClick={() => reanalyzeJD(selectedJd.id)}
                      disabled={analyzing === selectedJd.id}
                    >
                      {analyzing === selectedJd.id ? (
                        <><Loader2 size={15} className="btn-spinner" /> Re-analyzing...</>
                      ) : reanalyzeComplete === selectedJd.id ? (
                        <><CheckCircle2 size={15} /> Complete</>
                      ) : (
                        'Re-analyze'
                      )}
                    </button>
                  )}
                </div>
              </div>

              {selectedJd.required_skills?.length > 0 && (
                <div className="analysis-section">
                  <h3>Required Skills</h3>
                  <div className="skill-tags">
                    {selectedJd.required_skills.map((skill, idx) => (
                      <span key={idx} className="skill-tag required">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedJd.preferred_skills?.length > 0 && (
                <div className="analysis-section">
                  <h3>Preferred Skills</h3>
                  <div className="skill-tags">
                    {selectedJd.preferred_skills.map((skill, idx) => (
                      <span key={idx} className="skill-tag preferred">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedJd.technologies?.length > 0 && (
                <div className="analysis-section">
                  <h3>Technologies</h3>
                  <div className="skill-tags">
                    {selectedJd.technologies.map((tech, idx) => (
                      <span key={idx} className="skill-tag tech">{tech}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedJd.soft_skills?.length > 0 && (
                <div className="analysis-section">
                  <h3>Soft Skills</h3>
                  <div className="skill-tags">
                    {selectedJd.soft_skills.map((skill, idx) => (
                      <span key={idx} className="skill-tag soft">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedJd.responsibilities?.length > 0 && (
                <div className="analysis-section">
                  <h3>Responsibilities</h3>
                  <ul className="responsibility-list">
                    {selectedJd.responsibilities.map((resp, idx) => (
                      <li key={idx}>{resp}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="analysis-meta">
                {selectedJd.experience_years && (
                  <span className="meta-item">{selectedJd.experience_years}</span>
                )}
                {selectedJd.education_requirements && (
                  <span className="meta-item">{selectedJd.education_requirements}</span>
                )}
                <span className="meta-item source">{selectedJd.source.toUpperCase()}</span>
              </div>

              {selectedJd.raw_text && (
                <details className="raw-text-section">
                  <summary>View Raw Text ({selectedJd.raw_text.length} chars)</summary>
                  <pre className="raw-text">{selectedJd.raw_text}</pre>
                </details>
              )}
            </div>
          )}
        </section>

        <section className="jd-list-panel">
          <div className="panel">
            <div className="panel-header">
              <h2>Previously Uploaded ({total})</h2>
              <input
                type="text"
                placeholder="Search JDs..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
                className="search-input"
              />
            </div>
            {loading ? (
              <div className="skeleton-list">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="skeleton-item" />
                ))}
              </div>
            ) : jds.length === 0 ? (
              <p className="empty-state">No job descriptions uploaded yet.</p>
            ) : (
              <>
                <ul className="jd-list">
                  {jds.map((jd) => (
                    <li
                      key={jd.id}
                      className={`${selectedJd?.id === jd.id ? 'selected' : ''} ${!jd.is_analyzed ? 'unanalyzed' : ''}`}
                      onClick={() => viewJD(jd.id)}
                    >
                      <div className="jd-info">
                        <div className="jd-title-row">
                          <strong>{jd.title}</strong>
                          {!jd.is_analyzed && <span className="status-badge pending">Not Analyzed</span>}
                          {jd.is_analyzed && <span className="status-badge analyzed">Analyzed</span>}
                        </div>
                        <span>{jd.company || 'No company'}</span>
                        <span className="jd-date">{new Date(jd.created_at).toLocaleDateString()}</span>
                        {jd.required_skills?.length > 0 && (
                          <div className="skill-tags compact">
                            {jd.required_skills.slice(0, 3).map((skill, idx) => (
                              <span key={idx} className="skill-tag">{skill}</span>
                            ))}
                            {jd.required_skills.length > 3 && (
                              <span className="skill-tag more">+{jd.required_skills.length - 3}</span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="jd-item-actions">
                      <button
                        type="button"
                        className="delete-btn"
                        onClick={(e) => deleteJD(jd.id, e)}
                      >
                        <Trash2 size={14} /> Delete
                      </button>
                      </div>
                    </li>
                  ))}
                </ul>
                {pages > 1 && (
                  <div className="pagination">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage(page - 1)}
                    >
                      Prev
                    </button>
                    <span>Page {page} of {pages}</span>
                    <button
                      type="button"
                      disabled={page >= pages}
                      onClick={() => setPage(page + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default JobDescriptionPage;
