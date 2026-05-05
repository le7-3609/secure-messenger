# 🔐 Secure Messenger — Stage 1

A secured REST API for private messaging. Users can register, login, send encrypted messages, and read them back.
All messages are stored **AES-256-GCM encrypted** in the database. Passwords are **bcrypt hashed** and never stored in plain text.

---

## ✨ Features

- **User registration & login** with bcrypt password hashing
- **JWT authentication** — stateless, signed tokens with expiry
- **End-to-end message encryption** using AES-256-GCM
- **Per-user message isolation** — users see only messages they sent or received
- **Tamper detection** — GCM authentication tag rejects any modified ciphertext
- **Layered architecture** — full dependency injection with FastAPI's `Depends`
- **Type-safe** — complete type hints on all functions and methods
- **Custom exception hierarchy** — domain exceptions with context
- **Modern Python** — `pyproject.toml` with build system configuration

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database | SQLite via [SQLAlchemy](https://www.sqlalchemy.org/) ORM |
| Password hashing | [bcrypt](https://pypi.org/project/bcrypt/) |
| JWT tokens | [python-jose](https://pypi.org/project/python-jose/) |
| Encryption | [cryptography](https://pypi.org/project/cryptography/) — AES-256-GCM |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| Testing | [pytest](https://pytest.org/) + FastAPI TestClient |

---

## 🏗️ Architecture

The project follows a layered architecture with full dependency injection via FastAPI's `Depends`:

```
routes.py         → HTTP only (status codes, request/response)
    └── services/ → Business logic (auth, user, message)
          └── repositories/ → Database access only
                └── models/ → SQLAlchemy ORM tables
```

```
server/
├── models/
│   ├── base.py                 # SQLAlchemy engine, session, Base
│   ├── user.py                 # User model
│   └── message.py              # Message model
├── repositories/
│   ├── UserRepository.py       # DB access for users
│   └── messageRepository.py    # DB access for messages
├── services/
│   ├── authService.py          # JWT + bcrypt logic
│   ├── userService.py          # Register & login logic
│   └── messageService.py       # Send & fetch message logic
├── dependencies.py             # DI container (wires all layers)
├── routes.py                   # API route handlers
├── schemas.py                  # Pydantic request/response schemas
├── exceptions.py               # Custom exception hierarchy
├── crypto.py                   # AES-256-GCM encrypt/decrypt
└── main.py                     # App entry point
```

---

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.11+

### 📦 Installation

```bash
git clone https://github.com/le7-3609/secure-messenger.git
cd secure-messenger
pip install -r requirements.txt
```

### ▶️ Run the server

```bash
uvicorn server.main:app --reload
```

Open the interactive API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/register` | ❌ | Register a new user |
| `POST` | `/login` | ❌ | Login and receive a JWT token |
| `POST` | `/messages` | ✅ | Send an encrypted message |
| `GET` | `/messages` | ✅ | Fetch your messages (decrypted) |

### 💡 Example flow

```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

# Send a message (use token from login response)
curl -X POST http://localhost:8000/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "hello bob", "recipient": "bob"}'

# Read messages
curl http://localhost:8000/messages \
  -H "Authorization: Bearer <token>"
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output: **17 passed**

The test suite covers:
- Registration (success, duplicate username, short password)
- Login (success, wrong password, unknown user)
- Authentication (no token → 403, fake token → 401, valid token → 200)
- Encryption (round-trip, uniqueness, tamper detection, DB storage verification)
- Messaging (send, fetch decrypted, per-user isolation)

---

## 🔒 Security Notes

| Concern | How it's handled |
|---|---|
| Passwords | bcrypt hashed with salt — never stored in plain text |
| Messages | AES-256-GCM encrypted — ciphertext only in DB |
| Tokens | JWT signed with HS256, expire after 24 hours |
| Tamper detection | GCM auth tag raises exception on any modification |
| DB theft | Attacker sees only hashes and ciphertext |

> ⚠️ The AES key is generated in memory at startup (`os.urandom(32)`). Restarting the server makes existing messages unreadable. For production, load the key from an environment variable or a secrets manager (e.g. AWS Secrets Manager).

> ⚠️ `SECRET_KEY` in `auth.py` should be replaced with a long random string loaded from an environment variable in production.

---

## 🗺️ Roadmap

- **Stage 2** — Real-time messaging via Server-Sent Events (SSE) + CLI client

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).