import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import { Zap, Mic, Code2, BarChart3 } from 'lucide-react';
import './AuthPage.css';

const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('candidate');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { signup } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signup(name, email, password, role);
      toast('success', 'Account created successfully!');
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Signup failed');
      toast('error', err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Left Branding Panel */}
      <div className="auth-left">
        <Link to="/" className="al-brand">
          <span className="al-logo">
            <Zap size={18} />
          </span>
          <span className="al-name">Interview Studio</span>
        </Link>

        <div className="al-content">
          <h1>Start acing your interviews today</h1>
          <p>
            Join thousands of candidates practicing with AI-powered mock interviews.
            Get instant feedback and improve with every session.
          </p>
          <div className="al-features">
            <div className="al-feature">
              <div className="al-feature-icon"><Mic size={18} /></div>
              <div className="al-feature-text">
                <h3>Voice &amp; Coding Sessions</h3>
                <p>Realistic interview simulations with AI</p>
              </div>
            </div>
            <div className="al-feature">
              <div className="al-feature-icon"><Code2 size={18} /></div>
              <div className="al-feature-text">
                <h3>Live Coding IDE</h3>
                <p>Practice with Monaco editor and test cases</p>
              </div>
            </div>
            <div className="al-feature">
              <div className="al-feature-icon"><BarChart3 size={18} /></div>
              <div className="al-feature-text">
                <h3>Performance Insights</h3>
                <p>Detailed analytics on your strengths and gaps</p>
              </div>
            </div>
          </div>
        </div>

        <div className="al-footer">
          &copy; {new Date().getFullYear()} Interview Studio
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-header">
            <h2>Create your account</h2>
            <p className="auth-subtitle">
              Start practicing interviews in under a minute
            </p>
          </div>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <label className="auth-field">
              <span>Full Name</span>
              <input
                type="text"
                placeholder="Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
              />
            </label>
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                placeholder="jane@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <label className="auth-field">
              <span>I am a</span>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="candidate">Candidate</option>
                <option value="recruiter">Recruiter</option>
              </select>
            </label>
            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
