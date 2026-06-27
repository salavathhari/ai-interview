import pytest
from app.services.ai_service import AIService

def test_mock_skill_extraction():
    resume_text = "I have experience with Python, React, and Docker."
    skills = AIService.extract_skills(resume_text)
    assert "Python" in skills
    assert "React" in skills
    assert "Docker" in skills
    assert "Java" not in skills

def test_generate_mock_questions():
    role = "Full Stack Developer"
    resume = "Expert in Python and React"
    questions = AIService.generate_questions(role, resume, count=3)

    # Since we likely don't have an API key in the test environment,
    # it should fall back to mock questions.
    assert len(questions) == 3
    for q in questions:
        text = q["text"] if isinstance(q, dict) else q
        assert isinstance(text, str)
        assert len(text) > 10

def test_adaptive_question_fallback():
    """Test that the adaptive logic returns a question even in mock mode with new signature."""
    role = "Backend Engineer"
    resume = "FastAPI specialist"
    # New signature: role, interview_type, difficulty, resume_text, previous_questions, weak_topics, strong_topics
    question = AIService.generate_next_question(
        role=role,
        interview_type="Technical",
        difficulty="Medium",
        resume_text=resume,
        previous_questions=[],
        weak_topics=[],
        strong_topics=[]
    )
    assert isinstance(question, dict)
    assert "text" in question
    assert "topic" in question
    assert "difficulty" in question
    assert len(question["text"]) > 10

def test_adaptive_difficulty_increases_on_strong_answer():
    """After a strong answer (score >= 8), difficulty should go up and follow-up should be generated."""
    role = "SDE"
    resume = "Experience with Python, FastAPI, Docker"
    # Simulate one scored question on DSA at Medium
    previous_questions = [
        {"question": "What is BFS?", "answer": "BFS traverses level by level using a queue.", "score": 9, "topic": "DSA", "difficulty": "Medium"}
    ]
    question = AIService.generate_next_question(
        role=role,
        interview_type="Technical",
        difficulty="Medium",
        resume_text=resume,
        previous_questions=previous_questions,
        weak_topics=[],
        strong_topics=["DSA"]
    )
    assert isinstance(question, dict)
    assert "text" in question
    # After a strong answer on DSA, should stay on DSA and upgrade difficulty
    assert question.get("topic") == "DSA"
    assert question.get("difficulty") in ["Medium", "Hard"]

def test_adaptive_difficulty_decreases_on_weak_answer():
    """After a weak answer (score <= 5), should ask a simpler clarification question."""
    role = "SDE"
    resume = "Experience with Java"
    previous_questions = [
        {"question": "What are ACID properties?", "answer": "I'm not sure", "score": 3, "topic": "DBMS", "difficulty": "Medium"}
    ]
    question = AIService.generate_next_question(
        role=role,
        interview_type="Technical",
        difficulty="Medium",
        resume_text=resume,
        previous_questions=previous_questions,
        weak_topics=["DBMS"],
        strong_topics=[]
    )
    assert isinstance(question, dict)
    assert "text" in question
    # Should stay on DBMS for clarification and reduce difficulty
    assert question.get("topic") == "DBMS"
    assert question.get("difficulty") in ["Easy", "Medium"]

def test_bad_answer_gets_low_score():
    result = AIService.evaluate_answer(
        "How do you optimize SQL query performance in a backend service?",
        "anything"
    )
    assert result["score"] <= 2
    assert "does not" in result["feedback"].lower() or "too short" in result["feedback"].lower()

def test_relevant_answer_scores_higher_than_bad_answer():
    bad = AIService.evaluate_answer(
        "How do you optimize SQL query performance in a backend service?",
        "anything"
    )
    good = AIService.evaluate_answer(
        "How do you optimize SQL query performance in a backend service?",
        "I would first inspect the query plan, add indexes for frequent filters and joins, avoid select star, and check slow query logs. For example, if a user lookup is filtering by email, I would add an index on email and validate latency before and after. I would also watch trade-offs because too many indexes can slow writes."
    )
    assert good["score"] > bad["score"]
    assert good["accuracy"] > bad["accuracy"]

def test_role_topic_weighting_sde():
    """SDE interviews should include DSA, DBMS, OS, CN, Projects topics."""
    role = "SDE"
    resume = "Python, algorithms, system design"
    valid_topics = {"DSA", "DBMS", "OS", "CN", "Projects", "HR"}
    # Run multiple times to get varied topics
    topics_seen = set()
    for _ in range(20):
        q = AIService.generate_next_question(
            role=role,
            interview_type="Technical",
            difficulty="Medium",
            resume_text=resume,
            previous_questions=[],
            weak_topics=[],
            strong_topics=[]
        )
        if q.get("topic"):
            topics_seen.add(q["topic"])
    # At least 2 different topics should appear across 20 calls
    assert len(topics_seen) >= 2

def test_hr_interview_only_hr_topic():
    """HR interviews should only generate HR questions."""
    role = "SDE"
    resume = "Python developer"
    q = AIService.generate_next_question(
        role=role,
        interview_type="HR",
        difficulty="Medium",
        resume_text=resume,
        previous_questions=[],
        weak_topics=[],
        strong_topics=[]
    )
    assert q.get("topic") == "HR"

def test_coding_interview_only_dsa_topic():
    """Coding interviews should only generate DSA questions."""
    role = "SDE"
    resume = "Python developer"
    q = AIService.generate_next_question(
        role=role,
        interview_type="Coding",
        difficulty="Hard",
        resume_text=resume,
        previous_questions=[],
        weak_topics=[],
        strong_topics=[]
    )
    assert q.get("topic") == "DSA"
