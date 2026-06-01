import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./data/test.db"

from core.database import Base, get_db, User, Conversation, Message
from core.auth import hash_password, create_access_token

TEST_DB_URL = "sqlite:///./data/test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("data/test.db"):
        try:
            os.remove("data/test.db")
        except PermissionError:
            pass


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def app():
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="function")
def admin_user(db):
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin", email="admin@test.local",
            password_hash=hash_password("admin123"), role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="function")
def normal_user(db):
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        user = User(
            username="testuser", email="test@test.local",
            password_hash=hash_password("test123"), role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(admin_user):
    return create_access_token({
        "sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role
    })


@pytest.fixture(scope="function")
def user_token(normal_user):
    return create_access_token({
        "sub": str(normal_user.id), "username": normal_user.username, "role": normal_user.role
    })


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def conversation(db, normal_user):
    conv = Conversation(id="test-conv-1", user_id=normal_user.id, title="Test conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
