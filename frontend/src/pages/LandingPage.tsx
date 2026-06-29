import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Play, Code2, FileText, Layers, BarChart3, Shield,
  ArrowRight, CheckCircle2, Zap, Star, ChevronRight
} from 'lucide-react';
import './LandingPage.css';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: [0.25, 0.4, 0.25, 1] as const },
  }),
};

const features = [
  {
    icon: Play,
    color: 'blue',
    title: 'Voice Interviews',
    desc: 'Real-time AI voice conversations with adaptive follow-up questions that simulate actual interview panels.',
  },
  {
    icon: Code2,
    color: 'green',
    title: 'Live Coding',
    desc: 'Full IDE with Monaco editor, multi-language support, test case execution, and AI code review.',
  },
  {
    icon: FileText,
    color: 'purple',
    title: 'ATS Resume Analysis',
    desc: 'Scan your resume against ATS systems with detailed scoring, keyword matching, and optimization tips.',
  },
  {
    icon: Layers,
    color: 'amber',
    title: 'Skill Gap Analysis',
    desc: 'Compare your skills against job descriptions to identify gaps and get personalized learning paths.',
  },
  {
    icon: BarChart3,
    color: 'rose',
    title: 'Performance Analytics',
    desc: 'Track your progress over time with detailed charts, skill breakdowns, and improvement recommendations.',
  },
  {
    icon: Shield,
    color: 'cyan',
    title: 'Integrity Monitoring',
    desc: 'Built-in tab-switch detection and paste monitoring to ensure authentic practice sessions.',
  },
];

const testimonials = [
  {
    quote: 'Interview Studio completely changed how I prepare. The AI feedback is shockingly accurate and helped me land my dream role at a FAANG company.',
    name: 'Sarah Chen',
    role: 'Software Engineer at Google',
    rating: 5,
  },
  {
    quote: 'The coding challenges and real-time feedback are leagues beyond any other mock interview tool. I went from failing interviews to getting multiple offers.',
    name: 'Marcus Johnson',
    role: 'Full-Stack Developer at Stripe',
    rating: 5,
  },
  {
    quote: 'The skill gap analysis showed me exactly what to study. Within two weeks, I felt confident walking into my interviews.',
    name: 'Priya Patel',
    role: 'Backend Engineer at Amazon',
    rating: 5,
  },
];

const steps = [
  { num: '01', title: 'Choose Your Track', desc: 'Select from technical, behavioral, or system design interview tracks tailored to your role.' },
  { num: '02', title: 'Practice with AI', desc: 'Engage in realistic voice conversations or live coding sessions with an adaptive AI interviewer.' },
  { num: '03', title: 'Get Instant Feedback', desc: 'Receive detailed analytics, score breakdowns, and actionable improvement tips after every session.' },
];

function LandingPage() {
  return (
    <div className="landing">
      {/* ── Nav ── */}
      <header className="ln">
        <Link to="/" className="ln-brand">
          <span className="ln-logo">
            <Zap size={18} />
          </span>
          <span className="ln-name">Interview Studio</span>
        </Link>
        <nav className="ln-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it Works</a>
          <a href="#testimonials">Testimonials</a>
        </nav>
        <div className="ln-actions">
          <Link className="btn-ghost" to="/login">Sign in</Link>
          <Link className="btn-primary" to="/dashboard">
            Get Started <ArrowRight size={16} />
          </Link>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-badge">
          <span className="badge-dot" />
          AI-Powered Interview Platform
        </div>
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Ace Your Next Interview<br />
          <span className="hero-accent">with AI Precision</span>
        </motion.h1>
        <motion.p
          className="hero-sub"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          Practice with adaptive AI interviewers, solve live coding challenges,
          and get detailed analytics that show exactly where to improve — all
          before your real interview.
        </motion.p>
        <motion.div
          className="hero-cta"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Link className="btn-primary btn-lg" to="/dashboard">
            Start Practicing <ArrowRight size={18} />
          </Link>
          <Link className="btn-outline btn-lg" to="/signup">
            Create Free Account
          </Link>
        </motion.div>
        <motion.div
          className="hero-proof"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="proof-avatars">
            <div className="avatar" style={{ background: '#dbeafe' }}>S</div>
            <div className="avatar" style={{ background: '#dcfce7' }}>M</div>
            <div className="avatar" style={{ background: '#fce7f3' }}>P</div>
            <div className="avatar" style={{ background: '#fef3c7' }}>A</div>
          </div>
          <div className="proof-text">
            <strong>2,400+</strong> candidates practicing this week
          </div>
        </motion.div>

        {/* Visual Card */}
        <div className="hero-visual" aria-hidden="true">
          <div className="hv-glow hv-glow-1" />
          <div className="hv-glow hv-glow-2" />
          <motion.div
            className="hv-card"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.3 }}
          >
            <div className="hv-card-top">
              <span className="hv-live">
                <span className="live-dot" /> Live Session
              </span>
              <span className="hv-duration">12:34</span>
            </div>
            <div className="hv-divider" />
            <p className="hv-question">Explain the trade-offs between REST and gRPC for a microservices architecture.</p>
            <div className="hv-meters">
              <div className="hv-meter">
                <div className="hv-meter-head">
                  <span>Accuracy</span>
                  <span className="hv-meter-val">82%</span>
                </div>
                <div className="meter-track">
                  <div className="meter-bar meter-bar-blue" style={{ width: '82%' }} />
                </div>
              </div>
              <div className="hv-meter">
                <div className="hv-meter-head">
                  <span>Confidence</span>
                  <span className="hv-meter-val">74%</span>
                </div>
                <div className="meter-track">
                  <div className="meter-bar meter-bar-green" style={{ width: '74%' }} />
                </div>
              </div>
              <div className="hv-meter">
                <div className="hv-meter-head">
                  <span>Completeness</span>
                  <span className="hv-meter-val">91%</span>
                </div>
                <div className="meter-track">
                  <div className="meter-bar meter-bar-purple" style={{ width: '91%' }} />
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="hero-stats">
          {[
            { val: '4x', label: 'Faster feedback cycles' },
            { val: '96%', label: 'Candidate confidence lift' },
            { val: '15+', label: 'Interview roles supported' },
            { val: '50+', label: 'Technical topics covered' },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              className="stat"
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-40px' }}
              variants={fadeUp}
            >
              <span className="stat-val">{s.val}</span>
              <span className="stat-label">{s.label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Logos ── */}
      <section className="logos-bar">
        <p className="logos-title">Trusted by candidates interviewing at</p>
        <div className="logos-row">
          {['Google', 'Amazon', 'Meta', 'Microsoft', 'Apple', 'Stripe'].map((name) => (
            <span key={name} className="logo-item">{name}</span>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="features">
        <motion.div
          className="section-head"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <span className="eyebrow">Features</span>
          <h2>Everything you need to ace your interview</h2>
          <p>A complete toolkit designed to simulate real technical interviews with AI-powered evaluation.</p>
        </motion.div>
        <div className="features-grid">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              className="feature-card"
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-30px' }}
              variants={fadeUp}
            >
              <div className={`fc-icon fc-${f.color}`}>
                <f.icon size={22} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="how-it-works">
        <motion.div
          className="section-head"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <span className="eyebrow">How It Works</span>
          <h2>Three steps to interview confidence</h2>
          <p>Get started in minutes and start building the skills that matter.</p>
        </motion.div>
        <div className="steps-grid">
          {steps.map((s, i) => (
            <motion.div
              key={s.num}
              className="step-card"
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-30px' }}
              variants={fadeUp}
            >
              <span className="step-num">{s.num}</span>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              {i < steps.length - 1 && <ChevronRight className="step-arrow" size={20} />}
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section id="testimonials" className="testimonials">
        <motion.div
          className="section-head"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <span className="eyebrow">Testimonials</span>
          <h2>Loved by candidates worldwide</h2>
          <p>See how Interview Studio has helped professionals land their dream roles.</p>
        </motion.div>
        <div className="testimonials-grid">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              className="testimonial-card"
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-30px' }}
              variants={fadeUp}
            >
              <div className="tc-stars">
                {Array.from({ length: t.rating }).map((_, j) => (
                  <Star key={j} size={16} fill="currentColor" />
                ))}
              </div>
              <p className="tc-quote">"{t.quote}"</p>
              <div className="tc-author">
                <div className="tc-avatar" style={{ background: ['#dbeafe', '#dcfce7', '#fce7f3'][i] }}>
                  {t.name[0]}
                </div>
                <div>
                  <strong>{t.name}</strong>
                  <span>{t.role}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="cta-section">
        <motion.div
          className="cta-card"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2>Ready to ace your next interview?</h2>
          <p>Join thousands of candidates already practicing with AI-powered mock interviews.</p>
          <div className="cta-actions">
            <Link className="btn-white btn-lg" to="/dashboard">
              Start Practicing Free <ArrowRight size={18} />
            </Link>
          </div>
          <div className="cta-perks">
            <span><CheckCircle2 size={16} /> No credit card required</span>
            <span><CheckCircle2 size={16} /> Free tier available</span>
            <span><CheckCircle2 size={16} /> Cancel anytime</span>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-grid">
          <div className="footer-brand">
            <Link to="/" className="ln-brand">
              <span className="ln-logo"><Zap size={18} /></span>
              <span className="ln-name">Interview Studio</span>
            </Link>
            <p>AI-powered interview practice to help you land your dream job.</p>
          </div>
          <div className="footer-col">
            <h4>Product</h4>
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <Link to="/signup">Pricing</Link>
          </div>
          <div className="footer-col">
            <h4>Resources</h4>
            <Link to="/login">Sign In</Link>
            <Link to="/signup">Sign Up</Link>
            <a href="#testimonials">Testimonials</a>
          </div>
          <div className="footer-col">
            <h4>Company</h4>
            <a href="#">About</a>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} Interview Studio. Built with AI for better interviews.</p>
          <div className="footer-socials">
            <a href="#" aria-label="Twitter">Twitter</a>
            <a href="#" aria-label="GitHub">GitHub</a>
            <a href="#" aria-label="LinkedIn">LinkedIn</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
