"""
test_app.py — Stage 1 test suite.

╔══════════════════════════════════════════════════════════════════════╗
║  YOUR TASK: the test structure is given. Some tests are complete,    ║
║  others have a TODO for you to finish.                               ║
╚══════════════════════════════════════════════════════════════════════╝

HOW TO RUN:
  pytest tests/ -v

HOW TESTS WORK HERE:
  We use FastAPI's TestClient — it sends real HTTP requests to your app
  without needing to start a server. Each test gets a fresh, empty
  database so tests never interfere with each other.

  The test database is a separate file (test_messenger.db) and is
  wiped clean before every single test.
"""

from collections import defaultdict
import json
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.models import Base, get_db
from server.crypto import encrypt, decrypt
from server.dependencies import get_broadcaster


# ---------------------------------------------------------------------------
# Test database setup — uses a separate file, wiped before each test
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_messenger.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login(client, username="alice", password="secret123") -> str:
    """Register a user and return their JWT token."""
    client.post("/register", json={"username": username, "password": password})
    response = client.post("/login", json={"username": username, "password": password})
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def parse_first_sse_payload(stream_response) -> dict:
    for line in stream_response.iter_lines():
        if line and line.startswith("data: "):
            return json.loads(line[6:])
    raise AssertionError("SSE stream ended before any event was received")


class FakeBroadcaster:
    def __init__(self):
        self._events_by_user: dict[str, list[str]] = defaultdict(list)
        self.published: list[tuple[str, dict]] = []
        self._lock = threading.Lock()

    async def publish(self, username: str, data: str) -> None:
        parsed = json.loads(data)
        with self._lock:
            self._events_by_user[username].append(data)
            self.published.append((username, parsed))

    async def listen(self, username: str):
        with self._lock:
            events = list(self._events_by_user[username])
        for payload in events:
            yield payload


@pytest.fixture
def fake_broadcaster():
    fake = FakeBroadcaster()
    app.dependency_overrides[get_broadcaster] = lambda: fake
    try:
        yield fake
    finally:
        app.dependency_overrides.pop(get_broadcaster, None)


# ===========================================================================
# 1. Authentication tests
# ===========================================================================

class TestAuthentication:

    def test_register_success(self, client):
        response = client.post("/register", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 201

    def test_register_duplicate_username(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/register", json={"username": "alice", "password": "other-password"})
        assert response.status_code == 400

    def test_register_password_too_short(self, client):
        response = client.post("/register", json={"username": "alice", "password": "abc"})
        assert response.status_code == 422   # Pydantic rejects it before your code runs

    def test_login_success(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "secret123"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/register", json={"username": "alice", "password": "secret123"})
        response = client.post("/login", json={"username": "alice", "password": "wrongpassword"})
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post("/login", json={"username": "ghost", "password": "secret123"})
        assert response.status_code == 401

    def test_messages_require_token(self, client):
        response = client.get("/messages")
        assert response.status_code in (401, 403)

    def test_messages_reject_bad_token(self, client):
        response = client.get("/messages", headers={"Authorization": "Bearer fake-token"})
        assert response.status_code == 401

    def test_messages_accept_valid_token(self, client):
        token = register_and_login(client)
        response = client.get("/messages", headers=auth(token))
        assert response.status_code == 200


# ===========================================================================
# 2. Encryption tests
# ===========================================================================

class TestEncryption:

    def test_encrypt_is_not_plain_text(self):
        assert encrypt("hello world") != "hello world"

    def test_decrypt_round_trip(self):
        original = "this is a secret message"
        assert decrypt(encrypt(original)) == original

    def test_same_message_encrypts_differently_each_time(self):
        # fresh nonce every call → different ciphertext
        assert encrypt("hello") != encrypt("hello")

    def test_tampered_ciphertext_raises(self):
        blob = encrypt("original")
        tampered = blob[:-4] + "XXXX"
        with pytest.raises(Exception):
            decrypt(tampered)

    # TODO — complete this test:
    # After sending a message via POST /messages, query the database directly
    # and verify that the stored ciphertext is NOT the plain text,
    # but that decrypt(ciphertext) DOES return the original plain text.
    def test_messages_are_stored_encrypted(self, client):
        from server.models import Message
        token = register_and_login(client)
        client.post("/messages", json={"content": "secret text", "recipients": ["bob"]}, headers=auth(token))
        db = TestingSession()
        row = db.query(Message).first()
        db.close()
        assert row.ciphertext != "secret text"
        assert decrypt(row.ciphertext) == "secret text"


# ===========================================================================
# 3. Messaging tests
# ===========================================================================

class TestMessaging:

    def test_send_message_success(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        response = client.post(
            "/messages",
            json={"content": "hello bob", "recipients": ["bob"]},
            headers=auth(alice_token),
        )
        assert response.status_code == 201
        data = response.json()[0]
        assert data["content"] == "hello bob"   # returned decrypted
        assert data["sender"] == "alice"
        assert data["recipient"] == "bob"

    def test_get_messages_returns_decrypted(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")

        client.post("/messages", json={"content": "hi bob", "recipients": ["bob"]}, headers=auth(alice_token))

        response = client.get("/messages", headers=auth(alice_token))
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        assert messages[0]["content"] == "hi bob"   # must be decrypted, not ciphertext

    # TODO — complete this test:
    # Alice sends a message to Bob. Bob sends a message to Alice.
    # Verify that GET /messages returns ONLY the messages
    # where the requesting user is sender OR recipient.
    def test_user_sees_only_their_messages(self, client):
        alice_token = register_and_login(client, "alice", "secret123")
        bob_token   = register_and_login(client, "bob",   "secret456")
        charlie_token = register_and_login(client, "charlie", "secret789")

        client.post("/messages", json={"content": "hi bob",         "recipients": ["bob"]}, headers=auth(alice_token))
        client.post("/messages", json={"content": "charlie to bob", "recipients": ["bob"]}, headers=auth(charlie_token))

        alice_msgs = client.get("/messages", headers=auth(alice_token)).json()
        assert len(alice_msgs) == 1
        assert alice_msgs[0]["content"] == "hi bob"


# ===========================================================================
# 4. SSE tests
# ===========================================================================

class TestSSE:

    def test_sse_stream_receives_broadcast(self, client, fake_broadcaster):
        alice_token = register_and_login(client, "alice", "secret123")
        bob_token = register_and_login(client, "bob", "secret456")

        send_response = client.post(
            "/messages",
            json={"content": "hello everyone", "recipients": ["*"]},
            headers=auth(bob_token),
        )
        assert send_response.status_code == 201

        with client.stream("GET", "/stream", headers=auth(alice_token)) as stream_response:
            event = parse_first_sse_payload(stream_response)

        assert event["sender"] == "bob"
        assert event["content"] == "hello everyone"

    def test_only_sender_sees_targeted_messages(self, client, fake_broadcaster):
        alice_token = register_and_login(client, "alice", "secret123")
        register_and_login(client, "bob", "secret456")
        register_and_login(client, "charlie", "secret789")

        send_response = client.post(
            "/messages",
            json={"content": "private to bob", "recipients": ["bob"]},
            headers=auth(alice_token),
        )
        assert send_response.status_code == 201

        recipients = [username for username, _ in fake_broadcaster.published]
        assert recipients == ["bob"]
        assert "charlie" not in recipients

    def test_concurrent_clients(self, client, fake_broadcaster):
        alice_token = register_and_login(client, "alice", "secret123")
        bob_token = register_and_login(client, "bob", "secret456")

        barrier = threading.Barrier(2)
        responses: list[int] = []
        responses_lock = threading.Lock()

        def _send(token: str, content: str):
            with TestClient(app) as sender_client:
                barrier.wait(timeout=2)
                response = sender_client.post(
                    "/messages",
                    json={"content": content, "recipients": ["alice", "bob"]},
                    headers=auth(token),
                )
                with responses_lock:
                    responses.append(response.status_code)

        sender_1 = threading.Thread(target=_send, args=(alice_token, "from alice"), daemon=True)
        sender_2 = threading.Thread(target=_send, args=(bob_token, "from bob"), daemon=True)
        sender_1.start()
        sender_2.start()
        sender_1.join(timeout=2)
        sender_2.join(timeout=2)

        assert responses == [201, 201]

        alice_events = [payload["content"] for user, payload in fake_broadcaster.published if user == "alice"]
        bob_events = [payload["content"] for user, payload in fake_broadcaster.published if user == "bob"]
        assert set(alice_events) == {"from alice", "from bob"}
        assert set(bob_events) == {"from alice", "from bob"}
