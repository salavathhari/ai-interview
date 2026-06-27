from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.utils import decode_access_token
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.resume import Resume
from app.models.cheating_log import CheatingLog
from app.models.interview_question_metric import InterviewQuestionMetric
from app.models.career import JobDescription
from app.services.ai_service import AIService
import asyncio
import base64
import json
import os
import tempfile
import time
from datetime import datetime, timedelta, timezone

router = APIRouter()

TOTAL_QUESTIONS = 5
WARNING_THRESHOLD_SECONDS = 15
DIFFICULTY_TIME_LIMITS = {
    "easy": 60,
    "medium": 90,
    "hard": 120,
    "coding": 30 * 60,
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_time_limit(question: Question) -> int:
    difficulty = (question.difficulty or "medium").strip().lower()
    topic = (question.topic or "").strip().lower()
    if "coding" in difficulty or "coding" in topic:
        return DIFFICULTY_TIME_LIMITS["coding"]
    return DIFFICULTY_TIME_LIMITS.get(difficulty, DIFFICULTY_TIME_LIMITS["medium"])


def get_or_create_metric(db: Session, session_id: int, question: Question) -> InterviewQuestionMetric:
    metric = db.query(InterviewQuestionMetric).filter(
        InterviewQuestionMetric.session_id == session_id,
        InterviewQuestionMetric.question_id == question.id,
    ).first()

    if not metric:
        metric = InterviewQuestionMetric(
            session_id=session_id,
            question_id=question.id,
            question_start_time=now_utc(),
            time_limit=get_time_limit(question),
            difficulty=question.difficulty or "Medium",
            warning_triggered=False,
            was_auto_submitted=False,
        )
        db.add(metric)
    else:
        if not metric.question_start_time:
            metric.question_start_time = now_utc()
        metric.time_limit = metric.time_limit or get_time_limit(question)
        metric.difficulty = metric.difficulty or question.difficulty or "Medium"

    db.commit()
    db.refresh(metric)
    return metric


def metric_elapsed_seconds(metric: InterviewQuestionMetric, ended_at: datetime | None = None) -> int:
    start = as_utc(metric.question_start_time) or now_utc()
    end = as_utc(ended_at) or now_utc()
    return max(0, round((end - start).total_seconds()))


def metric_remaining_seconds(metric: InterviewQuestionMetric) -> int:
    limit = metric.time_limit or DIFFICULTY_TIME_LIMITS["medium"]
    return max(0, limit - metric_elapsed_seconds(metric))


def mark_metric_warning_if_needed(db: Session, metric: InterviewQuestionMetric) -> None:
    if metric.warning_triggered:
        return
    if metric_remaining_seconds(metric) <= WARNING_THRESHOLD_SECONDS:
        metric.warning_triggered = True
        db.commit()


def finalize_metric(
    db: Session,
    metric: InterviewQuestionMetric,
    question: Question,
    evaluation_time: int,
    was_auto_submitted: bool,
) -> None:
    ended_at = now_utc()
    time_limit = metric.time_limit or get_time_limit(question)
    metric.question_end_time = ended_at
    metric.time_taken = min(metric_elapsed_seconds(metric, ended_at), time_limit)
    metric.time_limit = time_limit
    metric.evaluation_time = evaluation_time
    metric.was_auto_submitted = was_auto_submitted
    metric.warning_triggered = metric.warning_triggered or metric.time_taken >= max(0, time_limit - WARNING_THRESHOLD_SECONDS)
    metric.difficulty = metric.difficulty or question.difficulty or "Medium"
    db.commit()


def timer_state_for_metric(metric: InterviewQuestionMetric) -> str:
    if metric.question_end_time:
        return "TIMEOUT" if metric.was_auto_submitted else "SUBMITTED"
    remaining = metric_remaining_seconds(metric)
    if remaining <= 0:
        return "TIMEOUT"
    if remaining <= WARNING_THRESHOLD_SECONDS:
        return "WARNING"
    return "RUNNING"


async def receive_interview_message(websocket: WebSocket, timeout_seconds: int | None) -> dict | None:
    if timeout_seconds is not None and timeout_seconds <= 0:
        return None
    try:
        if timeout_seconds is None:
            data = await websocket.receive_text()
        else:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=timeout_seconds)
        return json.loads(data)
    except asyncio.TimeoutError:
        return None


async def send_question(websocket: WebSocket, question: Question, metric: InterviewQuestionMetric, index: int) -> None:
    start_time = as_utc(metric.question_start_time) or now_utc()
    time_limit = metric.time_limit or get_time_limit(question)
    question_data = {
        "type": "question",
        "question_id": question.id,
        "index": index + 1,
        "total": TOTAL_QUESTIONS,
        "question_text": question.question_text,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "time_limit": time_limit,
        "remaining_time": metric_remaining_seconds(metric),
        "server_started_at": start_time.isoformat(),
        "server_deadline_at": (start_time + timedelta(seconds=time_limit)).isoformat(),
        "timer_state": timer_state_for_metric(metric),
    }

    audio_bytes = AIService.text_to_speech(question.question_text)
    if audio_bytes:
        question_data["audio_base64"] = base64.b64encode(audio_bytes).decode("utf-8")

    await websocket.send_json(question_data)


async def interview_websocket(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    await websocket.accept()

    try:
        payload = decode_access_token(token)
        email = payload.get("sub") if payload else None
        if not email:
            await websocket.send_json({"type": "error", "message": "Invalid token: missing email"})
            await websocket.close(code=4003)
            return
        user = db.query(User).filter(User.email == email).first()
        if not user:
            await websocket.send_json({"type": "error", "message": "User not found"})
            await websocket.close(code=4003)
            return
        user_id = user.id
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Token validation error: {str(e)}"})
        await websocket.close(code=4003)
        return

    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == user_id,
    ).first()

    if not session:
        await websocket.send_json({"type": "error", "message": f"Session {session_id} not found or access denied"})
        await websocket.close(code=4004)
        return

    if session.status == "completed":
        await websocket.send_json({"type": "error", "message": "Interview already completed"})
        await websocket.close(code=4005)
        return

    if session.status != "in-progress":
        session.status = "in-progress"
        db.commit()

    try:
        answered_count = db.query(Question).filter(
            Question.session_id == session_id,
            Question.answer_text.isnot(None),
        ).count()

        if answered_count > 0:
            await websocket.send_json({
                "type": "restored",
                "message": f"Restoring session from question {answered_count + 1}",
                "answered_count": answered_count,
            })

        for i in range(answered_count, TOTAL_QUESTIONS):
            question = db.query(Question).filter(
                Question.session_id == session_id,
            ).order_by(Question.id).offset(i).first()

            if not question:
                # 1. Get candidate's history of questions to find weak and strong topics
                historical_questions = db.query(Question).join(InterviewSession).filter(
                    InterviewSession.user_id == user_id,
                    Question.score.isnot(None),
                    Question.topic.isnot(None)
                ).all()
                
                topic_scores = {}
                for hq in historical_questions:
                    topic_scores.setdefault(hq.topic, []).append(hq.score)
                    
                weak_topics = []
                strong_topics = []
                for t, scores in topic_scores.items():
                    avg_s = sum(scores) / len(scores)
                    if avg_s <= 5.0:
                        weak_topics.append(t)
                    elif avg_s >= 8.0:
                        strong_topics.append(t)

                # 2. Get previous questions in the current session
                previous_questions_db = db.query(Question).filter(
                    Question.session_id == session_id,
                    Question.answer_text.isnot(None)
                ).order_by(Question.id).all()
                previous_questions = [
                    {
                        "question": pq.question_text,
                        "answer": pq.answer_text,
                        "score": pq.score,
                        "topic": pq.topic,
                        "difficulty": pq.difficulty
                    } for pq in previous_questions_db
                ]

                resume = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).first()

                existing_texts = {pq["question"] for pq in previous_questions}

                jd_text = ""
                if session.job_description_id:
                    jd = db.query(JobDescription).filter(JobDescription.id == session.job_description_id).first()
                    if jd:
                        jd_text = jd.raw_text or ""

                new_q_data = AIService.generate_next_question(
                    role=session.role,
                    interview_type=session.interview_type or "Technical",
                    difficulty=session.difficulty or "Medium",
                    resume_text=resume.extracted_text if resume else "",
                    previous_questions=previous_questions,
                    weak_topics=weak_topics,
                    strong_topics=strong_topics,
                    jd_text=jd_text
                )

                retry_count = 0
                while new_q_data["text"] in existing_texts and retry_count < 3:
                    new_q_data = AIService.generate_next_question(
                        role=session.role,
                        interview_type=session.interview_type or "Technical",
                        difficulty=session.difficulty or "Medium",
                        resume_text=resume.extracted_text if resume else "",
                        previous_questions=previous_questions,
                        weak_topics=weak_topics,
                        strong_topics=strong_topics,
                        jd_text=jd_text
                    )
                    retry_count += 1

                question = Question(
                    session_id=session_id,
                    question_text=new_q_data["text"],
                    topic=new_q_data.get("topic"),
                    difficulty=new_q_data.get("difficulty"),
                )
                db.add(question)
                db.commit()
                db.refresh(question)

            metric = get_or_create_metric(db, session_id, question)
            await send_question(websocket, question, metric, i)

            user_answer = None
            audio_base64 = None
            was_auto_submitted = False

            while question.answer_text is None and user_answer is None and audio_base64 is None:
                message = await receive_interview_message(websocket, metric_remaining_seconds(metric))

                if message is None:
                    user_answer = ""
                    was_auto_submitted = True
                    break

                if message.get("type") == "cheating_event":
                    db.add(CheatingLog(
                        session_id=session_id,
                        event_type=message.get("event"),
                        details=message.get("details"),
                    ))
                    db.commit()
                    continue

                if message.get("type") == "timer_warning":
                    metric.warning_triggered = True
                    db.commit()
                    continue

                if message.get("type") == "skip":
                    question.answer_text = "[Skipped]"
                    question.score = 0
                    question.score_accuracy = 0
                    question.score_communication = 0
                    question.score_confidence = 0
                    question.score_completeness = 0
                    question.feedback = "Question was skipped by the candidate."
                    question.improvement_tips = "Try to answer every question, even if briefly. Partial answers are better than skipping."
                    db.commit()
                    finalize_metric(db, metric, question, 0, False)
                    await websocket.send_json({
                        "type": "feedback",
                        "score": 0,
                        "feedback": "Question was skipped.",
                        "improvement_tips": "Try to answer every question, even briefly.",
                        "was_auto_submitted": False,
                        "timer_state": "SKIPPED",
                        "time_taken": metric_elapsed_seconds(metric),
                        "time_limit": metric.time_limit,
                        "evaluation_time": 0,
                    })
                    if i < TOTAL_QUESTIONS - 1:
                        while True:
                            msg = await receive_interview_message(websocket, None)
                            if msg and msg.get("type") == "next_question":
                                break
                    continue

                if message.get("type") == "repeat":
                    await send_question(websocket, question, metric, i)
                    continue

                if message.get("type") == "pause":
                    paused_at = now_utc()
                    metric.pause_duration = (metric.pause_duration or 0)
                    db.commit()
                    await websocket.send_json({"type": "paused", "message": "Interview paused. Send 'resume' to continue."})
                    while True:
                        msg = await receive_interview_message(websocket, None)
                        if msg and msg.get("type") == "resume":
                            resume_at = now_utc()
                            paused_seconds = (resume_at - paused_at).total_seconds()
                            metric.pause_duration = (metric.pause_duration or 0) + paused_seconds
                            db.commit()
                            await websocket.send_json({"type": "resumed", "message": "Interview resumed."})
                            await send_question(websocket, question, metric, i)
                            break
                    continue

                if message.get("type") != "answer":
                    continue

                user_answer = message.get("answer")
                audio_base64 = message.get("audio_base64")
                was_auto_submitted = bool(message.get("was_auto_submitted")) or metric_remaining_seconds(metric) <= 0

            if audio_base64:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    tmp.write(base64.b64decode(audio_base64))
                    tmp_path = tmp.name

                transcribed_text = AIService.speech_to_text(tmp_path)
                os.remove(tmp_path)

                if transcribed_text:
                    user_answer = transcribed_text
                    await websocket.send_json({
                        "type": "transcription",
                        "text": user_answer,
                    })

            if user_answer is None:
                await websocket.send_json({"type": "error", "message": "Answer or audio is required"})
                continue

            mark_metric_warning_if_needed(db, metric)
            eval_started = time.perf_counter()
            eval_result = AIService.evaluate_answer(question.question_text, user_answer)
            evaluation_time = round(time.perf_counter() - eval_started)

            question.answer_text = user_answer
            question.score = eval_result["score"]
            question.score_accuracy = eval_result["accuracy"]
            question.score_communication = eval_result["communication"]
            question.score_confidence = eval_result["confidence"]
            question.score_completeness = eval_result["completeness"]
            question.feedback = eval_result["feedback"]
            question.improvement_tips = eval_result["improvement_tips"]
            db.commit()

            finalize_metric(db, metric, question, evaluation_time, was_auto_submitted)

            feedback_audio = AIService.text_to_speech(f"You scored {question.score}. {question.feedback}")
            feedback_data = {
                "type": "feedback",
                "score": question.score,
                "feedback": question.feedback,
                "improvement_tips": question.improvement_tips,
                "was_auto_submitted": was_auto_submitted,
                "timer_state": "TIMEOUT" if was_auto_submitted else "SUBMITTED",
                "time_taken": metric.time_taken,
                "time_limit": metric.time_limit,
                "evaluation_time": evaluation_time,
            }
            if feedback_audio:
                feedback_data["audio_base64"] = base64.b64encode(feedback_audio).decode("utf-8")

            await websocket.send_json(feedback_data)

            if i < TOTAL_QUESTIONS - 1:
                while True:
                    msg = await receive_interview_message(websocket, None)
                    if msg and msg.get("type") == "next_question":
                        break

        session.status = "completed"
        final_questions = db.query(Question).filter(Question.session_id == session_id).all()
        scored_questions = [question.score for question in final_questions if question.score is not None]
        session.score = sum(scored_questions) / len(scored_questions) if scored_questions else 0
        
        # Calculate topic-wise scores for this session
        topic_maps = {
            "DSA": [],
            "DBMS": [],
            "OS": [],
            "CN": [],
            "OOP": [],
            "System Design": [],
            "Projects": [],
            "HR": []
        }
        comm_scores = []
        
        for q in final_questions:
            if q.score_communication is not None:
                comm_scores.append(q.score_communication)
            if q.topic and q.score is not None:
                topic_norm = q.topic.strip().upper()
                # Normalize mapping keys
                for key in topic_maps.keys():
                    key_norm = key.strip().upper()
                    # Handle some common mappings like Networking/CN, SQL/DBMS
                    if key_norm == topic_norm or (key_norm == "CN" and topic_norm == "COMPUTER NETWORKS") or (key_norm == "DBMS" and topic_norm == "SQL"):
                        topic_maps[key].append(q.score)
                        break
        
        session.score_dsa = sum(topic_maps["DSA"]) / len(topic_maps["DSA"]) if topic_maps["DSA"] else None
        session.score_dbms = sum(topic_maps["DBMS"]) / len(topic_maps["DBMS"]) if topic_maps["DBMS"] else None
        session.score_os = sum(topic_maps["OS"]) / len(topic_maps["OS"]) if topic_maps["OS"] else None
        session.score_cn = sum(topic_maps["CN"]) / len(topic_maps["CN"]) if topic_maps["CN"] else None
        session.score_oop = sum(topic_maps["OOP"]) / len(topic_maps["OOP"]) if topic_maps["OOP"] else None
        session.score_system_design = sum(topic_maps["System Design"]) / len(topic_maps["System Design"]) if topic_maps["System Design"] else None
        session.score_project = sum(topic_maps["Projects"]) / len(topic_maps["Projects"]) if topic_maps["Projects"] else None
        session.score_hr = sum(topic_maps["HR"]) / len(topic_maps["HR"]) if topic_maps["HR"] else None
        session.score_communication = sum(comm_scores) / len(comm_scores) if comm_scores else None

        session.ended_at = now_utc()
        db.commit()

        # Trigger automation: update skill gap and career readiness
        try:
            from app.services.automation_service import AutomationService
            automation = AutomationService(db)
            automation.on_interview_complete(session.user_id, session.id)
        except Exception as auto_err:
            print(f"Automation trigger (interview) failed: {auto_err}")

        await websocket.send_json({
            "type": "completed",
            "final_score": session.score,
            "message": "Interview completed successfully!",
        })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as exc:
        print(f"WebSocket error: {exc}")
        await websocket.send_json({"type": "error", "message": str(exc)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


router.add_api_websocket_route("/ws/interview/{session_id}", interview_websocket)
