import asyncio
import json
import os
import time as time_module
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import init_db, get_db, User, Conversation, Message, Memory
from core.auth import hash_password, verify_password, create_access_token, decode_token
from core.agent import AgentOrchestrator, AgentContext
from core.config import AgentConfig
from core.monitor import logger as audit_logger
from core.memory import get_relevant_memories, set_memory, delete_memory, format_memories_for_prompt
from core.queue import queue, rate_limiter

OLLAMA_BASE = "http://127.0.0.1:11434"
OLLAMA_CONNECT_TIMEOUT = 5.0
OLLAMA_READ_TIMEOUT = 120.0

app = FastAPI(title="Ollama Chat")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory="templates")

agent = AgentOrchestrator()


def format_ollama_error(exc: Exception | None = None, status_code: int | None = None, detail: str = "") -> str:
    if status_code:
        clean_detail = detail.strip()[:500]
        return f"Ollama trả về lỗi HTTP {status_code}" + (f": {clean_detail}" if clean_detail else ".")
    if isinstance(exc, httpx.ConnectError):
        return "Không thể kết nối Ollama. Hãy chạy `ollama serve` hoặc mở Ollama app."
    if isinstance(exc, httpx.TimeoutException):
        return "Ollama phản hồi quá lâu. Hãy thử model nhẹ hơn, giảm max tokens hoặc kiểm tra máy đang tải nặng."
    if exc:
        return f"Lỗi khi gọi Ollama: {str(exc)}"
    return "Lỗi không xác định khi gọi Ollama."


def get_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else ""


# ─── Auth Dependency ─────────────────────────────────────────────────────────
def get_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get("ollama_token")


async def require_user(request: Request, db: Session = Depends(get_db)):
    token = get_token(request)
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    uid = int(payload.get("sub"))
    user = db.query(User).filter(User.id == uid).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    request.state.user_id = uid
    request.state.user_role = payload.get("role", "user")
    request.state.username = payload.get("username", "")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)):
    token = get_token(request)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    try:
        uid = int(payload.get("sub"))
        user = db.query(User).filter(User.id == uid).first()
        return user
    except (ValueError, TypeError):
        return None


# ─── Models ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str = "qwen2:7b"
    system_prompt: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048


class TitleUpdate(BaseModel):
    title: str


# ─── Pages ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        url = "/admin" if user.role == "admin" else "/chat"
        return RedirectResponse(url=url)
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse("index.html", {"request": request, "username": user.username, "role": user.role})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        url = "/admin" if user.role == "admin" else "/chat"
        return RedirectResponse(url=url)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: User = Depends(require_user)):
    if user.role != "admin":
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse("admin.html", {"request": request, "username": user.username, "role": user.role})


# ─── Auth API ─────────────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if len(req.username) < 3 or len(req.password) < 6:
        raise HTTPException(400, "Username min 3 chars, password min 6 chars")
    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        raise HTTPException(400, "Username or email already exists")

    user = User(username=req.username, email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
    resp = JSONResponse({"ok": True, "token": token, "username": user.username, "role": user.role})
    resp.set_cookie(key="ollama_token", value=token, httponly=True, max_age=30*86400, samesite="lax", path="/")

    audit_logger.log(user.id, "register", {}, get_ip(request), db)
    db.commit()
    return resp


@app.post("/api/auth/login")
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        audit_logger.log(None, "login_failed", {"username": req.username}, get_ip(request), db)
        db.commit()
        raise HTTPException(401, "Invalid username or password")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")

    token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})
    resp = JSONResponse({"ok": True, "token": token, "username": user.username, "role": user.role})
    resp.set_cookie(key="ollama_token", value=token, httponly=True, max_age=30*86400, samesite="lax", path="/")

    audit_logger.log(user.id, "login", {}, get_ip(request), db)
    db.commit()
    return resp


@app.get("/api/auth/me")
async def me(user: User = Depends(require_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "created_at": user.created_at.isoformat()}


@app.post("/api/auth/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("ollama_token", path="/")
    return resp


# ─── Conversations API ────────────────────────────────────────────────────────
@app.get("/api/conversations")
async def list_conversations(user: User = Depends(require_user), db: Session = Depends(get_db)):
    convs = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).all()
    return {"conversations": [{"id": c.id, "title": c.title, "created": c.created_at.isoformat(), "updated": c.updated_at.isoformat(), "message_count": len(c.messages)} for c in convs]}


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {"id": conv.id, "title": conv.title, "created": conv.created_at.isoformat(), "messages": [{"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in conv.messages]}


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    db.delete(conv)
    db.commit()
    return {"ok": True}


@app.put("/api/conversations/{conv_id}")
async def update_conversation(conv_id: str, upd: TitleUpdate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    conv.title = upd.title
    db.commit()
    return {"ok": True}


# ─── Memory API ───────────────────────────────────────────────────────────────
@app.get("/api/memories")
async def list_memories(user: User = Depends(require_user), db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.user_id == user.id).order_by(Memory.updated_at.desc()).all()
    return {"memories": [{"key": m.key, "value": m.value, "source": m.source, "confidence": m.confidence, "updated": m.updated_at.isoformat()} for m in memories]}


@app.post("/api/memories")
async def create_memory(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    body = await request.json()
    key = body.get("key", "").strip()
    value = body.get("value", "").strip()
    if not key or not value:
        raise HTTPException(400, "key and value required")
    set_memory(user.id, key, value, db, "manual", 100)
    db.commit()
    return {"ok": True}


@app.delete("/api/memories/{key}")
async def remove_memory(key: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    delete_memory(user.id, key, db)
    db.commit()
    return {"ok": True}


# ─── Chat API ─────────────────────────────────────────────────────────────────
@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    conv_id = req.conversation_id or str(uuid.uuid4())

    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user.id).first()
    if not conv:
        conv = Conversation(id=conv_id, user_id=user.id)
        db.add(conv)
        db.commit()

    ctx = AgentContext(
        user_id=user.id,
        username=user.username,
        query=req.message,
        conversation_id=conv_id,
        model=req.model,
        system_prompt=req.system_prompt,
        temperature=req.temperature,
        top_p=req.top_p,
        top_k=req.top_k,
        max_tokens=req.max_tokens,
        start_time=time_module.time(),
    )

    ok, err_msg = agent.process_input(ctx, db, get_ip(request))
    if not ok:
        return JSONResponse({"error": err_msg}, status_code=400)

    msg = Message(conversation_id=conv_id, role="user", content=req.message)
    db.add(msg)
    db.commit()

    # Auto-name conversation from first user message
    msg_count = db.query(Message).filter(Message.conversation_id == conv_id).count()
    if msg_count <= 2:
        title = req.message[:80].strip().replace("\n", " ").replace("\r", "") or "New conversation"
        if len(title) > 60:
            title = title[:57] + "..."
        conv.title = title
        db.commit()

    history = list(db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.timestamp).all())
    ctx.history_messages = history[:-1]

    ollama_messages = agent.build_ollama_messages(ctx, db)

    adaptive = agent.get_adaptive_config(req.message)
    final_max_tokens = adaptive.get("max_tokens", req.max_tokens)
    final_temperature = adaptive.get("temperature", req.temperature)
    ollama_options = {
        "temperature": final_temperature,
        "top_p": req.top_p,
        "top_k": req.top_k,
        "num_predict": final_max_tokens,
    }

    audit_logger.log_system_prompt(
        user_id=user.id,
        username=user.username,
        conversation_id=conv_id,
        model=req.model,
        messages=ollama_messages,
        options=ollama_options,
        ip=get_ip(request),
    )

    ok2, rem = rate_limiter.check(user.id)
    if not ok2:
        return JSONResponse({"error": "Quá nhiều yêu cầu. Vui lòng đợi 60s."}, status_code=429)

    event_channel: asyncio.Queue[dict] = asyncio.Queue()

    async def handler():
        await queue.acquire_ollama()
        try:
            timeout = httpx.Timeout(OLLAMA_READ_TIMEOUT, connect=OLLAMA_CONNECT_TIMEOUT)
            async with httpx.AsyncClient(timeout=timeout) as client:
                full = ""
                for attempt in range(agent.config.max_retries):
                    try:
                        if attempt > 0:
                            await event_channel.put({
                                "content": f"\n\nĐang thử lại kết nối Ollama lần {attempt + 1}/{agent.config.max_retries}...\n\n",
                                "conversation_id": conv_id,
                            })

                        async with client.stream(
                            "POST",
                            f"{OLLAMA_BASE}/api/chat",
                            json={
                                "model": req.model,
                                "messages": ollama_messages,
                                "stream": True,
                                "options": ollama_options,
                            },
                        ) as resp:
                            if resp.status_code != 200:
                                err = await resp.aread()
                                await event_channel.put({
                                    "error": format_ollama_error(status_code=resp.status_code, detail=err.decode(errors="replace"))
                                })
                                return

                            async for line in resp.aiter_lines():
                                if not line.strip():
                                    continue
                                try:
                                    chunk = json.loads(line)
                                except json.JSONDecodeError:
                                    continue

                                content = chunk.get("message", {}).get("content", "")
                                full += content
                                done = chunk.get("done", False)
                                await event_channel.put({"content": content, "done": done, "conversation_id": conv_id})

                                if done:
                                    if not full.strip():
                                        await event_channel.put({"error": "Ollama trả về phản hồi rỗng. Hãy thử lại hoặc chọn model khác."})
                                        return

                                    db2 = next(get_db())
                                    try:
                                        asst_msg = Message(conversation_id=conv_id, role="assistant", content=full)
                                        db2.add(asst_msg)
                                        conv2 = db2.query(Conversation).filter(Conversation.id == conv_id).first()
                                        if conv2:
                                            conv2.updated_at = datetime.now(timezone.utc)
                                        db2.commit()
                                        agent.process_response(ctx, full, db2, get_ip(request))
                                        db2.commit()
                                    finally:
                                        db2.close()
                                    return
                        if full.strip():
                            return
                    except (httpx.ConnectError, httpx.TimeoutException) as e:
                        if full.strip() or attempt == agent.config.max_retries - 1:
                            await event_channel.put({"error": format_ollama_error(e)})
                            return
                        await asyncio.sleep(0.5 * (attempt + 1))
                    except Exception as e:
                        await event_channel.put({"error": format_ollama_error(e)})
                        return

                await event_channel.put({"error": "Dừng xử lý: đạt số lần thử tối đa khi gọi Ollama."})
        finally:
            queue.release_ollama()
            await event_channel.put({"done": True, "internal": True})

    await queue.enqueue(user.id, user.username, conv_id, handler)
    pos = await queue.get_position(conv_id)

    async def generate():
        if pos > 0:
            yield f"data: {json.dumps({'queue': pos, 'content': f'⏳ Đang chờ... Vị trí: #{pos}'})}\n\n"

        while True:
            event = await event_channel.get()
            if event.get("done") and event.get("internal"):
                break
            if "error" in event:
                yield f"data: {json.dumps(event)}\n\n"
                return
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─── RAG API (session-only, file upload, cyber security only) ────────────────
from core.rag import (
    store_document_sync, retrieve, format_rag_context,
    store_session_document, get_session_docs, delete_session_doc,
    session_retrieve, is_security_content, is_allowed_extension,
    extract_text_from_bytes, session_store,
)
from fastapi import UploadFile, File, Form
from core.database import Document
import os as os_mod


@app.post("/api/rag/upload-file")
async def rag_upload_file(
    file: UploadFile = File(...),
    user: User = Depends(require_user),
):
    if not is_allowed_extension(file.filename or "file.txt"):
        raise HTTPException(400, f"Định dạng file không được hỗ trợ. Chấp nhận: .txt, .md, .csv, .log, .json, .docx, .pdf, ...")

    raw = await file.read()
    content = extract_text_from_bytes(raw, file.filename or "file.txt")
    if not content:
        raise HTTPException(400, "Không thể đọc nội dung file hoặc file rỗng")

    ok, reason = is_security_content(content)
    if not ok:
        raise HTTPException(400, f"❌ {reason}")

    doc = store_session_document(user.id, file.filename or "document.txt", content)
    return {"ok": True, "id": doc["id"], "filename": doc["filename"], "chunks": doc["chunk_count"]}


@app.get("/api/rag/documents")
async def rag_list(user: User = Depends(require_user)):
    docs = get_session_docs(user.id)
    return {"documents": [{"id": d["id"], "filename": d["filename"], "chunks": d["chunk_count"]} for d in docs]}


@app.delete("/api/rag/documents/{doc_id}")
async def rag_delete(doc_id: str, user: User = Depends(require_user)):
    ok = delete_session_doc(user.id, doc_id)
    if not ok:
        raise HTTPException(404, "Document not found")
    return {"ok": True}


@app.get("/api/rag/search")
async def rag_search(q: str = "", user: User = Depends(require_user)):
    if not q:
        return {"results": []}
    results = session_retrieve(user.id, q)
    return {"results": [{"content": r[0][:200], "score": round(r[1], 3)} for r in results]}


# ─── Models API ───────────────────────────────────────────────────────────────
@app.get("/api/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return {"models": sorted(set(m["name"] for m in data.get("models", [])))}
            return {"models": [], "error": f"Ollama returned {resp.status_code}"}
    except httpx.ConnectError:
        return {"models": [], "error": "Cannot connect to Ollama"}


@app.get("/api/models/catalog")
async def model_catalog():
    from core.config import MODEL_CATALOG, MODEL_CATEGORIES
    installed = set()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                installed = set(m["name"] for m in data.get("models", []))
    except Exception:
        pass
    models = []
    for m in MODEL_CATALOG:
        models.append({
            "name": m.name,
            "category": m.category,
            "description": m.description,
            "display_name": m.display_name or m.name.split(":")[0],
            "installed": m.name in installed,
        })
    return {"models": models, "categories": MODEL_CATEGORIES}


@app.post("/api/models/pull")
async def pull_model(request: Request, user: User = Depends(require_user)):
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Model name required")

    async def pull_stream():
        async with httpx.AsyncClient(timeout=600) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE}/api/pull",
                    json={"name": name, "stream": True},
                ) as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'error': f'Pull failed: {resp.status_code}'})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                status = chunk.get("status", "")
                                progress = {}
                                if "completed" in chunk and "total" in chunk:
                                    progress = {"completed": chunk["completed"], "total": chunk["total"]}
                                yield f"data: {json.dumps({'status': status, 'progress': progress, 'done': chunk.get('status') == 'success'})}\n\n"
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(pull_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─── Admin API ────────────────────────────────────────────────────────────────
def require_admin(user: User = Depends(require_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return user


@app.get("/api/admin/users")
async def admin_list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from core.database import AuditLog
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        last_active = db.query(AuditLog.created_at).filter(
            AuditLog.user_id == u.id, AuditLog.event.in_(["login", "chat"])
        ).order_by(AuditLog.created_at.desc()).first()
        result.append({
            "id": u.id, "username": u.username, "email": u.email,
            "role": u.role, "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat(),
            "conv_count": len(u.conversations),
            "last_active": last_active[0].isoformat() if last_active else None,
        })
    return {"users": result}


@app.put("/api/admin/users/{user_id}/role")
async def admin_update_role(user_id: int, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    body = await request.json()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.role = body.get("role", user.role)
    db.commit()
    return {"ok": True}


@app.put("/api/admin/users/{user_id}/toggle")
async def admin_toggle_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot disable yourself")
    user.is_active = 0 if user.is_active else 1
    db.commit()
    return {"ok": True, "is_active": user.is_active}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/audit")
async def admin_audit_log(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 100, event: str = "", user_id: int = 0):
    from core.database import AuditLog
    query = db.query(AuditLog, User.username).outerjoin(User, User.id == AuditLog.user_id)
    if event:
        query = query.filter(AuditLog.event == event)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{
        "id": l.AuditLog.id, "user_id": l.AuditLog.user_id,
        "event": l.AuditLog.event, "detail": l.AuditLog.detail,
        "ip": l.AuditLog.ip_address, "created": l.AuditLog.created_at.isoformat(),
        "username": l.username or "System",
    } for l in logs]}


@app.get("/api/admin/stats")
async def admin_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    user_count = db.query(User).count()
    conv_count = db.query(Conversation).count()
    msg_count = db.query(Message).count()
    active_users = db.query(User).filter(User.is_active == 1).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    convs_today = db.query(Conversation).filter(Conversation.created_at >= today_start).count()
    msgs_today = db.query(Message).filter(Message.timestamp >= today_start).count()
    convs_week = db.query(Conversation).filter(Conversation.created_at >= today_start - timedelta(days=7)).count()
    total_storage = 0
    db_path = os_mod.path.join("data", "chatbot.db")
    if os_mod.path.exists(db_path):
        total_storage = os_mod.path.getsize(db_path)
    return {
        "users": user_count, "conversations": conv_count, "messages": msg_count,
        "active_users": active_users, "admins": admin_count,
        "convs_today": convs_today, "msgs_today": msgs_today,
        "convs_week": convs_week,
        "storage_bytes": total_storage,
    }


@app.get("/api/admin/conversations")
async def admin_list_conversations(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 50, search: str = ""):
    query = db.query(Conversation)
    if search:
        query = query.filter(Conversation.title.ilike(f"%{search}%"))
    total = query.count()
    convs = query.order_by(Conversation.updated_at.desc()).limit(limit).all()
    result = []
    for c in convs:
        last_msg = db.query(Message.content, Message.role).filter(
            Message.conversation_id == c.id, Message.role == "assistant"
        ).order_by(Message.timestamp.desc()).first()
        result.append({
            "id": c.id, "title": c.title or "Untitled",
            "username": c.user.username if c.user else "Deleted",
            "user_id": c.user_id,
            "msg_count": len(c.messages),
            "created": c.created_at.isoformat() if c.created_at else "",
            "updated": c.updated_at.isoformat() if c.updated_at else "",
            "last_message": last_msg[0][:150] if last_msg and last_msg[0] else None,
            "last_role": last_msg[1] if last_msg else None,
        })
    return {"conversations": result, "total": total}


@app.delete("/api/admin/models/{model_name}")
async def admin_delete_model(model_name: str, admin: User = Depends(require_admin)):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(f"{OLLAMA_BASE}/api/delete", json={"name": model_name})
            if resp.status_code == 200:
                return {"ok": True}
            return {"ok": False, "error": f"Ollama returned {resp.status_code}"}
    except httpx.ConnectError:
        raise HTTPException(502, "Cannot connect to Ollama")


@app.get("/api/admin/activity")
async def admin_activity(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 50):
    """Combined activity feed: audit logs + recent messages with user context."""
    from core.database import AuditLog
    from sqlalchemy import case

    logs = db.query(
        AuditLog.id, AuditLog.event, AuditLog.detail, AuditLog.ip_address,
        AuditLog.created_at, AuditLog.user_id, User.username
    ).outerjoin(User, User.id == AuditLog.user_id).order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()

    recent_msgs = db.query(
        Message.id, Message.content, Message.timestamp,
        Message.conversation_id, Message.role,
        Conversation.user_id, Conversation.title,
        User.username
    ).join(Conversation, Conversation.id == Message.conversation_id
    ).outerjoin(User, User.id == Conversation.user_id
    ).order_by(Message.timestamp.desc()).limit(20).all()

    items = []

    for l in logs:
        items.append({
            "type": "event",
            "id": f"e{l.id}",
            "event": l.event,
            "detail": l.detail,
            "user_id": l.user_id,
            "username": l.username or "System",
            "ip": l.ip_address,
            "created": l.created_at.isoformat(),
        })

    for m in recent_msgs:
        items.append({
            "type": "message",
            "id": f"m{m.id}",
            "event": "chat_message",
            "detail": {"role": m.role, "content": m.content[:200], "conv_title": m.title, "conv_id": m.conversation_id},
            "user_id": m.user_id,
            "username": m.username or "Unknown",
            "ip": None,
            "created": m.timestamp.isoformat(),
        })

    items.sort(key=lambda x: x["created"], reverse=True)
    items = items[:limit]

    return {"activities": items, "total": len(items)}


@app.get("/api/admin/users/{user_id}")
async def admin_user_detail(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Single user detail with conversations and recent activity."""
    from core.database import AuditLog
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    convs = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).limit(20).all()
    conv_list = [{
        "id": c.id, "title": c.title, "msg_count": len(c.messages),
        "created": c.created_at.isoformat(), "updated": c.updated_at.isoformat(),
    } for c in convs]

    msg_count = db.query(Message).join(Conversation).filter(Conversation.user_id == user_id).count()

    logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(30).all()
    activity_list = [{
        "id": l.id, "event": l.event, "detail": l.detail,
        "ip": l.ip_address, "created": l.created_at.isoformat(),
    } for l in logs]

    last_active = db.query(AuditLog.created_at).filter(
        AuditLog.user_id == user_id
    ).order_by(AuditLog.created_at.desc()).first()

    return {
        "user": {
            "id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "is_active": bool(user.is_active),
            "created_at": user.created_at.isoformat(),
            "conv_count": len(convs),
            "msg_count": msg_count,
            "last_active": last_active[0].isoformat() if last_active else None,
        },
        "conversations": conv_list,
        "activity": activity_list,
    }


@app.post("/api/admin/tunnel/start")
async def admin_tunnel_start(admin: User = Depends(require_admin)):
    from core.tunnel import start_tunnel, get_tunnel_url
    start_tunnel()
    import asyncio
    await asyncio.sleep(3)
    return {"ok": True, "url": get_tunnel_url() or ""}


@app.post("/api/admin/tunnel/stop")
async def admin_tunnel_stop(admin: User = Depends(require_admin)):
    from core.tunnel import stop_tunnel
    stop_tunnel()
    return {"ok": True}


@app.get("/api/admin/tunnel")
async def admin_tunnel_status(admin: User = Depends(require_admin)):
    from core.tunnel import tunnel_status
    return tunnel_status()


@app.get("/api/admin/system")
async def admin_system(admin: User = Depends(require_admin)):
    import sys, platform, shutil
    ollama_ok = False
    ollama_models = 0
    ollama_server = ""
    ollama_version = ""
    model_details = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                data = resp.json()
                models = data.get("models", [])
                ollama_models = len(models)
                model_details = [{
                    "name": m["name"],
                    "size": m.get("size", 0),
                    "modified": m.get("modified_at", ""),
                    "digest": m.get("digest", "")[:12],
                } for m in models][:20]
                ollama_server = f"Ollama API"
                try:
                    vresp = await client.get(f"{OLLAMA_BASE}/api/version", timeout=3)
                    if vresp.status_code == 200:
                        ollama_version = vresp.json().get("version", "")
                except Exception:
                    pass
    except Exception:
        pass

    db_path = os_mod.path.join("data", "chatbot.db")
    db_size = os_mod.path.getsize(db_path) if os_mod.path.exists(db_path) else 0
    total, used, free = shutil.disk_usage(os_mod.path.abspath("."))
    import psutil
    mem = psutil.virtual_memory()
    proc = psutil.Process()
    return {
        "ollama_ok": ollama_ok,
        "ollama_models": ollama_models,
        "ollama_server": ollama_server,
        "ollama_version": ollama_version,
        "model_details": model_details,
        "python_version": sys.version.split()[0],
        "platform": platform.system() + " " + platform.release(),
        "uptime": "N/A",
        "db_size_bytes": db_size,
        "disk_total": total,
        "disk_free": free,
        "disk_used": used,
        "ram_total": mem.total,
        "ram_available": mem.available,
        "ram_percent": mem.percent,
        "process_memory_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
        "process_cpu_percent": proc.cpu_percent(interval=0.1),
    }


# ─── Init ─────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    init_db()
    db = next(get_db())
    try:
        if not db.query(User).filter(User.role == "admin").first():
            admin = User(username="admin", email="admin@chat.local", password_hash=hash_password("admin123"), role="admin")
            db.add(admin)
            db.commit()
    finally:
        db.close()

    # Auto-scaling worker pool
    await queue.start()

    # Cloudflare tunnel — managed via start.bat or admin panel only
    # (auto-start disabled; use start.bat for automatic tunnel)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
