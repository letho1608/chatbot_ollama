# Tysor diagrams

Các sơ đồ Mermaid dưới đây phản ánh luồng hiện tại trong mã nguồn. Bản Word sử dụng ảnh PNG tương ứng trong `docs/diagrams` để mở ổn định khi không có mạng.

## 1. System Architecture

```mermaid
flowchart TB
    Browser["Web Browser\nDashboard / Login / Chat / Admin"]
    FastAPI["FastAPI Server\nPages + REST API + SSE"]
    Agent["Agent Framework\nSafety / Memory / Validator / Monitor / Queue"]
    Hybrid["Hybrid Retrieval\nSession RAG + GraphRAG + Web fallback"]
    SQLite["SQLite\ndata/chatbot.db"]
    Ollama["Ollama 127.0.0.1:11434\n/api/chat /api/embeddings /api/pull /api/tags"]
    Dataset["AISecKG dataset\nCSV triples + entity info"]
    Web["Trusted Cyber Security websites"]
    Tunnel["Cloudflare Tunnel\noptional public URL"]

    Browser -->|HTTP / SSE| FastAPI
    Tunnel --> Browser
    FastAPI --> Agent
    FastAPI --> SQLite
    Agent --> Hybrid
    Agent --> Ollama
    Hybrid --> Ollama
    Hybrid --> Dataset
    Hybrid --> Web
```

## 2. Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant F as FastAPI
    participant D as SQLite
    U->>B: Submit register or login form
    B->>F: POST /api/auth/register or /api/auth/login
    F->>D: Validate account
    D-->>F: User row
    F->>F: Hash or verify password, create JWT
    F->>D: Write audit log
    F-->>B: JWT cookie + JSON token and role
    B->>B: Store token in localStorage
    B->>F: GET /api/auth/me
    F-->>B: Current user and role
    B-->>U: /chat for user, /admin for admin
```

## 3. Chat Streaming Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant F as FastAPI
    participant A as Agent
    participant Q as Queue
    participant O as Ollama
    participant D as SQLite
    U->>B: Enter Cyber Security question
    B->>F: POST /api/chat/stream
    F->>A: process_input()
    A->>A: safety + injection + topic + sensitive redaction
    F->>D: Save original user message
    F->>A: build_ollama_messages()
    A->>A: system prompt + memory + hybrid RAG + history
    F->>F: adaptive config + rate limit
    F->>Q: enqueue()
    Q->>O: POST /api/chat, one Ollama call at a time
    O-->>F: streamed chunks
    F->>F: redact sensitive streamed output
    F-->>B: SSE chunks
    B-->>U: Render Markdown
    F->>D: Save assistant response
    F->>A: output validation + memory extraction + audit
```

## 4. Hybrid RAG Flow

```mermaid
flowchart TB
    Upload["POST /api/rag/upload-file"] --> Ext{"Allowed extension?"}
    Ext -->|No| Reject["Return 400"]
    Ext -->|Yes| Extract["Extract text"]
    Extract --> Sec{"At least 50 chars and 2 security keywords?"}
    Sec -->|No| Reject
    Sec -->|Yes| Chunk["Chunk: 500 words, overlap 80"]
    Chunk --> Embed["Ollama /api/embeddings\nnomic-embed-text"]
    Embed --> Session["Per-user in-memory session_store"]
    Query["Chat query"] --> SessionSearch["Session cosine similarity"]
    Query --> Graph["GraphRAG over AISecKG"]
    SessionSearch --> Merge["Merge retrieval context"]
    Graph --> Merge
    Merge --> Confident{"Confident hit and not fresh-web query?"}
    Confident -->|Yes| Prompt["Inject context into system prompt"]
    Confident -->|No| Web["Trusted-domain web fallback"]
    Web --> Prompt
```

## 5. Safety And Redaction Flow

```mermaid
flowchart TB
    Query["User query"] --> Content["check_content_safety()"]
    Content --> Injection["detect_prompt_injection()"]
    Injection --> Topic["check_security_relevance()\nunless greeting/social"]
    Topic --> Sensitive["sanitize_sensitive()\nsecrets + PII"]
    Sensitive --> Ollama["Ollama /api/chat"]
    Ollama --> Stream["Stream chunks"]
    Stream --> Redact["sanitize_sensitive() before SSE"]
    Redact --> Browser["Browser"]
    Stream --> Post["process_response()"]
    Post --> Validate["validate_response() + validate_output()"]
    Validate --> Memory["memory extraction"]
    Memory --> Audit["audit log"]
```

## 6. Admin Flow

```mermaid
flowchart TB
    Admin["Admin browser /admin"] --> Auth["GET /api/auth/me\nrequire role=admin"]
    Auth --> Dashboard["Dashboard stats + activity"]
    Auth --> Users["Users: detail / role / toggle / delete"]
    Auth --> Models["Models: list / pull / delete"]
    Auth --> Conversations["Browse conversations"]
    Auth --> Audit["Audit logs"]
    Auth --> System["System health"]
    System --> Ollama["Ollama status"]
    System --> Resource["RAM / disk / process / AI log"]
    System --> Tunnel["Cloudflare tunnel start / stop"]
```

## 7. Agent Framework

```mermaid
flowchart TB
    Input["process_input()\nsafety + redaction"] --> Build["build_ollama_messages()"]
    Build --> Prompt["Base prompt + custom system prompt"]
    Build --> Memory["Persistent user memories"]
    Build --> Hybrid["Hybrid RAG context"]
    Build --> History["Trimmed conversation history"]
    Prompt --> Ollama["Ollama messages"]
    Memory --> Ollama
    Hybrid --> Ollama
    History --> Ollama
    Ollama --> Adaptive["Adaptive options\n512 / 2048 / 4096 max tokens"]
    Adaptive --> Response["process_response()"]
    Response --> Validate["Validator + output safety"]
    Response --> Extract["Memory extraction"]
    Response --> Monitor["Audit and AI log"]
```

## 8. SQLite Schema

```mermaid
erDiagram
    users ||--o{ conversations : has
    conversations ||--o{ messages : contains
    users ||--o{ memories : has
    users ||--o{ audit_logs : emits
    users ||--o| user_preferences : configures
    users ||--o{ rag_documents : owns
    rag_documents ||--o{ rag_chunks : contains
```
