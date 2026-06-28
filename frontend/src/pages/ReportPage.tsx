import { ArrowLeft, CheckCircle2, Download, Lightbulb, Target, TriangleAlert } from 'lucide-react';
import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { interviewApi, getAccessToken } from '../services/api';
import './ReportPage.css';

type Question = {
  id: number;
  question_text: string;
  topic?: string;
  difficulty?: string;
  score?: number;
  feedback?: string;
  improvement_tips?: string;
};

type InterviewSession = {
  id: number;
  role: string;
  status: string;
  score?: number;
  started_at: string;
  questions: Question[];
};

type ReportSummary = {
  summary?: string;
  strengths?: string[] | string;
  weaknesses?: string[] | string;
  roadmap?: string[] | string;
  confidence_score?: number | string;
};

const normalizeList = (value: string[] | string | undefined, fallback: string[]) => {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (!value) return fallback;

  const items = value
    .split(/\n|(?:\d+\.\s*)|(?:;\s*)/)
    .map((item) => item.replace(/^[-*]\s*/, '').trim())
    .filter(Boolean);

  return items.length > 0 ? items : fallback;
};

const ReportPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      navigate('/login');
      return;
    }

    const loadReport = async () => {
      try {
        let targetSessionId = Number(sessionId);

        if (!targetSessionId) {
          const sessionsResponse = await interviewApi.getMyInterviews();
          const latestCompleted = sessionsResponse.data.find((item: any) => item.status === 'completed') ?? sessionsResponse.data[0];
          targetSessionId = latestCompleted?.id;
        }

        if (!targetSessionId) {
          setError('No interview session is available for reporting yet.');
          return;
        }

        const [sessionResponse, feedbackResponse] = await Promise.all([
          interviewApi.getSession(targetSessionId),
          interviewApi.getFeedback(targetSessionId),
        ]);

        setSession(sessionResponse.data);
        setSummary(feedbackResponse.data);
      } catch (err) {
        console.error(err);
        setError('Unable to load the report.');
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, [navigate, sessionId]);

  const scorePercent = useMemo(() => {
    const score = session?.score ?? 0;
    return Math.max(0, Math.min(100, Math.round(score * 10)));
  }, [session]);

  const fallbackStrengths = useMemo(() => {
    const bestQuestions = [...(session?.questions ?? [])]
      .filter((question) => question.score !== undefined && question.score >= 7)
      .slice(0, 3);
    if (bestQuestions.length === 0) return ['Clear communication on core concepts', 'Consistent attempt structure', 'Good baseline technical readiness'];
    return bestQuestions.map((question) => `${question.topic || 'Technical'} response scored ${question.score}/10`);
  }, [session]);

  const fallbackWeaknesses = useMemo(() => {
    const weakQuestions = [...(session?.questions ?? [])]
      .filter((question) => question.score !== undefined && question.score < 7)
      .slice(0, 3);
    if (weakQuestions.length === 0) return ['Add more depth to edge cases', 'Use more concrete examples', 'Practice concise final summaries'];
    return weakQuestions.map((question) => `${question.topic || 'Technical'} needs more depth`);
  }, [session]);

  const strengths = normalizeList(summary?.strengths, fallbackStrengths);
  const weaknesses = normalizeList(summary?.weaknesses, fallbackWeaknesses);
  const roadmap = normalizeList(summary?.roadmap, [
    'Review weak topics with focused notes and examples.',
    'Practice timed answers with a clear problem, approach, trade-off structure.',
    'Repeat one mixed mock interview and compare score movement.',
  ]);

  const downloadPdf = async () => {
    if (!session) return;
    setDownloading(true);
    try {
      const response = await interviewApi.downloadReport(session.id);
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `interview_report_${session.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      setError('PDF download failed.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <div className="report-state">Preparing report...</div>;
  if (error && !session) return <div className="report-state">{error}</div>;

  return (
    <div className="report-shell">
      <header className="report-header">
        <button type="button" className="back-button" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={16} />
          Dashboard
        </button>
        <button type="button" className="download-button" onClick={downloadPdf} disabled={downloading || !session}>
          <Download size={16} />
          {downloading ? 'Downloading' : 'Download PDF'}
        </button>
      </header>

      {error && <div className="report-alert">{error}</div>}

      <main className="report-card">
        <section className="report-hero">
          <div>
            <p className="report-eyebrow">Interview Report</p>
            <h1>{session?.role}</h1>
            <span>{session?.started_at ? new Date(session.started_at).toLocaleDateString() : 'Recent session'}</span>
          </div>

          <div className="score-circle" style={{ '--score': scorePercent } as CSSProperties}>
            <div>
              <strong>{scorePercent}%</strong>
              <span>Overall Score</span>
            </div>
          </div>
        </section>

        <section className="summary-strip">
          <article>
            <Target size={18} />
            <span>Status</span>
            <strong>{session?.status}</strong>
          </article>
          <article>
            <CheckCircle2 size={18} />
            <span>Questions</span>
            <strong>{session?.questions?.length ?? 0}</strong>
          </article>
          <article>
            <Lightbulb size={18} />
            <span>Confidence</span>
            <strong>{summary?.confidence_score ?? `${scorePercent}%`}</strong>
          </article>
        </section>

        <section className="report-summary">
          <h2>Executive Summary</h2>
          <p>{summary?.summary || 'The session has been evaluated across answer quality, communication, confidence, completeness, and topic coverage.'}</p>
        </section>

        <section className="report-columns">
          <article className="report-section strengths">
            <div className="section-heading">
              <CheckCircle2 size={18} />
              <h2>Strengths</h2>
            </div>
            <ul>
              {strengths.map((item, index) => (
                <li key={`s-${index}`}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="report-section weaknesses">
            <div className="section-heading">
              <TriangleAlert size={18} />
              <h2>Weaknesses</h2>
            </div>
            <ul>
              {weaknesses.map((item, index) => (
                <li key={`w-${index}`}>{item}</li>
              ))}
            </ul>
          </article>
        </section>

        <section className="roadmap-section">
          <div className="section-heading">
            <Lightbulb size={18} />
            <h2>AI Suggestions</h2>
          </div>
          <div className="roadmap-list">
              {roadmap.map((item, index) => (
                <article key={`r-${index}`}>
                <span>{index + 1}</span>
                <p>{item}</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default ReportPage;
