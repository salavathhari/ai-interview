import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewApi, API_BASE_URL, getAccessToken } from '../services/api';
import { usePreferences } from '../contexts/PreferencesContext';
import { useToast } from '../components/ui/Toast';
import {
  Volume2, VolumeX, Mic, SkipForward, Pause, Play,
  RotateCcw, Repeat, Square, Rocket, RefreshCw
} from 'lucide-react';
import './InterviewPage.css';

type InterviewStatus = 'connecting' | 'answering' | 'evaluating' | 'feedback' | 'finished';
type TimerState = 'IDLE' | 'RUNNING' | 'PAUSED' | 'WARNING' | 'SUBMITTED' | 'TIMEOUT' | 'EVALUATING';

const InterviewPage: React.FC = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const { soundAlerts, emailNotif } = usePreferences();
    const { toast } = useToast();
    const soundAlertsRef = useRef(soundAlerts);
    const emailNotifRef = useRef(emailNotif);
    
    const [status, setStatus] = useState<InterviewStatus>('connecting');
    const [timerState, setTimerState] = useState<TimerState>('IDLE');
    const [question, setQuestion] = useState<any>(null);
    const [feedback, setFeedback] = useState<any>(null);
    const [answer, setAnswer] = useState('');
    const [progress, setProgress] = useState({ current: 0, total: 5 });
    const [isRecording, setIsRecording] = useState(false);
    const [remainingSeconds, setRemainingSeconds] = useState(0);
    const [timeLimit, setTimeLimit] = useState(90);
    const [, setQuestionMetrics] = useState<any[]>([]);
    
    const [isAISpeaking, setIsAISpeaking] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [voiceSpeed, setVoiceSpeed] = useState(1);
    const [isReconnecting, setIsReconnecting] = useState(false);
    const [networkError, setNetworkError] = useState<string | null>(null);

    const pauseStartRef = useRef<number | null>(null);
    const evaluationStartRef = useRef<number | null>(null);
    const currentQuestionIdRef = useRef<string | number | null>(null);
    const currentMetricsRef = useRef<any | null>(null);
    const answerRef = useRef('');
    const statusRef = useRef<InterviewStatus>('connecting');
    const isMutedRef = useRef(isMuted);
    const deadlineRef = useRef<number | null>(null);
    const autoSubmittedRef = useRef(false);
    const warningTriggeredRef = useRef(false);
    const criticalTriggeredRef = useRef(false);
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    
    const synthesisRef = useRef<SpeechSynthesis | null>(null);
    const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
    const recognitionRef = useRef<any>(null);
    const silenceTimerRef = useRef<number | null>(null);

    useEffect(() => {
        answerRef.current = answer;
    }, [answer]);

    useEffect(() => {
        statusRef.current = status;
    }, [status]);

    useEffect(() => {
        isMutedRef.current = isMuted;
    }, [isMuted]);

    useEffect(() => {
        soundAlertsRef.current = soundAlerts;
    }, [soundAlerts]);

    useEffect(() => {
        emailNotifRef.current = emailNotif;
    }, [emailNotif]);

    // Setup Speech Synthesis & Recognition
    useEffect(() => {
        if ('speechSynthesis' in window) {
            synthesisRef.current = window.speechSynthesis;
        }

        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => setIsRecording(true);

            recognition.onresult = (event: any) => {
                let currentTranscript = '';
                for (let i = 0; i < event.results.length; i++) {
                    currentTranscript += event.results[i][0].transcript;
                }
                setAnswer(currentTranscript);

                // Silence detection for auto-submit
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = window.setTimeout(() => {
                    if (statusRef.current === 'answering' && answerRef.current.trim().length > 0) {
                        stopListening();
                        submitAnswer(false);
                    }
                }, 3000); // 3 seconds of silence
            };

            recognition.onerror = (event: any) => {
                console.error("Speech recognition error", event.error);
                if (event.error === 'not-allowed') {
                    setNetworkError("Microphone access denied. Please enable it in your browser settings.");
                }
                setIsRecording(false);
            };

            recognition.onend = () => {
                setIsRecording(false);
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
            };

            recognitionRef.current = recognition;
        }

        return () => {
            if (synthesisRef.current) synthesisRef.current.cancel();
            if (recognitionRef.current) recognitionRef.current.stop();
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        };
    }, []);

    const speakText = (text: string, isQuestion: boolean = true) => {
        if (!synthesisRef.current || isMutedRef.current) {
            if (isQuestion && statusRef.current === 'answering') startListening();
            return;
        }
        synthesisRef.current.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = voiceSpeed;
        utteranceRef.current = utterance;

        utterance.onstart = () => setIsAISpeaking(true);
        utterance.onend = () => {
            setIsAISpeaking(false);
            if (isQuestion && statusRef.current === 'answering') {
                startListening();
            }
        };
        utterance.onerror = () => setIsAISpeaking(false);

        synthesisRef.current.speak(utterance);
    };

    const stopSpeaking = () => {
        if (synthesisRef.current) {
            synthesisRef.current.cancel();
            setIsAISpeaking(false);
        }
    };

    const replayQuestion = () => {
        if (question?.question_text) {
            speakText(question.question_text, true);
        }
    };

    const startListening = () => {
        if (!recognitionRef.current || statusRef.current !== 'answering') return;
        try {
            recognitionRef.current.start();
        } catch (err) {
            console.debug('Recognition already started', err);
        }
    };

    const stopListening = () => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    };

    const playWarningSound = () => {
        if (!soundAlertsRef.current) return;
        try {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            if (!AudioContextClass) return;
            const audioContext = new AudioContextClass();
            const oscillator = audioContext.createOscillator();
            const gain = audioContext.createGain();

            oscillator.frequency.value = 660;
            gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.08, audioContext.currentTime + 0.03);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.25);
            oscillator.connect(gain);
            gain.connect(audioContext.destination);
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.28);
        } catch (err) {
            console.debug('Timer warning sound unavailable', err);
        }
    };

    const playCriticalSound = () => {
        if (!soundAlertsRef.current) return;
        try {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            if (!AudioContextClass) return;
            const audioContext = new AudioContextClass();

            for (let i = 0; i < 3; i++) {
                const oscillator = audioContext.createOscillator();
                const gain = audioContext.createGain();
                const start = audioContext.currentTime + i * 0.15;
                oscillator.frequency.value = 880;
                gain.gain.setValueAtTime(0.0001, start);
                gain.gain.exponentialRampToValueAtTime(0.12, start + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.1);
                oscillator.connect(gain);
                gain.connect(audioContext.destination);
                oscillator.start(start);
                oscillator.stop(start + 0.12);
            }
        } catch (err) {
            console.debug('Critical timer sound unavailable', err);
        }
    };

    const submitAnswer = (wasAutoSubmitted = false) => {
        if (statusRef.current !== 'answering' && !wasAutoSubmitted) return;
        if (autoSubmittedRef.current && wasAutoSubmitted) return;

        stopSpeaking();
        stopListening();

        if (wasAutoSubmitted) {
            autoSubmittedRef.current = true;
            setTimerState('TIMEOUT');
            if (emailNotifRef.current) {
                toast('warning', 'Time ran out — answer auto-submitted');
            }
        } else {
            setTimerState('SUBMITTED');
        }

        const elapsedSeconds = Math.max(0, timeLimit - remainingSeconds);
        if (currentMetricsRef.current) {
            currentMetricsRef.current.time_taken = elapsedSeconds;
            currentMetricsRef.current.time_limit = timeLimit;
            currentMetricsRef.current.was_auto_submitted = wasAutoSubmitted;
            currentMetricsRef.current.warning_triggered = warningTriggeredRef.current;
        }
        pauseStartRef.current = Date.now();
        evaluationStartRef.current = Date.now();
        socketRef.current?.send(JSON.stringify({
            type: 'answer',
            answer: answerRef.current,
            was_auto_submitted: wasAutoSubmitted,
            warning_triggered: warningTriggeredRef.current
        }));
        setStatus('evaluating');
        setTimerState('EVALUATING');
    };

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            navigate('/login');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
        const ws = new WebSocket(`${protocol}//${wsHost}/ws/interview/${sessionId}?token=${token}`);
        socketRef.current = ws;

        ws.onopen = () => console.log('Connected to interview');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'question') {
                const now = Date.now();
                if (currentMetricsRef.current && pauseStartRef.current) {
                    const pauseDuration = Math.round((now - pauseStartRef.current) / 1000);
                    currentMetricsRef.current.pause_duration = pauseDuration;
                    setQuestionMetrics((prev) => [...prev, currentMetricsRef.current]);
                }

                const incomingId = data.question_id ?? data.id ?? `q-${data.index ?? 0}`;
                const incomingLimit = data.time_limit ?? 90;
                const incomingDeadline = data.server_deadline_at ? new Date(data.server_deadline_at).getTime() : Date.now() + incomingLimit * 1000;
                const incomingRemaining = Math.max(0, Math.ceil((incomingDeadline - Date.now()) / 1000));
                currentQuestionIdRef.current = incomingId;
                currentMetricsRef.current = {
                    question_id: incomingId,
                    time_taken: 0,
                    time_limit: incomingLimit,
                    pause_duration: 0,
                    evaluation_time: 0,
                    was_auto_submitted: false,
                    warning_triggered: Boolean(data.timer_state === 'WARNING')
                };
                pauseStartRef.current = null;
                evaluationStartRef.current = null;
                deadlineRef.current = incomingDeadline;
                autoSubmittedRef.current = false;
                warningTriggeredRef.current = Boolean(data.timer_state === 'WARNING');
                criticalTriggeredRef.current = false;
                
                setQuestion(data);
                setProgress({ current: data.index, total: data.total });
                setStatus('answering');
                setTimerState(incomingRemaining <= 15 ? 'WARNING' : 'RUNNING');
                setAnswer('');
                setFeedback(null);
                setTimeLimit(incomingLimit);
                setRemainingSeconds(incomingRemaining);
                
                // Voice Interview Feature: AI Speaks Question
                speakText(data.question_text, true);

            } else if (data.type === 'transcription') {
                // Ignore backend transcription when using native Voice APIs
            } else if (data.type === 'feedback') {
                if (evaluationStartRef.current) {
                    const evaluationTime = Math.round((Date.now() - evaluationStartRef.current) / 1000);
                    if (currentMetricsRef.current) {
                        currentMetricsRef.current.evaluation_time = evaluationTime;
                    }
                    evaluationStartRef.current = null;
                }
                setFeedback(data);
                setTimerState(data.timer_state === 'TIMEOUT' ? 'TIMEOUT' : 'SUBMITTED');
                setStatus('feedback');
                
                if (emailNotifRef.current) {
                    toast('info', 'Question evaluated — check your feedback');
                }
                
                // Voice Interview Feature: AI Speaks Feedback
                speakText(`${data.feedback}. ${data.improvement_tips || ''}`, false);

            } else if (data.type === 'completed') {
                setStatus('finished');
                setTimerState('IDLE');
                if (emailNotifRef.current) {
                    toast('success', 'Interview completed — your report is ready');
                }
            } else if (data.type === 'error') {
                setNetworkError(data.message);
            }
        };

        ws.onclose = (event) => {
            if (event.code === 1000 || event.code === 4005) {
                setStatus('finished');
                setTimerState('IDLE');
            } else if (event.code !== 1000 && reconnectAttemptsRef.current < 3 && statusRef.current !== 'finished') {
                setIsReconnecting(true);
                reconnectAttemptsRef.current += 1;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 8000);
                setTimeout(() => {
                    if (statusRef.current !== 'finished') {
                        console.log(`Reconnecting attempt ${reconnectAttemptsRef.current}...`);
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const token = getAccessToken();
                        if (token) {
                            const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
                            const newWs = new WebSocket(`${protocol}//${wsHost}/ws/interview/${sessionId}?token=${token}`);
                            socketRef.current = newWs;
                            newWs.onopen = ws.onopen;
                            newWs.onmessage = ws.onmessage;
                            newWs.onclose = ws.onclose;
                            newWs.onerror = ws.onerror;
                            setIsReconnecting(false);
                        }
                    }
                }, delay);
            } else {
                console.log('WS Closed', event);
                setIsReconnecting(false);
            }
        };

        const handleVisibilityChange = () => {
            if (document.hidden) {
                socketRef.current?.send(JSON.stringify({ 
                    type: 'cheating_event', 
                    event: 'tab_switch', 
                    details: 'User switched tabs or minimized the browser.' 
                }));
            }
        };

        const handlePaste = () => {
            socketRef.current?.send(JSON.stringify({ 
                type: 'cheating_event', 
                event: 'paste', 
                details: 'User pasted content into the answer box.' 
            }));
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('paste', handlePaste);

        return () => {
            ws.close();
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            window.removeEventListener('paste', handlePaste);
            stopSpeaking();
            stopListening();
        };
    }, [sessionId, navigate]);

    useEffect(() => {
        if (status === 'answering') {
            const timer = window.setInterval(() => {
                if (!deadlineRef.current) return;
                const nextRemaining = Math.max(0, Math.ceil((deadlineRef.current - Date.now()) / 1000));
                setRemainingSeconds(nextRemaining);

                if (nextRemaining <= 15 && nextRemaining > 0) {
                    setTimerState('WARNING');
                    if (!warningTriggeredRef.current) {
                        warningTriggeredRef.current = true;
                        playWarningSound();
                        socketRef.current?.send(JSON.stringify({
                            type: 'timer_warning',
                            question_id: currentQuestionIdRef.current
                        }));
                    }
                    if (nextRemaining <= 5 && nextRemaining > 0 && !criticalTriggeredRef.current) {
                        criticalTriggeredRef.current = true;
                        playCriticalSound();
                    }
                } else if (nextRemaining > 15) {
                    setTimerState('RUNNING');
                }

                if (nextRemaining <= 0 && !autoSubmittedRef.current) {
                    submitAnswer(true);
                }
            }, 250);
            return () => window.clearInterval(timer);
        }
        return undefined;
    }, [status, timeLimit, remainingSeconds]);

    const handleSubmit = () => {
        if (!answer.trim()) return;
        submitAnswer(false);
    };

    const handleNext = () => {
        stopSpeaking();
        if (progress.current === progress.total) {
            // Voice interview done → proceed to coding round
            setStatus('finished');
            setTimerState('IDLE');
        } else {
            socketRef.current?.send(JSON.stringify({ type: 'next_question' }));
            setStatus('evaluating');
            setTimerState('EVALUATING');
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    };

    const [isPaused, setIsPaused] = useState(false);

    const togglePause = () => {
        if (isPaused) {
            socketRef.current?.send(JSON.stringify({ type: 'resume' }));
            setIsPaused(false);
        } else {
            socketRef.current?.send(JSON.stringify({ type: 'pause' }));
            setIsPaused(true);
        }
    };

    const toggleMute = () => {
        setIsMuted(prev => {
            if (!prev) stopSpeaking();
            return !prev;
        });
    };

    const skipQuestion = () => {
        stopSpeaking();
        stopListening();
        socketRef.current?.send(JSON.stringify({ type: 'skip' }));
        setStatus('evaluating');
        setTimerState('EVALUATING');
    };

    const repeatQuestion = () => {
        socketRef.current?.send(JSON.stringify({ type: 'repeat' }));
    };

    const dismissError = () => setNetworkError(null);

    const timerTone = remainingSeconds <= 5 ? 'critical' : remainingSeconds <= 15 ? 'warning' : 'safe';
    const timerProgress = Math.max(0, Math.min(100, (remainingSeconds / Math.max(timeLimit, 1)) * 100));

    const statusLabel = () => {
        if (status === 'evaluating') return 'Evaluating answer...';
        if (status === 'feedback') return 'Generating next question...';
        if (isAISpeaking) return 'AI is Speaking...';
        if (isRecording) return 'Listening...';
        return 'Ready for your answer';
    };

    if (status === 'connecting') return (
        <div className="interview-state">
            {isReconnecting ? 'Reconnecting to your AI Interviewer...' : 'Connecting to your AI Interviewer...'}
        </div>
    );
    if (status === 'finished') return (
        <div className="interview-state">
            <h2>Voice Interview Complete!</h2>
            <p>Great job! Now let's test your coding skills.</p>
            <div style={{ display: 'flex', gap: 12, marginTop: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => navigate(`/coding/${sessionId}`)} className="primary" style={{ fontSize: 16, padding: '12px 28px' }}>
                    <Rocket size={18} /> Start Coding Round
                </button>
                <button onClick={() => navigate('/dashboard')} className="secondary" style={{ fontSize: 14, padding: '10px 20px' }}>
                    Skip & Go to Dashboard
                </button>
            </div>
            <div style={{ marginTop: 24, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                <p style={{ fontSize: 14, color: 'var(--muted)', marginBottom: 12 }}>Want to try again?</p>
                <button
                    onClick={async () => {
                        try {
                            const res = await interviewApi.retry({ role: question?.topic || 'Technical', difficulty: 'Medium', interview_type: 'Technical' });
                            navigate(`/interview/${res.data.id}`);
                        } catch {
                            setNetworkError('Failed to start retry interview');
                        }
                    }}
                    className="secondary"
                    style={{ fontSize: 14, padding: '10px 20px' }}
                >
                    <RefreshCw size={16} /> Retry Interview
                </button>
            </div>
        </div>
    );

    return (
        <div className="interview-shell">
            {networkError && (
                <div className="network-error-banner">
                    <span>{networkError}</span>
                    <button onClick={dismissError} className="dismiss-btn">✕</button>
                </div>
            )}
            {isReconnecting && (
                <div className="reconnecting-banner">
                    Reconnecting... Attempt {reconnectAttemptsRef.current}/3
                </div>
            )}
            <header className="interview-header">
                <div>
                    <p className="eyebrow">Live Voice Interview</p>
                    <h1>AI Technical Interview</h1>
                </div>
                <div className="meta">
                    <span>Question {progress.current} / {progress.total}</span>
                    <div className={`timer ${timerTone} ${timerState === 'WARNING' ? 'pulse' : ''}`} aria-live="polite">
                        <span>{formatTime(remainingSeconds)}</span>
                        <small>{timerState}</small>
                        <div className="timer-track">
                            <div className="timer-fill" style={{ width: `${timerProgress}%` }} />
                        </div>
                    </div>
                </div>
            </header>

            <section className="question-card">
                <div className="question-meta">
                    <span>{question?.topic || 'Technical'}</span>
                    <span>{question?.difficulty || 'Medium'}</span>
                </div>
                <h2>{question?.question_text}</h2>
                <div className="voice-controls">
                    <button onClick={replayQuestion} className="control-btn" title="Replay Question" disabled={isAISpeaking}>
                        <RotateCcw size={14} /> Replay
                    </button>
                    <button onClick={repeatQuestion} className="control-btn" title="Request AI to repeat">
                        <Repeat size={14} /> Repeat
                    </button>
                    <button onClick={stopSpeaking} className="control-btn danger-text" title="Stop Speaking" disabled={!isAISpeaking}>
                        <Square size={14} /> Stop AI
                    </button>
                    <button onClick={toggleMute} className={`control-btn ${isMuted ? 'muted' : ''}`} title="Mute AI">
                        {isMuted ? <><VolumeX size={14} /> Muted</> : <><Volume2 size={14} /> Mute AI</>}
                    </button>
                    <button onClick={skipQuestion} className="control-btn skip-btn" title="Skip this question">
                        <SkipForward size={14} /> Skip
                    </button>
                    <button onClick={togglePause} className={`control-btn ${isPaused ? 'pause-active' : ''}`} title={isPaused ? 'Resume interview' : 'Pause interview'}>
                        {isPaused ? <><Play size={14} /> Resume</> : <><Pause size={14} /> Pause</>}
                    </button>
                    <div className="speed-control">
                        <label htmlFor="voice-speed">Speed: {voiceSpeed}x</label>
                        <input 
                            id="voice-speed"
                            type="range" 
                            min="0.5" max="2" step="0.1" 
                            value={voiceSpeed} 
                            onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))} 
                        />
                    </div>
                </div>
            </section>

            <section className="answer-card">
                <div className="answer-header">
                    <h3>Your Answer</h3>
                    <div className="status-indicators">
                        {isAISpeaking && <span className="indicator speaking-indicator pulse"><Volume2 size={12} /> AI Speaking...</span>}
                        {isRecording && <span className="indicator listening-indicator pulse"><Mic size={12} /> Listening...</span>}
                        <span className="status-pill">{statusLabel()}</span>
                    </div>
                </div>

                {status === 'answering' && (
                    <>
                        <div className={`transcript-panel ${isRecording ? 'recording-active' : ''}`}>
                            <textarea
                                value={answer}
                                onChange={(e) => setAnswer(e.target.value)}
                                placeholder="Start speaking... Your transcript will appear here live."
                                className="transcript-area"
                            />
                        </div>
                        <div className="answer-actions">
                            <button onClick={handleSubmit} className="primary">Submit Answer</button>
                            <button onClick={isRecording ? stopListening : startListening} className={isRecording ? 'danger' : 'secondary'}>
                                {isRecording ? <><Square size={14} /> Stop Recording & Submit</> : <><Mic size={14} /> Start Recording</>}
                            </button>
                        </div>
                    </>
                )}

                {status === 'evaluating' && <div className="thinking">Evaluating answer...</div>}

                {status === 'feedback' && feedback && (
                    <div className="feedback-card">
                        <div className="feedback-header">
                            <h4>AI Feedback</h4>
                            <span>{feedback.score}/10</span>
                        </div>
                        <p>{feedback.feedback}</p>
                        <div className="tips">
                            <strong>Improvement Tips</strong>
                            <p>{feedback.improvement_tips}</p>
                        </div>
                        <button onClick={handleNext} className="primary">
                            {progress.current === progress.total ? 'Finish Interview' : 'Next Question'}
                        </button>
                    </div>
                )}
            </section>

            <section className="progress-card">
                <div className="progress-header">
                    <span>Progress</span>
                    <span>Question {progress.current} / {progress.total}</span>
                </div>
                <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${Math.min((progress.current / progress.total) * 100, 100)}%` }} />
                </div>
                <p className="progress-status">{statusLabel()}</p>
            </section>
        </div>
    );
};

export default InterviewPage;
