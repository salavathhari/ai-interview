import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import { Zap, Mic, Code2, BarChart3 } from 'lucide-react';
import './AuthPage.css';

const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();
    const { toast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            const role = localStorage.getItem('role');
            toast('success', 'Welcome back!');
            if (role === 'admin') navigate('/admin/dashboard');
            else if (role === 'recruiter') navigate('/recruiter/dashboard');
            else navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Invalid credentials');
            toast('error', err.message || 'Login failed');
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
                    <h1>Welcome back to your interview prep</h1>
                    <p>
                        Pick up where you left off. Your AI-powered interview practice
                        sessions, analytics, and progress are all waiting for you.
                    </p>
                    <div className="al-features">
                        <div className="al-feature">
                            <div className="al-feature-icon"><Mic size={18} /></div>
                            <div className="al-feature-text">
                                <h3>Voice &amp; Coding Sessions</h3>
                                <p>Continue your practice with AI-driven interviews</p>
                            </div>
                        </div>
                        <div className="al-feature">
                            <div className="al-feature-icon"><Code2 size={18} /></div>
                            <div className="al-feature-text">
                                <h3>Live Coding IDE</h3>
                                <p>Solve problems with real-time AI feedback</p>
                            </div>
                        </div>
                        <div className="al-feature">
                            <div className="al-feature-icon"><BarChart3 size={18} /></div>
                            <div className="al-feature-text">
                                <h3>Performance Insights</h3>
                                <p>Track your improvement over time</p>
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
                        <h2>Sign in</h2>
                        <p className="auth-subtitle">
                            Enter your credentials to access your account
                        </p>
                    </div>

                    {error && <div className="auth-error">{error}</div>}

                    <form onSubmit={handleSubmit} className="auth-form">
                        <label className="auth-field">
                            <span>Email</span>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                placeholder="you@company.com"
                                autoFocus
                            />
                        </label>
                        <label className="auth-field">
                            <span>Password</span>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="Enter your password"
                            />
                        </label>
                        <button type="submit" className="auth-submit" disabled={loading}>
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <p className="auth-switch">
                        Don't have an account? <Link to="/signup">Create one</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
