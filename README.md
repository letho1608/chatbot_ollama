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

---

## Authentication Flow

```
User                    Browser                   FastAPI                Database
  │                        │                        │                      │
  │  POST /api/auth/login  │                        │                      │
  │───────────────────────►│  POST /api/auth/login   │                      │
  │                        │───────────────────────►│                      │
  │                        │                        │  SELECT * FROM users │
  │                        │                        ├─────────────────────►│
  │                        │                        │◄─────────────────────┤
  │                        │                        │                      │
  │                        │                        │  bcrypt.verify()     │
  │                        │                        │  Create JWT token    │
  │                        │                        │  AuditLog: "login"   │
  │                        │◄──── {token, role} ────┤  db.flush()          │
  │◄─── {token, role} ─────┤                        │                      │
  │                        │                        │                      │
  │  Store token in        │                        │                      │
  │  localStorage          │                        │                      │
  │                        │                        │                      │
  │  GET /api/auth/me      │                        │                      │
  │───────────────────────►│───────────────────────►│                      │
  │                        │                        │  Decode JWT          │
  │                        │                        │  Verify "sub" claim  │
  │                        │◄──── {user, role} ─────┤                      │
  │◄──── {user, role} ─────┤                        │                      │
  │                        │                        │                      │
  │  role=admin ──► /admin │                        │                      │
  │  role=user  ──► /chat  │                        │                      │
```

---

## Chat Flow

```
User                Browser/Frontend              FastAPI+Agent              Ollama
 │                      │                            │                        │
 │  Type message        │                            │                        │
 │─────────────────────►│  POST /api/chat/stream      │                        │
 │                      │───────────────────────────►│                        │
 │                      │                            │  AgentOrchestrator     │
 │                      │                            │  .process_input():     │
 │                      │                            │    ├─ Safety Check     │
 │                      │                            │    ├─ PII Sanitize     │
 │                      │                            │    ├─ Security Topic   │
 │                      │                            │    └─ Injection Det.  │
 │                      │                            │                        │
 │                      │                            │  Save Message (user)  │
 │                      │                            │  Auto-name title      │
 │                      │                            │                        │
 │                      │                            │  Agent.build_messages():│
 │                      │                            │    ├─ System Prompt    │
 │                      │                            │    ├─ Memories        │
 │                      │                            │    ├─ RAG Context     │
 │                      │                            │    └─ History msgs    │
 │                      │                            │                        │
 │                      │                            │  POST /api/chat       │
 │                      │                            │──────────────────────►│
 │                      │  SSE: data: {content}      │◄───── stream ────────┤
 │◄─────────────────────┤◄───────────────────────────┤                        │
 │                      │                            │                        │
 │                      │                            │  on done:              │
 │                      │                            │  Agent.process_resp(): │
 │                      │                            │    ├─ Output Validate  │
 │                      │                            │    ├─ Safety Check     │
 │                      │                            │    ├─ Memory Extract   │
 │                      │                            │    └─ Audit Log       │
 │                      │                            │                        │
 │                      │  Render Markdown            │                        │
 │◄─────────────────────┤                            │                        │
```

---

## RAG Document Flow

```
User                  Browser                    FastAPI                  Ollama
 │                      │                          │                       │
 │  Drop file           │                          │                       │
 │  (.txt/.pdf/.docx)   │                          │                       │
 │─────────────────────►│                          │                       │
 │                      │  POST /api/rag/upload    │                       │
 │                      │  (multipart form-data)   │                       │
 │                      │─────────────────────────►│                       │
 │                      │                          │                       │
 │                      │                          │  1. Check extension   │
 │                      │                          │     (is_allowed)      │
 │                      │                          │                       │
 │                      │                          │  2. Extract text      │
 │                      │                          │     ├─ .txt → utf-8   │
 │                      │                          │     ├─ .docx → docx   │
 │                      │                          │     └─ .pdf  → pypdf  │
 │                      │                          │                       │
 │                      │                          │  3. Security check    │
 │                      │                          │     (SECURITY_KEYWORDS│
 │                      │                          │      ≥ 2 matches)     │
 │                      │                          │                       │
 │                      │                          │  4. Chunk text        │
 │                      │                          │     (500 words,       │
 │                      │                          │      80 overlap)      │
 │                      │                          │                       │
 │                      │                          │  5. Get embeddings    │
 │                      │                          │─────────────────────►│
 │                      │                          │◄──── embedding ───────┤
 │                      │                          │                       │
 │                      │                          │  6. Store in memory   │
 │                      │                          │     (session_store)   │
 │                      │                          │                       │
 │                      │◄── {ok, id, filename} ───┤                       │
 │◄─────────────────────┤                          │                       │
 │                      │                          │                       │
 │  Type message        │                          │                       │
 │─────────────────────►│  POST /api/chat/stream    │                       │
 │                      │─────────────────────────►│                       │
 │                      │                          │  session_retrieve()   │
 │                      │                          │  ├─ Get query emb     │
 │                      │                          │  ├─ Cos sim vs docs   │
 │                      │                          │  └─ Top-K chunks      │
 │                      │                          │                       │
 │                      │                          │  Inject into prompt:  │
 │                      │                          │  "Relevant context:\n │
 │                      │                          │   <chunk_text>"       │
```

---

## Safety & Content Filtering Flow

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────┐
│            validate_input()                      │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. check_content_safety()                       │
│     ├─ violence patterns                         │
│     ├─ self_harm patterns                        │
│     ├─ harassment patterns                       │
│     ├─ hate_speech patterns                      │
│     ├─ explicit_adult patterns                   │
│     ├─ drugs patterns                            │
│     ├─ weapons patterns                          │
│     ├─ illegal_access patterns                   │
│     └─ phishing patterns                         │
│     ┌─────────────────────┐                      │
│     │ BLOCKED? → Return   │                      │
│     │ "Blocked: category" │                      │
│     └─────────┬───────────┘                      │
│               ▼ (pass)                           │
│                                                  │
│  2. detect_prompt_injection()                    │
│     ├─ "ignore previous instructions"            │
│     ├─ "reveal system prompt"                    │
│     ├─ DAN / "do anything now"                   │
│     ├─ bypass / unfiltered / etc.                │
│     └─ 20+ injection patterns                    │
│     ┌──────────────────────────┐                 │
│     │ INJECTION? → Return      │                 │
│     │ "Prompt injection det."  │                 │
│     └──────────┬───────────────┘                 │
│               ▼ (pass)                           │
│                                                  │
│  3. check_security_relevance()                   │
│     ├─ Match against SECURITY_KEYWORDS (200+)    │
│     ├─ Allow greetings/social phrases            │
│     └─ Require ≥1 security keyword               │
│     ┌──────────────────────────────┐             │
│     │ OFF-TOPIC? → Return          │             │
│     │ "Tysor chỉ hỗ trợ Cyber..." │             │
│     └──────────┬───────────────────┘             │
│               ▼ (pass)                           │
│                                                  │
│  4. sanitize_pii()                               │
│     ├─ Email: [EMAIL]                            │
│     ├─ Phone: [PHONE]                            │
│     └─ CCCD:  [CCCD]                             │
│     ┌──────────────────────┐                     │
│     │ PII found? → Return   │                     │
│     │ sanitized text       │                     │
│     └──────────┬───────────┘                     │
│               ▼ (pass/clean)                     │
│                                                  │
│  ✅ → Pass to AgentOrchestrator                  │
│       ctx.query = sanitized (PII removed)        │
│                                                  │
└──────────────────────────────────────────────────┘
    │
    ▼
Ollama API (PII-free query)
    │
    ▼
┌──────────────────────────────────────────────────┐
│            validate_output()                     │
│  └─ check_content_safety() on response           │
│     ┌─────────────────────┐                      │
│     │ BLOCKED? → Audit +  │                      │
│     │ suppress response   │                      │
│     └─────────────────────┘                      │
└──────────────────────────────────────────────────┘
```

---

## Admin Panel Flow

```
Admin User              Browser                    FastAPI                  DB
    │                      │                          │                     │
    │  GET /admin          │                          │                     │
    │─────────────────────►│  init():                  │                     │
    │                      │  ├─ Check JWT token      │                     │
    │                      │  ├─ GET /api/auth/me     │                     │
    │                      │  ├─ role==='admin'?      │                     │
    │                      │  └─ nav('dashboard')     │                     │
    │                      │                          │                     │
    │  Click tab           │                          │                     │
    │─────────────────────►│  nav('users')            │                     │
    │                      │─────────────────────────►│                     │
    │                      │  GET /api/admin/users    │                     │
    │                      │─────────────────────────►│  SELECT * FROM users│
    │                      │                          │────────────────────►│
    │                      │◄─── {users: [...]} ──────┤◄────────────────────│
    │◄─── Render table ────┤                          │                     │
    │                      │                          │                     │
    │  Click user row      │                          │                     │
    │─────────────────────►│  openUserModal(id)        │                     │
    │                      │─────────────────────────►│                     │
    │                      │  GET /api/admin/users/N  │  JOIN activity +    │
    │                      │─────────────────────────►│  conversations      │
    │                      │                          │────────────────────►│
    │                      │◄─── {user, activity,     │◄────────────────────│
    │                      │      conversations} ─────┤                     │
    │◄─── Render modal ────┤                          │                     │
    │                      │                          │                     │
    │                      │  Dashboard stats:        │                     │
    │                      │  GET /api/admin/stats    │                     │
    │                      │─────────────────────────►│                     │
    │                      │◄─── {users, convs, msgs, │                     │
    │                      │      storage_bytes, ...} │                     │
    │                      │                          │                     │
    │                      │  Activity feed:          │                     │
    │                      │  GET /api/admin/activity │                     │
    │                      │─────────────────────────►│                     │
    │                      │◄─── {activities: [...]}  │                     │
```

---

## Agent Framework Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         AgentOrchestrator                               │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                    process_input()                           │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │     │
│  │  │  Safety      │  │  PII         │  │  Topic           │   │     │
│  │  │  Validation  │─►│  Sanitization│─►│  Relevance Check │   │     │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │     │
│  │  ┌──────────────┐  ┌────────────────────────────────────┐   │     │
│  │  │  Injection   │  │  ctx.query = result.sanitized      │   │     │
│  │  │  Detection   │─►│  (PII removed from query)          │   │     │
│  │  └──────────────┘  └────────────────────────────────────┘   │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                    build_ollama_messages()                   │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │     │
│  │  │  System      │  │  Memories    │  │  RAG Context     │   │     │
│  │  │  Prompt      │+ │  (from DB)   │+ │  (session_store) │   │     │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │     │
│  │  ┌──────────────────────────────────────────────────────┐   │     │
│  │  │  History Messages (from Conversation.messages)       │   │     │
│  │  └──────────────────────────────────────────────────────┘   │     │
│  │  ┌──────────────────────────────────────────────────────┐   │     │
│  │  │  User Query (sanitized, PII-free)                    │   │     │
│  │  └──────────────────────────────────────────────────────┘   │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                    get_adaptive_config()                     │     │
│  │  Short query (≤10 words)  → max_tokens=512, temp=0.7       │     │
│  │  Medium query             → max_tokens=2048, temp=0.7       │     │
│  │  Complex query (≥50 words)→ max_tokens=4096, temp=0.8       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                    process_response()                        │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │     │
│  │  │  Output      │  │  Safety      │  │  Memory          │   │     │
│  │  │  Validation  │  │  Check       │  │  Extraction      │   │     │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │     │
│  │  ┌──────────────────────────────────────────────────────┐   │     │
│  │  │  Audit Log (chat event, latency, tokens, flagged)    │   │     │
│  │  └──────────────────────────────────────────────────────┘   │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────┐       ┌─────────────────────┐
│     users       │       │   conversations     │
├─────────────────┤       ├─────────────────────┤
│ id (PK)         │◄──────│ id (PK)             │
│ username (UQ)   │       │ user_id (FK)        │
│ email (UQ)      │       │ title               │
│ password_hash   │       │ created_at          │
│ role            │       │ updated_at          │
│ is_active       │       └──────────┬──────────┘
│ created_at      │                  │
└────────┬────────┘                  │
         │                          │
         │  ┌─────────────────┐     │
         │  │    messages     │     │
         │  ├─────────────────┤     │
         └──│ id (PK)         │     │
            │ conversation_id─│─────┘
            │ role (FK)       │
            │ content         │
            │ timestamp       │
            └─────────────────┘

┌─────────────────┐       ┌─────────────────────┐
│    memories     │       │    audit_logs       │
├─────────────────┤       ├─────────────────────┤
│ id (PK)         │       │ id (PK)             │
│ user_id (FK)    │       │ user_id (FK)        │
│ key             │       │ event               │
│ value           │       │ detail (JSON)       │
│ source          │       │ ip_address          │
│ confidence      │       │ created_at          │
│ created_at      │       └─────────────────────┘
│ updated_at      │
└─────────────────┘

┌─────────────────────┐   ┌─────────────────────────┐
│  rag_documents      │   │    rag_chunks            │
├─────────────────────┤   ├─────────────────────────┤
│ id (PK)             │   │ id (PK)                 │
│ user_id (FK)        │   │ document_id (FK)────────┤
│ filename            │   │ chunk_index             │
│ content (TEXT)      │   │ content (TEXT)          │
│ chunk_count         │   │ embedding (JSON TEXT)    │
│ created_at          │   └─────────────────────────┘
└─────────────────────┘

┌─────────────────────┐
│  user_preferences   │
├─────────────────────┤
│ id (PK)             │
│ user_id (FK, UQ)    │
│ language            │
│ theme               │
│ max_tokens          │
│ temperature         │
│ extra (JSON)        │
└─────────────────────┘
```

---

## Project Structure

```
D:\Code\ai\chabot_ollama\
│
├── app_backend.py        # Main FastAPI application (all routes)
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
python -m uvicorn app_backend:app --host 127.0.0.1 --port 8000

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

---

## License

MIT License
