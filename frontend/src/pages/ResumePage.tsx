import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { resumeApi } from '../services/api';
import {
  Upload, FileText, Trash2, Eye, GitBranch,
  CheckCircle2, AlertTriangle, X, Shield, User, Mail,
  Phone, MapPin, Link as LinkIcon, Globe, Layers
} from 'lucide-react';
import './ResumePage.css';

interface Resume {
  id: number;
  filename: string;
  extracted_text: string;
  skills: string | null;
  content_hash: string | null;
  version: number;
  is_active: boolean;
  parsed_name: string | null;
  parsed_email: string | null;
  parsed_phone: string | null;
  parsed_location: string | null;
  parsed_linkedin: string | null;
  parsed_github: string | null;
  parsed_portfolio: string | null;
  created_at: string;
}

interface UploadResult {
  id: number;
  filename: string;
  skills: string[];
  version: number;
  is_active: boolean;
  parsed_fields: Record<string, string | null>;
  classification: any;
  quality: any;
  duplicate_of: number | null;
  message: string;
}

interface Version {
  id: number;
  version_number: number;
  filename: string;
  content_hash: string | null;
  change_reason: string | null;
  created_at: string | null;
}

interface CompareResult {
  resume_a: { id: number; filename: string; word_count: number };
  resume_b: { id: number; filename: string; word_count: number };
  skills_common: string[];
  skills_only_a: string[];
  skills_only_b: string[];
  skill_overlap_pct: number;
  text_similarity: number;
  length_diff: number;
}

const ResumePage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploaded, setUploaded] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [showVersions, setShowVersions] = useState<number | null>(null);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareSelection, setCompareSelection] = useState<number[]>([]);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [bulkMode, setBulkMode] = useState(false);

  const loadResumes = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await resumeApi.getMyResumes({ per_page: 50, search: searchTerm || undefined });
      setResumes(resp.data);
    } catch (err) {
      console.error('Failed to load resumes:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    loadResumes();
  }, [loadResumes]);

  const handleFile = useCallback((selected: File | null) => {
    if (!selected) return;
    const ext = selected.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setError('Only PDF and DOCX files are allowed.');
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB.');
      return;
    }
    setFile(selected);
    setError(null);
  }, []);

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const dropped = event.dataTransfer.files?.[0] || null;
    handleFile(dropped);
  };

  const pollExtractionStatus = async (resumeId: number): Promise<boolean> => {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const resp = await resumeApi.getResume(resumeId);
        const data = resp.data;
        if (data.processing_status === 'completed') return true;
        if (data.processing_status === 'failed') return false;
      } catch { /* retry */ }
    }
    return false;
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const result: UploadResult = await resumeApi.upload(formData, (pct) => {
        setUploadProgress(pct);
      });
      setFile(null);
      setUploadProgress(0);

      if (result.processing_status === 'pending' || result.processing_status === 'processing') {
        const completed = await pollExtractionStatus(result.id);
        if (completed) {
          const fullResume = await resumeApi.getResume(result.id);
          const data = fullResume.data;
          setUploaded({
            ...result,
            skills: data.skills ? data.skills.split(', ').filter(Boolean) : [],
            parsed_fields: {
              name: data.parsed_name, email: data.parsed_email,
              phone: data.parsed_phone, location: data.parsed_location,
              linkedin: data.parsed_linkedin, github: data.parsed_github,
              portfolio: data.parsed_portfolio,
            },
          });
        } else {
          setUploaded(result);
        }
      } else {
        setUploaded(result);
      }

      loadResumes();
    } catch (err: any) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const deleteResume = async (id: number) => {
    if (!confirm('Are you sure you want to delete this resume and all its analysis data?')) return;
    try {
      await resumeApi.delete(id);
      if (selectedResume?.id === id) setSelectedResume(null);
      loadResumes();
    } catch (error) {
      console.error(error);
    }
  };

  const setActive = async (id: number) => {
    try {
      await resumeApi.setActive(id);
      loadResumes();
    } catch (error) {
      console.error(error);
    }
  };

  const loadVersions = async (resumeId: number) => {
    if (showVersions === resumeId) {
      setShowVersions(null);
      return;
    }
    try {
      const resp = await resumeApi.getVersions(resumeId);
      setVersions(resp.data);
      setShowVersions(resumeId);
    } catch (error) {
      console.error(error);
    }
  };

  const showPreview = (resume: Resume) => {
    setSelectedResume(resume);
    setPreviewText(resume.extracted_text?.substring(0, 2000) || 'No text available');
  };

  const detectedTechnologies = useMemo(() => {
    if (!uploaded?.skills?.length) return [];
    return uploaded.skills.slice(0, 8);
  }, [uploaded]);

  const parsedFields = useMemo(() => {
    return uploaded?.parsed_fields || {};
  }, [uploaded]);

  const renderFieldIcon = (key: string) => {
    const icons: Record<string, React.ReactNode> = {
      name: <User size={13} />,
      email: <Mail size={13} />,
      phone: <Phone size={13} />,
      location: <MapPin size={13} />,
      linkedin: <LinkIcon size={13} />,
      github: <LinkIcon size={13} />,
      portfolio: <Globe size={13} />,
    };
    return icons[key] || null;
  };

  return (
    <div className="resume-shell">
      <header className="resume-header">
        <div>
          <h1>Resume Manager</h1>
          <p>Upload, manage, and compare your resumes. Extract skills for personalized interview sessions.</p>
        </div>
      </header>

      {/* Upload Card */}
      <section className="upload-card">
        <div
          className={`dropzone ${isDragging ? 'dragging' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <div>
            <Upload size={32} style={{ color: 'var(--muted)', marginBottom: 12 }} />
            <h2>Drag & Drop Resume</h2>
            <p>PDF or DOCX files accepted (max 10MB)</p>
            <label className="browse-button">
              Browse Files
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(event) => handleFile(event.target.files?.[0] || null)}
              />
            </label>
            {file && (
              <div className="file-info">
                <FileText size={14} style={{ color: 'var(--accent-strong)' }} />
                <span className="file-name">{file.name}</span>
                <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>
        </div>

        {uploading && (
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
            <span className="progress-text">{uploadProgress}%</span>
          </div>
        )}

        <button
          type="button"
          className="upload-action"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          <Upload size={15} /> {uploading ? 'Uploading...' : 'Upload Resume'}
        </button>
        {error && <p className="error-text">{error}</p>}
      </section>

      {/* Upload Result */}
      {uploaded && (
        <section className="analysis-card">
          <div className="result-success">
            <h3><CheckCircle2 size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Upload Successful</h3>
            <div className="result-grid">
              {Object.entries(parsedFields).map(([key, value]) => {
                if (!value) return null;
                const isLink = key === 'linkedin' || key === 'github' || key === 'portfolio';
                return (
                  <div className="result-field" key={key}>
                    {renderFieldIcon(key)}{' '}
                    <strong>{key.charAt(0).toUpperCase() + key.slice(1)}:</strong>{' '}
                    {isLink ? (
                      <a href={value.startsWith('http') ? value : '#'} target="_blank" rel="noopener noreferrer">
                        {value}
                      </a>
                    ) : value}
                  </div>
                );
              })}
            </div>
            {uploaded.quality && (
              <div className="result-field" style={{ marginTop: 8 }}>
                <Shield size={13} style={{ verticalAlign: 'middle' }} />{' '}
                <strong>Quality Score:</strong> {Math.round(uploaded.quality.quality_score || 0)}/100
              </div>
            )}
            {uploaded.duplicate_of && (
              <div className="result-field duplicate-warning">
                <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />{' '}
                <strong>Note:</strong> This content is similar to resume #{uploaded.duplicate_of}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Extracted Skills */}
      <section className="analysis-card">
        <div className="analysis-block">
          <h3><Layers size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Extracted Skills</h3>
          <div className="tag-grid">
            {detectedTechnologies.length > 0 ? (
              detectedTechnologies.map((skill: string) => (
                <span className="tag" key={skill}>{skill}</span>
              ))
            ) : (
              <p className="empty-text">Upload a resume to see extracted skills.</p>
            )}
          </div>
        </div>
      </section>

      {/* Resume List */}
      <section className="analysis-card">
        <div className="analysis-block">
          <div className="section-header">
            <h3><FileText size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Your Resumes ({resumes.length})</h3>
            <div className="header-actions">
              <input
                type="text"
                placeholder="Search resumes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
              <button
                className={`action-btn ${bulkMode ? 'active' : ''}`}
                onClick={() => {
                  setBulkMode(!bulkMode);
                  setSelectedIds([]);
                  setCompareMode(false);
                  setCompareSelection([]);
                }}
              >
                {bulkMode ? 'Cancel' : 'Bulk Select'}
              </button>
              {bulkMode && selectedIds.length > 0 && (
                <button
                  className="action-btn danger"
                  onClick={async () => {
                    if (!confirm(`Delete ${selectedIds.length} resume(s)?`)) return;
                    try {
                      await resumeApi.bulkDelete(selectedIds);
                      setSelectedIds([]);
                      setBulkMode(false);
                      loadResumes();
                    } catch (err) {
                      alert('Failed to delete resumes');
                    }
                  }}
                >
                  <Trash2 size={12} /> Delete {selectedIds.length}
                </button>
              )}
              <button
                className={`action-btn ${compareMode ? 'active' : ''}`}
                onClick={() => {
                  setCompareMode(!compareMode);
                  setCompareSelection([]);
                  setCompareResult(null);
                  setBulkMode(false);
                  setSelectedIds([]);
                }}
              >
                {compareMode ? 'Cancel' : <><Layers size={12} /> Compare</>}
              </button>
              {compareMode && compareSelection.length === 2 && (
                <button
                  className="action-btn primary"
                  onClick={async () => {
                    try {
                      const resp = await resumeApi.compare(compareSelection[0], compareSelection[1]);
                      setCompareResult(resp.data);
                    } catch (err) {
                      alert('Failed to compare resumes');
                    }
                  }}
                >
                  Run Compare
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div className="skeleton-list">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton-item" />
              ))}
            </div>
          ) : resumes.length === 0 ? (
            <p className="empty-text">No resumes uploaded yet.</p>
          ) : (
            <ul className="resume-list">
              {resumes.map((resume) => (
                <li
                  key={resume.id}
                  className={`resume-item ${resume.is_active ? 'active' : ''} ${selectedResume?.id === resume.id ? 'selected' : ''} ${selectedIds.includes(resume.id) ? 'bulk-selected' : ''} ${compareSelection.includes(resume.id) ? 'compare-selected' : ''}`}
                >
                  <div className="resume-item-main">
                    <div className="resume-item-checkbox">
                      {(bulkMode || compareMode) && (
                        <input
                          type="checkbox"
                          checked={bulkMode ? selectedIds.includes(resume.id) : compareSelection.includes(resume.id)}
                          onChange={() => {
                            if (bulkMode) {
                              setSelectedIds(prev =>
                                prev.includes(resume.id) ? prev.filter(id => id !== resume.id) : [...prev, resume.id]
                              );
                            } else if (compareMode) {
                              setCompareSelection(prev =>
                                prev.includes(resume.id)
                                  ? prev.filter(id => id !== resume.id)
                                  : prev.length < 2 ? [...prev, resume.id] : [prev[1], resume.id]
                              );
                            }
                          }}
                        />
                      )}
                    </div>
                    <div className="resume-item-info">
                      <div className="resume-item-header">
                        <strong>{resume.filename}</strong>
                        {resume.is_active && <span className="active-badge">Active</span>}
                        <span className="version-badge">v{resume.version}</span>
                      </div>
                      <div className="resume-item-meta">
                        {resume.parsed_name && <span>{resume.parsed_name}</span>}
                        {resume.parsed_email && <span>{resume.parsed_email}</span>}
                        <span>{new Date(resume.created_at).toLocaleDateString()}</span>
                      </div>
                      {resume.skills && (
                        <div className="resume-item-skills">
                          {resume.skills.split(',').slice(0, 5).map((s) => (
                            <span className="tag small" key={s.trim()}>{s.trim()}</span>
                          ))}
                          {resume.skills.split(',').length > 5 && (
                            <span className="tag small more">
                              +{resume.skills.split(',').length - 5}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="resume-item-actions">
                      {!resume.is_active && (
                        <button
                          type="button"
                          className="action-btn activate"
                          onClick={() => setActive(resume.id)}
                          title="Set as active resume"
                        >
                          <CheckCircle2 size={12} /> Activate
                        </button>
                      )}
                      <button
                        type="button"
                        className="action-btn preview"
                        onClick={() => showPreview(resume)}
                      >
                        <Eye size={12} /> Preview
                      </button>
                      <button
                        type="button"
                        className="action-btn versions"
                        onClick={() => loadVersions(resume.id)}
                      >
                        <GitBranch size={12} /> Versions
                      </button>
                      <button
                        type="button"
                        className="action-btn delete"
                        onClick={() => deleteResume(resume.id)}
                      >
                        <Trash2 size={12} /> Delete
                      </button>
                    </div>
                  </div>

                  {showVersions === resume.id && versions.length > 0 && (
                    <div className="versions-panel">
                      <h4>Version History</h4>
                      {versions.map((v) => (
                        <div key={v.id} className="version-item">
                          <span className="version-num">v{v.version_number}</span>
                          <span className="version-date">
                            {v.created_at ? new Date(v.created_at).toLocaleString() : 'N/A'}
                          </span>
                          <span className="version-reason">{v.change_reason || 'N/A'}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Preview Section */}
      {selectedResume && previewText && (
        <section className="analysis-card preview-section">
          <div className="section-header">
            <h3><Eye size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Resume Preview: {selectedResume.filename}</h3>
            <button
              type="button"
              className="close-btn"
              onClick={() => { setSelectedResume(null); setPreviewText(null); }}
            >
              <X size={14} /> Close
            </button>
          </div>
          <pre className="preview-text">{previewText}</pre>
          {selectedResume.extracted_text && selectedResume.extracted_text.length > 2000 && (
            <p className="preview-truncated">
              Showing first 2000 characters of {selectedResume.extracted_text.length} total.
            </p>
          )}
        </section>
      )}

      {/* Compare Result */}
      {compareResult && (
        <section className="analysis-card compare-section">
          <div className="section-header">
            <h3><Layers size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Comparison Result</h3>
            <button type="button" className="close-btn" onClick={() => setCompareResult(null)}>
              <X size={14} /> Close
            </button>
          </div>
          <div className="compare-grid">
            <div className="compare-col">
              <h4>{compareResult.resume_a.filename}</h4>
              <p>{compareResult.resume_a.word_count} words</p>
              <p>{compareResult.skills_only_a.length} unique skills</p>
            </div>
            <div className="compare-col">
              <h4>{compareResult.resume_b.filename}</h4>
              <p>{compareResult.resume_b.word_count} words</p>
              <p>{compareResult.skills_only_b.length} unique skills</p>
            </div>
          </div>
          <div className="compare-stats">
            <div className="stat">
              <strong>Skill Overlap:</strong> {compareResult.skill_overlap_pct}%
            </div>
            <div className="stat">
              <strong>Text Similarity:</strong> {(compareResult.text_similarity * 100).toFixed(1)}%
            </div>
            <div className="stat">
              <strong>Length Diff:</strong> {compareResult.length_diff > 0 ? '+' : ''}{compareResult.length_diff} words
            </div>
          </div>
          {compareResult.skills_common.length > 0 && (
            <div className="compare-skills">
              <h4>Common Skills</h4>
              <div className="tag-grid">
                {compareResult.skills_common.map((s) => <span className="tag" key={s}>{s}</span>)}
              </div>
            </div>
          )}
          {compareResult.skills_only_a.length > 0 && (
            <div className="compare-skills">
              <h4>Only in {compareResult.resume_a.filename}</h4>
              <div className="tag-grid">
                {compareResult.skills_only_a.map((s) => <span className="tag highlight-a" key={s}>{s}</span>)}
              </div>
            </div>
          )}
          {compareResult.skills_only_b.length > 0 && (
            <div className="compare-skills">
              <h4>Only in {compareResult.resume_b.filename}</h4>
              <div className="tag-grid">
                {compareResult.skills_only_b.map((s) => <span className="tag highlight-b" key={s}>{s}</span>)}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export default ResumePage;
