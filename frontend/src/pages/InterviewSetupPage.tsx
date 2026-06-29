import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { interviewApi } from '../services/api';
import {
  ArrowLeft, Mic, Code2, FileText, BarChart3,
  Briefcase, Gauge, Layers, Play
} from 'lucide-react';
import './InterviewSetupPage.css';

const InterviewSetupPage: React.FC = () => {
  const [role, setRole] = useState('Backend Developer');
  const [difficulty, setDifficulty] = useState('Medium');
  const [type, setType] = useState('Technical');
  const navigate = useNavigate();

  const handleStart = async () => {
    try {
      const response = await interviewApi.create({ 
        role, 
        difficulty, 
        interview_type: type 
      });
      navigate(`/interview/${response.data.id}`);
    } catch (error) {
      console.error(error);
    }
  };

  const getPreviewItems = () => {
    const items = [];
    if (type === 'Technical' || type === 'Coding') {
      items.push({ icon: Code2, color: 'blue', text: 'Technical Q&A with adaptive follow-ups' });
    }
    if (type === 'HR') {
      items.push({ icon: Mic, color: 'green', text: 'Behavioral & HR scenario questions' });
    }
    if (type === 'System Design') {
      items.push({ icon: Layers, color: 'purple', text: 'System design architecture discussion' });
    }
    if (type === 'Coding') {
      items.push({ icon: Code2, color: 'purple', text: 'Live coding with AI code review' });
    }
    items.push({ icon: BarChart3, color: 'amber', text: 'Real-time scoring & instant feedback' });
    items.push({ icon: FileText, color: 'green', text: 'Detailed post-interview report' });
    return items;
  };

  return (
    <div className="setup-shell">
      <Link to="/dashboard" className="setup-back">
        <ArrowLeft size={15} /> Back to Dashboard
      </Link>

      <div className="setup-card">
        {/* Header */}
        <div className="setup-header">
          <div className="setup-icon">
            <Mic size={26} />
          </div>
          <p className="setup-eyebrow">Interview Setup</p>
          <h1>Configure your session</h1>
          <p className="setup-subtitle">
            Choose your target role, difficulty level, and interview format to begin.
          </p>
        </div>

        {/* Form */}
        <div className="setup-form">
          <label className="setup-field">
            <span><Briefcase size={13} /> Target Role</span>
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              <option>Backend Developer</option>
              <option>Frontend Developer</option>
              <option>Full Stack Developer</option>
              <option>SDE</option>
              <option>ML Engineer</option>
              <option>Data Engineer</option>
              <option>DevOps Engineer</option>
            </select>
          </label>

          <label className="setup-field">
            <span><Gauge size={13} /> Difficulty</span>
            <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </label>

          <label className="setup-field">
            <span><Layers size={13} /> Interview Type</span>
            <select value={type} onChange={(event) => setType(event.target.value)}>
              <option>Technical</option>
              <option>HR</option>
              <option>Coding</option>
              <option>System Design</option>
            </select>
          </label>
        </div>

        {/* Preview */}
        <div className="setup-preview">
          <h3>What to expect</h3>
          <div className="preview-items">
            {getPreviewItems().map((item, i) => (
              <div className="preview-item" key={i}>
                <span className={`preview-dot ${item.color}`} />
                <item.icon size={14} style={{ color: 'var(--muted)', flexShrink: 0 }} />
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="setup-divider" />

        {/* CTA */}
        <div className="setup-cta-section">
          <button type="button" className="setup-cta" onClick={handleStart}>
            <Play size={17} /> Start Interview
          </button>
          <p className="setup-hint">
            Session adapts to your responses in real time
          </p>
        </div>
      </div>
    </div>
  );
};

export default InterviewSetupPage;
