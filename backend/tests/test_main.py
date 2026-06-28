import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Mock DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={"email": "test@pytest.com", "password": "Password123", "name": "Tester"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@pytest.com"
    assert "access_token" in data

def test_login(client):
    # Ensure user exists (from previous test or create new)
    client.post(
        "/auth/signup",
        json={"email": "login@pytest.com", "password": "Password123", "name": "Tester"}
    )
    response = client.post(
        "/auth/login",
        json={"email": "login@pytest.com", "password": "Password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_admin_access_denied(client):
    # Standard user login
    r = client.post("/auth/login", json={"email": "test@pytest.com", "password": "Password123"})
    token = r.json()["access_token"]
    
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403 # Unauthorized for non-admin
