import { Link } from 'react-router-dom';
import './LandingPage.css';

function LandingPage() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </span>
          <span className="brand-name">Interview Studio</span>
        </Link>
        <div className="nav-actions">
          <Link className="ghost-button" to="/login">Sign in</Link>
          <Link className="solid-button" to="/dashboard">Get Started</Link>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <p className="eyebrow">Realtime practice for technical interviews</p>
          <h1>
            Practice Real AI Interviews
            <br />
            Get Instant Technical Feedback
          </h1>
          <p className="hero-subtitle">
            Sharpen your interview skills with adaptive questions, live coding rounds,
            voice sessions, and detailed analytics that show exactly where to improve.
          </p>
          <div className="hero-actions">
            <Link className="solid-button" to="/dashboard">Start Interview</Link>
            <Link className="outline-button" to="/signup">Create Account</Link>
          </div>
          <div className="hero-stats">
            <div>
              <h3>4x</h3>
              <p>Faster feedback cycles</p>
            </div>
            <div>
              <h3>96%</h3>
              <p>Candidate confidence lift</p>
            </div>
            <div>
              <h3>15+</h3>
              <p>Interview roles supported</p>
            </div>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="glass-card">
            <p className="card-label">Live AI Interview</p>
            <div className="card-line" />
            <p className="card-question">Explain the trade-offs between REST and gRPC.</p>
            <div className="card-meter">
              <span>Accuracy</span>
              <div className="meter">
                <div className="meter-fill" style={{ width: '82%' }} />
              </div>
            </div>
            <div className="card-meter">
              <span>Confidence</span>
              <div className="meter">
                <div className="meter-fill green" style={{ width: '74%' }} />
              </div>
            </div>
            <div className="card-meter">
              <span>Completeness</span>
              <div className="meter">
                <div className="meter-fill purple" style={{ width: '91%' }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="features-header">
          <p className="eyebrow">Features</p>
          <h2>Everything you need to ace your interview</h2>
          <p>A complete toolkit designed to simulate real technical interviews with AI-powered evaluation.</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon blue">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            </div>
            <h3>Voice Interviews</h3>
            <p>Real-time AI voice conversations with adaptive follow-up questions that simulate actual interview panels.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon green">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            </div>
            <h3>Live Coding</h3>
            <p>Full IDE with Monaco editor, multi-language support, test case execution, and AI code review.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon purple">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <h3>ATS Analysis</h3>
            <p>Scan your resume against ATS systems with detailed scoring, keyword matching, and optimization tips.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon amber">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <h3>Skill Gap Analysis</h3>
            <p>Compare your skills against job descriptions to identify gaps and get personalized learning paths.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon rose">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
            </div>
            <h3>Performance Analytics</h3>
            <p>Track your progress over time with detailed charts, skill breakdowns, and improvement recommendations.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon cyan">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <h3>Cheating Detection</h3>
            <p>Built-in tab-switch detection and paste monitoring to ensure authentic practice sessions.</p>
          </div>
        </div>
      </section>

      <section className="cta">
        <div className="cta-card">
          <h2>Ready to ace your next interview?</h2>
          <p>Join thousands of candidates practicing with AI-powered mock interviews.</p>
          <Link className="solid-button cta-button" to="/signup">Get Started Free</Link>
        </div>
      </section>

      <footer className="landing-footer">
        <p>&copy; {new Date().getFullYear()} Interview Studio. Built with AI for better interviews.</p>
      </footer>
    </div>
  );
}

export default LandingPage;
