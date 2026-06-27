import Editor from '@monaco-editor/react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Code2,
  Cpu,
  EyeOff,
  History,
  Loader2,
  MemoryStick,
  Play,
  Send,
  Sparkles,
  Terminal,
  Trophy,
  X,
  Zap,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { codingApi } from '../services/api';
import './CodingPage.css';

// ─── Types ────────────────────────────────────────────────────────────────────

type Language = 'python' | 'java' | 'cpp' | 'javascript' | 'typescript';

const LANGUAGES: { value: Language; label: string; monacoId: string }[] = [
  { value: 'python',     label: 'Python 3',     monacoId: 'python'     },
  { value: 'java',       label: 'Java',          monacoId: 'java'       },
  { value: 'cpp',        label: 'C++',           monacoId: 'cpp'        },
  { value: 'javascript', label: 'JavaScript',    monacoId: 'javascript' },
  { value: 'typescript', label: 'TypeScript',    monacoId: 'typescript' },
];

type TestCaseResult = {
  test_number: number;
  passed: boolean;
  runtime_ms?: number;
  memory_kb?: number;
  input?: string;
  expected?: string;
  actual?: string;
  error?: string;
};

type RunResult = {
  status: string;
  runtime_ms?: number;
  memory_kb?: number;
  output?: string;
  all_passed?: boolean;
  public_results?: TestCaseResult[];
  hidden_total?: number;
  hidden_passed?: number;
};

type SubmitResult = RunResult & {
  id?: number;
  correctness_score?: number;
  ai_feedback?: string;
  ai_score?: number;
  time_complexity?: string;
  space_complexity?: string;
  test_results?: TestCaseResult[];
};

type Challenge = {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  supported_languages?: Language[];
  starter_codes?: Record<Language, string>;
  topics?: string[];
  constraints?: string;
  examples?: { input: string; output: string; explanation?: string }[];
  test_cases?: { input: string; expected: string }[];
  time_limit_ms?: number;
};

type HistoryItem = {
  id: number;
  status: string;
  language?: string;
  runtime_ms?: number;
  memory_kb?: number;
  correctness_score?: number;
  ai_score?: number;
  is_final: boolean;
  created_at: string;
};

type ConsoleTab = 'testcases' | 'output' | 'aireview';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const statusColor = (status: string) => {
  if (status === 'Accepted') return 'success';
  if (status === 'Running' || status === 'Submitting') return 'pending';
  return 'error';
};

const difficultyClass = (d: string) => d?.toLowerCase() || 'easy';

const formatMs = (ms?: number) => (ms != null ? `${ms} ms` : '—');
const formatKb = (kb?: number) => (kb != null ? `${(kb / 1024).toFixed(1)} MB` : '—');

const TIMER_LIMIT = 45 * 60; // 45 minutes

// ─── Component ────────────────────────────────────────────────────────────────

const CodingPage = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();

  // Session & challenge
  const [codingSessionId, setCodingSessionId] = useState<number | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Editor
  const [language, setLanguage] = useState<Language>('python');
  const [code, setCode] = useState('');
  const [savedDraft, setSavedDraft] = useState<string | null>(null);
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSavedCode = useRef<string>('');
  const resetCodeActionRef = useRef<(() => void) | null>(null);

  // Execution
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // UI
  const [activeTab, setActiveTab] = useState<ConsoleTab>('testcases');
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Timer
  const [secondsLeft, setSecondsLeft] = useState(TIMER_LIMIT);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ─── Init ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { navigate('/login'); return; }

    const init = async () => {
      setLoading(true);
      try {
        // Start or resume coding session
        const interviewSessionId = sessionId ? parseInt(sessionId) : undefined;
        const sessionRes = await codingApi.startSession({
          interview_session_id: interviewSessionId,
          language: 'python',
        });
        const sess = sessionRes.data;
        setCodingSessionId(sess.id);

        const ch: Challenge = sess.challenge;
        setChallenge(ch);

        // Load all challenges for selector
        const allRes = await codingApi.getChallenges();
        setChallenges(allRes.data);

        // Set default language and starter code
        const defaultLang: Language = 'python';
        setLanguage(defaultLang);
        setCode(ch.starter_codes?.[defaultLang] || '');

        // Start timer
        startTimer();
      } catch (err: any) {
        console.error(err);
        // Fallback: load challenges directly
        try {
          const allRes = await codingApi.getChallenges();
          setChallenges(allRes.data);
          const first = allRes.data[0];
          if (first) {
            setChallenge(first);
            setCode(first.starter_codes?.python || first.starter_code || '');
          }
          startTimer();
        } catch {
          setError('Failed to load coding session. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    init();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [sessionId, navigate]);

  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setSecondsLeft(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  // ─── Auto-Save ────────────────────────────────────────────────────────────

  useEffect(() => {
    if (code && codingSessionId) {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = setTimeout(() => {
        try {
          localStorage.setItem(`coding_draft_${codingSessionId}`, JSON.stringify({ language, code, savedAt: Date.now() }));
        } catch { /* storage full */ }
      }, 2000);
    }
    return () => { if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current); };
  }, [code, language, codingSessionId]);

  // Restore draft on mount
  useEffect(() => {
    if (codingSessionId) {
      try {
        const raw = localStorage.getItem(`coding_draft_${codingSessionId}`);
        if (raw) {
          const draft = JSON.parse(raw);
          if (draft.code && draft.language) {
            setSavedDraft(draft.code);
            setLanguage(draft.language);
            setCode(draft.code);
          }
        }
      } catch { /* corrupt data */ }
    }
  }, [codingSessionId]);

  const dismissDraft = () => {
    setSavedDraft(null);
    if (codingSessionId) localStorage.removeItem(`coding_draft_${codingSessionId}`);
  };

  const restoreDraft = () => {
    if (savedDraft) {
      setCode(savedDraft);
      setSavedDraft(null);
    }
  };

  // ─── Language Switch ───────────────────────────────────────────────────────

  const switchLanguage = (lang: Language) => {
    if (lang === language) return;
    if (code.trim() && code.trim() !== (challenge?.starter_codes?.[language] || '').trim()) {
      const confirmed = window.confirm(
        `Switching to ${lang} will replace your current code. Continue?`
      );
      if (!confirmed) return;
    }
    setLanguage(lang);
    if (challenge?.starter_codes?.[lang]) {
      setCode(challenge.starter_codes[lang]);
    }
    setRunResult(null);
    setSubmitResult(null);
  };

  // ─── Challenge Switch ──────────────────────────────────────────────────────

  const switchChallenge = async (challengeId: number) => {
    try {
      const res = await codingApi.getChallenge(challengeId);
      const ch: Challenge = res.data;
      setChallenge(ch);
      setCode(ch.starter_codes?.[language] || '');
      setRunResult(null);
      setSubmitResult(null);
      setSubmitted(false);
    } catch { setError('Failed to load challenge.'); }
  };

  // ─── Run Code ─────────────────────────────────────────────────────────────

  const runCode = async () => {
    if (!challenge || isRunning || isSubmitting) return;
    setIsRunning(true);
    setRunResult({ status: 'Running', output: 'Executing against public test cases...' });
    setActiveTab('testcases');
    try {
      const res = await codingApi.runCode({
        challenge_id: challenge.id,
        code,
        language,
        coding_session_id: codingSessionId ?? undefined,
      });
      setRunResult(res.data);
    } catch (err: any) {
      setRunResult({
        status: 'Runtime Error',
        output: err?.response?.data?.detail || 'Execution failed.',
        public_results: [],
      });
    } finally {
      setIsRunning(false);
    }
  };

  // ─── Submit Code ──────────────────────────────────────────────────────────

  const submitCode = async () => {
    if (!challenge || isRunning || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitResult({ status: 'Submitting', output: 'Running all test cases + AI review...' });
    setActiveTab('testcases');
    try {
      const res = await codingApi.submitCode({
        challenge_id: challenge.id,
        code,
        language,
        coding_session_id: codingSessionId ?? undefined,
        session_id: sessionId ? parseInt(sessionId) : undefined,
      });
      setSubmitResult(res.data);
      setSubmitted(true);
      setActiveTab('aireview');
      if (timerRef.current) clearInterval(timerRef.current);
      // Refresh history
      loadHistory();
    } catch (err: any) {
      setSubmitResult({
        status: 'Runtime Error',
        output: err?.response?.data?.detail || 'Submission failed.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── History ──────────────────────────────────────────────────────────────

  const loadHistory = async () => {
    if (!challenge) return;
    try {
      const res = await codingApi.getSubmissions({
        coding_session_id: codingSessionId ?? undefined,
        challenge_id: challenge.id,
      });
      setHistory(res.data.submissions || []);
    } catch { /* silent */ }
  };

  const toggleHistory = () => {
    if (!showHistory) loadHistory();
    setShowHistory(h => !h);
  };

  // ─── Timer Format ─────────────────────────────────────────────────────────

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };
  const timerClass = secondsLeft <= 300 ? 'critical' : secondsLeft <= 600 ? 'warning' : 'safe';

  // ─── Active Result ─────────────────────────────────────────────────────────

  const activeResult = submitResult || runResult;
  const isProcessing = isRunning || isSubmitting;

  // Public TC results from either run or submit
  const publicResults: TestCaseResult[] = submitResult?.test_results || activeResult?.public_results || [];
  const hiddenTotal = activeResult?.hidden_total ?? (submitResult ? (challenge?.test_cases?.length || 0) : 0);
  const hiddenPassed = activeResult?.hidden_passed ?? 0;

  const monacoLang = LANGUAGES.find(l => l.value === language)?.monacoId || 'python';

  // ─── Render ───────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="coding-loading">
        <Loader2 className="spin" size={40} />
        <p>AI is selecting your coding challenge…</p>
      </div>
    );
  }

  return (
    <div className="coding-shell">
      {/* ── Top Bar ── */}
      <header className="coding-topbar">
        <div className="coding-topbar-left">
          <Code2 size={20} className="coding-logo-icon" />
          <div>
            <p className="coding-eyebrow">Coding Round</p>
            <h1 className="coding-title">{challenge?.title || 'Loading…'}</h1>
          </div>
        </div>

        <div className="coding-topbar-center">
          <label className="challenge-select">
            <span>Problem</span>
            <select
              value={challenge?.id ?? ''}
              onChange={e => switchChallenge(Number(e.target.value))}
              disabled={challenges.length === 0 || submitted}
            >
              {challenges.map(c => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
            <ChevronDown size={14} />
          </label>
        </div>

        <div className="coding-topbar-right">
          <button
            className="history-btn"
            onClick={toggleHistory}
            title="Submission History"
          >
            <History size={16} />
            {showHistory ? 'Hide History' : 'History'}
          </button>
          <div className={`coding-timer ${timerClass}`}>
            <Clock3 size={14} />
            {formatTime(secondsLeft)}
          </div>
          {submitted && (
            <>
              <button
                className="finish-btn"
                onClick={() => navigate(sessionId ? `/report/${sessionId}` : '/dashboard')}
              >
                <Trophy size={15} /> Finish
              </button>
              <button
                className="run-btn"
                onClick={async () => {
                  try {
                    const res = await codingApi.retry({
                      interview_session_id: sessionId ? parseInt(sessionId) : undefined,
                      language,
                    });
                    const sess = res.data;
                    setCodingSessionId(sess.id);
                    setChallenge(sess.challenge);
                    setCode(sess.challenge?.starter_codes?.[language] || '');
                    setRunResult(null);
                    setSubmitResult(null);
                    setSubmitted(false);
                    setActiveTab('testcases');
                    setSecondsLeft(TIMER_LIMIT);
                    startTimer();
                  } catch { setError('Failed to retry. Please try again.'); }
                }}
              >
                🔄 Retry
              </button>
            </>
          )}
        </div>
      </header>

      {error && (
        <div className="coding-alert">
          <AlertTriangle size={15} /> {error}
          <button onClick={() => setError('')}><X size={14} /></button>
        </div>
      )}

      {savedDraft && (
        <div className="coding-alert" style={{ background: 'rgba(35, 134, 54, 0.1)', borderColor: 'rgba(35, 134, 54, 0.4)', color: 'var(--green)' }}>
          <span>You have a saved draft from a previous session.</span>
          <button onClick={restoreDraft} style={{ color: 'var(--green)', fontWeight: 700, marginRight: 8 }}>Restore</button>
          <button onClick={dismissDraft}><X size={14} /></button>
        </div>
      )}

      {/* ── History Drawer ── */}
      {showHistory && (
        <div className="history-drawer">
          <div className="history-drawer-header">
            <span><History size={14} /> Submission History</span>
            <button onClick={() => setShowHistory(false)}><X size={14} /></button>
          </div>
          {history.length === 0 ? (
            <p className="history-empty">No submissions yet.</p>
          ) : (
            <table className="history-table">
              <thead>
                <tr>
                  <th>#</th><th>Status</th><th>Lang</th><th>Correctness</th><th>AI Score</th><th>Runtime</th><th>Time</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={h.id}>
                    <td>{history.length - i}</td>
                    <td><span className={`status-pill ${statusColor(h.status)}`}>{h.status}</span></td>
                    <td><span className="lang-badge">{h.language}</span></td>
                    <td>{h.correctness_score != null ? `${h.correctness_score}%` : '—'}</td>
                    <td>{h.ai_score != null ? `${h.ai_score}/10` : '—'}</td>
                    <td>{formatMs(h.runtime_ms)}</td>
                    <td>{new Date(h.created_at).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── Main Workspace ── */}
      <main className="coding-workspace">
        {/* ── Left: Problem Pane ── */}
        <section className="problem-pane">
          <div className="problem-header">
            <div className="problem-header-top">
              <h2>{challenge?.title}</h2>
              <span className={`difficulty-badge ${difficultyClass(challenge?.difficulty || '')}`}>
                {challenge?.difficulty}
              </span>
            </div>
            <div className="topic-tags">
              {challenge?.topics?.map(t => (
                <span key={t} className="topic-tag">{t}</span>
              ))}
            </div>
          </div>

          <div className="problem-body">
            <article className="problem-section">
              <p className="problem-description">{challenge?.description}</p>
            </article>

            {challenge?.examples && challenge.examples.length > 0 && (
              <article className="problem-section">
                <h3>Examples</h3>
                {challenge.examples.map((ex, i) => (
                  <div className="example-block" key={i}>
                    <div className="example-label">Example {i + 1}</div>
                    <div className="example-row">
                      <div className="example-part">
                        <span>Input</span>
                        <pre>{ex.input}</pre>
                      </div>
                      <div className="example-part">
                        <span>Output</span>
                        <pre>{ex.output}</pre>
                      </div>
                    </div>
                    {ex.explanation && (
                      <p className="example-explanation">
                        <strong>Explanation:</strong> {ex.explanation}
                      </p>
                    )}
                  </div>
                ))}
              </article>
            )}

            {challenge?.constraints && (
              <article className="problem-section">
                <h3>Constraints</h3>
                <pre className="constraints-block">{challenge.constraints}</pre>
              </article>
            )}

            <article className="problem-section">
              <h3>Notes</h3>
              <ul className="notes-list">
                <li>Read input from <code>stdin</code> and write output to <code>stdout</code>.</li>
                <li>Match output exactly as shown in examples.</li>
                <li>Time limit: {challenge?.time_limit_ms ?? 5000}ms per test case.</li>
                <li>
                  {(challenge?.test_cases?.length ?? 0)} public
                  {' '}+ {(challenge as any)?.hidden_test_cases?.length ?? 3} hidden test cases.
                </li>
              </ul>
            </article>
          </div>
        </section>

        {/* ── Right: Editor + Console ── */}
        <section className="editor-pane">
          {/* Toolbar */}
          <div className="editor-toolbar">
            <div className="lang-selector-group">
              {LANGUAGES.map(lang => (
                <button
                  key={lang.value}
                  className={`lang-tab ${language === lang.value ? 'active' : ''}`}
                  onClick={() => switchLanguage(lang.value)}
                  disabled={submitted}
                >
                  {lang.label}
                </button>
              ))}
            </div>
            <div className="editor-actions">
              <button
                id="run-code-btn"
                className="run-btn"
                onClick={runCode}
                disabled={isProcessing || !challenge || submitted}
              >
                {isRunning ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
                {isRunning ? 'Running…' : 'Run'}
              </button>
              <button
                id="submit-code-btn"
                className="submit-btn"
                onClick={submitCode}
                disabled={isProcessing || !challenge || submitted}
              >
                {isSubmitting ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
                {isSubmitting ? 'Submitting…' : submitted ? 'Submitted ✓' : 'Submit'}
              </button>
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="monaco-frame">
            <Editor
              height="100%"
              language={monacoLang}
              value={code}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbersMinChars: 3,
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                padding: { top: 14, bottom: 14 },
                automaticLayout: true,
                readOnly: submitted,
                fontLigatures: true,
                cursorBlinking: 'smooth',
                smoothScrolling: true,
              }}
              onChange={value => setCode(value ?? '')}
            />
          </div>

          {/* Console Panel */}
          <div className={`console-panel ${activeResult ? statusColor(activeResult.status) : 'idle'}`}>
            {/* Tabs */}
            <div className="console-tabs">
              <button
                className={`console-tab ${activeTab === 'testcases' ? 'active' : ''}`}
                onClick={() => setActiveTab('testcases')}
              >
                <Terminal size={13} /> Test Cases
                {publicResults.length > 0 && (
                  <span className={`tc-badge ${publicResults.every(r => r.passed) ? 'pass' : 'fail'}`}>
                    {publicResults.filter(r => r.passed).length}/{publicResults.length}
                  </span>
                )}
              </button>
              <button
                className={`console-tab ${activeTab === 'output' ? 'active' : ''}`}
                onClick={() => setActiveTab('output')}
              >
                <Cpu size={13} /> Output
              </button>
              {submitResult?.ai_feedback && (
                <button
                  className={`console-tab ${activeTab === 'aireview' ? 'active' : ''} ai-tab`}
                  onClick={() => setActiveTab('aireview')}
                >
                  <Sparkles size={13} /> AI Review
                  {submitResult.ai_score != null && (
                    <span className="ai-score-badge">{submitResult.ai_score}/10</span>
                  )}
                </button>
              )}

              {/* Stats row */}
              {activeResult && activeResult.status !== 'Running' && activeResult.status !== 'Submitting' && (
                <div className="console-stats">
                  {activeResult.runtime_ms != null && (
                    <span><Zap size={11} /> {formatMs(activeResult.runtime_ms)}</span>
                  )}
                  {activeResult.memory_kb != null && (
                    <span><MemoryStick size={11} /> {formatKb(activeResult.memory_kb)}</span>
                  )}
                  {activeResult.status === 'Accepted'
                    ? <CheckCircle2 size={15} className="icon-success" />
                    : <AlertTriangle size={15} className="icon-error" />}
                </div>
              )}
            </div>

            {/* Tab: Test Cases */}
            {activeTab === 'testcases' && (
              <div className="tc-panel">
                {isProcessing && (
                  <div className="tc-loading">
                    <Loader2 size={18} className="spin" />
                    <span>{isRunning ? 'Executing…' : 'Running all test cases + AI review…'}</span>
                  </div>
                )}

                {!isProcessing && publicResults.length === 0 && (
                  <div className="tc-empty">
                    Run your code to see test case results here.
                  </div>
                )}

                {!isProcessing && publicResults.length > 0 && (
                  <div className="tc-list">
                    {publicResults.map((tc, i) => (
                      <div key={i} className={`tc-item ${tc.passed ? 'pass' : 'fail'}`}>
                        <div className="tc-item-header">
                          <span className="tc-num">
                            {tc.passed
                              ? <CheckCircle2 size={14} className="icon-success" />
                              : <AlertTriangle size={14} className="icon-error" />}
                            Test {tc.test_number}
                          </span>
                          <span className="tc-meta">
                            {tc.runtime_ms != null && <><Zap size={11} />{tc.runtime_ms}ms</>}
                          </span>
                        </div>
                        {tc.input != null && (
                          <div className="tc-io">
                            <div className="tc-io-row">
                              <span>Input</span>
                              <pre>{tc.input}</pre>
                            </div>
                            <div className="tc-io-row">
                              <span>Expected</span>
                              <pre>{tc.expected}</pre>
                            </div>
                            {!tc.passed && tc.actual != null && (
                              <div className="tc-io-row error">
                                <span>Got</span>
                                <pre>{tc.actual}</pre>
                              </div>
                            )}
                            {!tc.passed && tc.error && tc.actual == null && (
                              <div className="tc-io-row error">
                                <span>Error</span>
                                <pre>{tc.error}</pre>
                              </div>
                            )}
                          </div>
                        )}
                        {tc.input == null && !tc.passed && (
                          <p className="tc-hidden-fail">Hidden test case failed.</p>
                        )}
                        {tc.input == null && tc.passed && (
                          <p className="tc-hidden-pass">Hidden test case passed.</p>
                        )}
                      </div>
                    ))}

                    {/* Hidden TC summary (submit only) */}
                    {submitResult && hiddenTotal > 0 && (
                      <div className={`tc-hidden-summary ${hiddenPassed === hiddenTotal ? 'pass' : 'fail'}`}>
                        <EyeOff size={14} />
                        <span>Hidden Tests: {hiddenPassed} / {hiddenTotal} passed</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Output */}
            {activeTab === 'output' && (
              <div className="output-panel">
                <pre>{activeResult?.output || 'No output yet. Run your code first.'}</pre>
              </div>
            )}

            {/* Tab: AI Review */}
            {activeTab === 'aireview' && submitResult?.ai_feedback && (
              <div className="ai-review-panel">
                <div className="ai-review-header">
                  <div className="ai-score-ring">
                    <svg viewBox="0 0 56 56" className="ai-ring-svg">
                      <circle cx="28" cy="28" r="24" className="ring-track" />
                      <circle
                        cx="28" cy="28" r="24"
                        className="ring-fill"
                        strokeDasharray={`${(submitResult.ai_score ?? 0) / 10 * 150.796} 150.796`}
                      />
                    </svg>
                    <span className="ai-score-text">{submitResult.ai_score?.toFixed(1)}</span>
                  </div>
                  <div className="ai-review-meta">
                    <h4>AI Code Review</h4>
                    <p className="ai-feedback-text">{submitResult.ai_feedback}</p>
                  </div>
                </div>

                <div className="ai-complexity">
                  <div className="complexity-item">
                    <Zap size={14} />
                    <span>Time</span>
                    <strong>{submitResult.time_complexity || '—'}</strong>
                  </div>
                  <div className="complexity-item">
                    <MemoryStick size={14} />
                    <span>Space</span>
                    <strong>{submitResult.space_complexity || '—'}</strong>
                  </div>
                  <div className="complexity-item">
                    <CheckCircle2 size={14} />
                    <span>Correctness</span>
                    <strong>{submitResult.correctness_score?.toFixed(0)}%</strong>
                  </div>
                </div>

                {/* Final verdict */}
                <div className={`final-verdict ${statusColor(submitResult.status)}`}>
                  {submitResult.status === 'Accepted'
                    ? <><Trophy size={18} /> All test cases passed!</>
                    : <><AlertTriangle size={18} /> {submitResult.status}</>}
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

export default CodingPage;
