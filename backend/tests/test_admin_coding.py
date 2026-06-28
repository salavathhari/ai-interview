import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.coding_challenge import CodingChallenge, CodingSubmission, CodingSession

# Test Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_coding.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def setup_data(db_session):
    # Create an admin user
    admin = User(
        email="admin@test.com",
        name="Admin User",
        hashed_password="hashed_password",
        is_admin=True,
        is_active=True
    )
    # Create a candidate user
    candidate = User(
        email="candidate@test.com",
        name="Candidate User",
        hashed_password="hashed_password",
        is_admin=False,
        is_active=True
    )
    db_session.add_all([admin, candidate])
    db_session.commit()

    # Create a coding challenge
    challenge = CodingChallenge(
        title="Sum Array",
        description="Return sum of array.",
        difficulty="Easy",
        supported_languages=["python"],
        test_cases=[{"input": "1 2 3", "expected": "6"}],
        hidden_test_cases=[{"input": "10 20", "expected": "30"}, {"input": "0", "expected": "0"}]
    )
    db_session.add(challenge)
    db_session.commit()

    # Create a coding session
    coding_session = CodingSession(
        user_id=candidate.id,
        challenge_id=challenge.id,
        language_used="python",
        status="submitted",
        coding_score=8.5
    )
    db_session.add(coding_session)
    db_session.commit()

    # Create a coding submission
    submission = CodingSubmission(
        user_id=candidate.id,
        challenge_id=challenge.id,
        coding_session_id=coding_session.id,
        code="def sum(arr):\n    return sum(arr)",
        language="python",
        status="Accepted",
        runtime_ms=15,
        memory_kb=2048,
        correctness_score=100.0,
        ai_score=9.0,
        ai_feedback="Great variable names.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        is_final=True,
        test_results=[
            {"test_number": 1, "passed": True},  # public
            {"test_number": 2, "passed": True},  # hidden 1
            {"test_number": 3, "passed": True}   # hidden 2
        ]
    )
    db_session.add(submission)
    db_session.commit()

    return {
        "admin": admin,
        "candidate": candidate,
        "challenge": challenge,
        "submission": submission,
        "session": coding_session
    }

TEST_PASSWORD = "Password123"

def get_token(client, email):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": TEST_PASSWORD}
    )
    return response.json().get("access_token")

def test_admin_endpoints_permissions(client, setup_data):
    # We will register candidate and admin via signup to get correct tokens
    client.post("/auth/signup", json={"email": "candidate_api@test.com", "password": TEST_PASSWORD, "name": "Candidate"})
    client.post("/auth/signup", json={"email": "admin_api@test.com", "password": TEST_PASSWORD, "name": "Admin"})
    
    # Manually promote admin_api to admin
    db = TestingSessionLocal()
    admin_user = db.query(User).filter(User.email == "admin_api@test.com").first()
    admin_user.is_admin = True
    db.commit()
    db.close()

    # Login candidate
    cand_token = get_token(client, "candidate_api@test.com")
    # Login admin
    adm_token = get_token(client, "admin_api@test.com")

    # Access submissions list as candidate -> should fail (403)
    res = client.get("/admin/coding/submissions", headers={"Authorization": f"Bearer {cand_token}"})
    assert res.status_code == 403

    # Access submissions list as admin -> should succeed (200)
    res = client.get("/admin/coding/submissions", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200

def test_admin_list_submissions_filtering(client, setup_data):
    adm_token = get_token(client, "admin_api@test.com")

    # Seed an actual coding submission for candidate_api
    db = TestingSessionLocal()
    cand_user = db.query(User).filter(User.email == "candidate_api@test.com").first()
    challenge = db.query(CodingChallenge).first()
    
    sub = CodingSubmission(
        user_id=cand_user.id,
        challenge_id=challenge.id,
        code="print(1)",
        language="python",
        status="Accepted",
        runtime_ms=12,
        memory_kb=1024,
        is_final=True
    )
    db.add(sub)
    db.commit()
    db.close()

    # List submissions
    res = client.get("/admin/coding/submissions", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "submissions" in data
    assert len(data["submissions"]) >= 1
    assert data["submissions"][0]["candidate_email"] == "candidate_api@test.com"

    # Search filter by candidate email
    res = client.get("/admin/coding/submissions?search=candidate_api", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    assert len(res.json()["submissions"]) >= 1

    # Search filter by challenge title
    res = client.get("/admin/coding/submissions?search=Sum+Array", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    assert len(res.json()["submissions"]) >= 1

    # Language filter
    res = client.get("/admin/coding/submissions?language=python", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    assert len(res.json()["submissions"]) >= 1

    # Status filter
    res = client.get("/admin/coding/submissions?status=Accepted", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    assert len(res.json()["submissions"]) >= 1

def test_admin_get_submission_detail(client, setup_data):
    adm_token = get_token(client, "admin_api@test.com")

    db = TestingSessionLocal()
    sub = db.query(CodingSubmission).filter(CodingSubmission.status == "Accepted").first()
    sub_id = sub.id
    db.close()

    # Get details
    res = client.get(f"/admin/coding/submissions/{sub_id}", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == sub_id
    assert "candidate_email" in data
    assert "challenge_title" in data
    assert data["code"] is not None
    assert "hidden_passed" in data
    assert "hidden_total" in data

def test_admin_get_coding_analytics(client, setup_data):
    adm_token = get_token(client, "admin_api@test.com")

    # Get analytics
    res = client.get("/admin/coding/analytics", headers={"Authorization": f"Bearer {adm_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_submissions" in data
    assert "total_sessions" in data
    assert "avg_correctness_score" in data
    assert "avg_ai_score" in data
    assert "language_distribution" in data
    assert "status_distribution" in data
    assert "difficulty_breakdown" in data
