import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { interviewApi } from '../services/api';
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
      alert('Failed to start interview');
    }
  };

  return (
    <div className="setup-shell">
      <div className="setup-card">
        <div className="setup-header">
          <p className="setup-eyebrow">Interview Setup</p>
          <h1>Prepare your session</h1>
          <p className="setup-subtitle">
            Select your role, difficulty, and interview type to begin.
          </p>
        </div>

        <div className="setup-form">
          <label className="setup-field">
            <span>Role</span>
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              <option>Backend Developer</option>
              <option>Frontend Developer</option>
              <option>SDE</option>
              <option>ML Engineer</option>
            </select>
          </label>
          <label className="setup-field">
            <span>Difficulty</span>
            <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </label>
          <label className="setup-field">
            <span>Interview Type</span>
            <select value={type} onChange={(event) => setType(event.target.value)}>
              <option>Technical</option>
              <option>HR</option>
              <option>Coding</option>
              <option>System Design</option>
            </select>
          </label>
        </div>

        <button type="button" className="setup-cta" onClick={handleStart}>
          Start Interview
        </button>
      </div>
    </div>
  );
};

export default InterviewSetupPage;
