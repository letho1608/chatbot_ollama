# Tysor - Cyber Security AI Chatbot

A production-grade Cyber Security AI chatbot powered by **Ollama** with a full web UI, authentication, RBAC, session-only RAG, and an intelligent agent framework with safety, memory, and content filtering.

---

## Features

- **Chat Interface** — OpenAI-style clean UI, dark/light mode, streaming responses
- **Authentication** — JWT-based login/register with bcrypt password hashing
- **RBAC** — User / Admin roles; admin panel at `/admin`
- **Model Management** — Curated catalog of 50+ models across 7 categories, pull-on-click
- **RAG (Session-only)** — Drag-drop file upload (.txt, .md, .csv, .docx, .pdf, etc.), security keyword validation, in-memory embeddings with cosine similarity
- **Agent Framework** — Input/output safety validation, PII sanitization, prompt injection detection, memory extraction, loop detection, adaptive scaling
- **Admin Dashboard** — Full admin panel with stats, activity feed, user management, audit logs, system monitoring
- **Topic Filtering** — Blocks non-cyber-security queries; extended jailbreak/injection protection
- **Vietnamese Language** — Default system prompt forces Vietnamese responses

---


👉 **[diagrams.html](diagrams.html)** — System Architecture, Authentication Flow, Chat Flow, RAG Document Flow, Safety & Content Filtering Flow, Admin Panel Flow, Agent Framework Architecture, and Database Schema.

## Project Structure

```
D:\Code\ai\chabot_ollama\
│
├── main.py               # Main FastAPI application (all routes)
├── auth.py               # JWT creation/verification, bcrypt
├── database.py           # SQLAlchemy models & session
├── requirements.txt      # Python dependencies
├── README.md             # This file
│
├── core/                 # Agent framework
│   ├── __init__.py
│   ├── agent.py          # AgentOrchestrator (process_input, build, process_response)
│   ├── config.py         # AgentConfig, MODEL_CATALOG, BLOCKED/INJECTION patterns, SECURITY_KEYWORDS
│   ├── memory.py         # Memory CRUD, extraction, conflict resolution
│   ├── monitor.py        # AuditLogger (event/chat logging)
│   ├── rag.py            # Document chunking, embeddings, session store, file extraction
│   ├── safety.py         # Input/output validation, PII, injection detection, topic check
│   └── validator.py      # Response validation, loop detection, hallucination checking
│
├── static/               # Frontend assets
│   ├── style.css         # Global styles (dark/light theme, admin layout, chat)
│   ├── app.js            # Chat UI logic (model dropdown, RAG, settings, auth)
│   └── admin.js          # Admin panel logic (7 tabs, user modal, charts, model pull)
│
├── data/                 # SQLite database storage
│   └── chatbot.db
│
└── templates/            # Jinja2 templates
    ├── index.html        # Chat page (main app)
    ├── dashboard.html    # Landing page
    ├── login.html        # Login page
    ├── register.html     # Register page
    └── admin.html        # Admin panel page
```

---
## Lab Submission Templates

- `report/SCORING.md` — Lab 3 scoring rubric and feature checklist.
- `report/group_report/TEMPLATE_GROUP_REPORT.md` — Group report template.
- `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md` — Individual report template.
- `EVALUATION.md` — Lab 3 evaluation metrics and log interpretation.
- `scripts/parse_evaluation_metrics.py` — Script to aggregate prompt/chat metrics from logs.

---
## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running (`ollama serve`)

### Steps

```bash
# 1. Clone the repository
cd D:\Code\ai\chabot_ollama

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify Ollama is running
curl http://127.0.0.1:11434/api/tags

# 4. Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 5. Open browser
start http://127.0.0.1:8000
```

### Test Accounts

- **User:** `testuser` / `test123`
- **Admin:** `admin` / `admin123` (auto-created on first startup)
- Register new accounts at `/register`.

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | — | Register new user |
| POST | `/api/auth/login` | — | Login, get JWT token |
| GET | `/api/auth/me` | User | Current user info |
| POST | `/api/auth/logout` | User | Logout |
| POST | `/api/chat/stream` | User | Stream chat response |
| GET | `/api/conversations` | User | List user's conversations |
| GET | `/api/conversations/{id}` | User | Get conversation messages |
| DELETE | `/api/conversations/{id}` | User | Delete conversation |
| PUT | `/api/conversations/{id}` | User | Update conversation title |
| GET | `/api/models/catalog` | User | Full model catalog + installed status |
| POST | `/api/models/pull` | User | Pull a model from Ollama |
| DELETE | `/api/admin/models/{name}` | Admin | Delete an installed model |
| POST | `/api/rag/upload-file` | User | Upload document for RAG |
| GET | `/api/rag/documents` | User | List uploaded documents |
| DELETE | `/api/rag/documents/{id}` | User | Delete document |
| GET | `/api/rag/search` | User | Semantic search in documents |
| GET | `/api/memory` | User | Get user memories |
| POST | `/api/memory` | User | Set memory |
| DELETE | `/api/memory/{key}` | User | Delete memory |
| GET | `/api/admin/stats` | Admin | Dashboard statistics |
| GET | `/api/admin/users` | Admin | List all users |
| GET | `/api/admin/users/{id}` | Admin | User detail + activity |
| PUT | `/api/admin/users/{id}/toggle` | Admin | Enable/disable user |
| DELETE | `/api/admin/users/{id}` | Admin | Delete user |
| GET | `/api/admin/conversations` | Admin | All conversations |
| GET | `/api/admin/activity` | Admin | Combined activity feed |
| GET | `/api/admin/audit` | Admin | Audit log entries |
| GET | `/api/admin/system` | Admin | System health info |

---

## Security Features

- **Input Validation:** Blocks violence, self-harm, harassment, hate speech, explicit content, drugs, weapons, illegal access, phishing
- **Prompt Injection:** 20+ patterns detecting jailbreak attempts, DAN, roleplay bypass, encoded queries
- **Topic Filtering:** 200+ cyber security keywords — non-security queries are blocked with Vietnamese message
- **PII Sanitization:** Email, phone number, Vietnamese ID (CCCD) automatically removed before query reaches Ollama
- **Output Validation:** Empty response detection, loop detection, contradiction checking, confidence scoring
- **JWT Authentication:** Tokens with `sub` (string), role-based access (user/admin)
- **Audit Logging:** All login attempts, admin actions, chat events, safety blocks logged with IP
- **Rate Limiting:** N/A (local deployment only)


