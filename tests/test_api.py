"""API endpoint tests: conversations, models, RAG upload."""

import json
import io


class TestConversations:
    def test_list_empty(self, client, user_headers):
        resp = client.get("/api/conversations", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["conversations"] == []

    def test_create_via_chat(self, app, user_headers):
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.post("/api/chat/stream", headers=user_headers, json={
                "message": "Xin chào"
            })
            assert resp.status_code in (200, 400, 503)

    def test_list_after_create(self, client, user_headers):
        resp = client.get("/api/conversations", headers=user_headers)
        assert resp.status_code == 200

    def test_delete_conversation(self, client, user_headers, db, normal_user, conversation):
        resp = client.delete(f"/api/conversations/{conversation.id}", headers=user_headers)
        assert resp.status_code == 200

    def test_delete_other_users_conversation(self, client, user_headers, db, normal_user, admin_user):
        from core.database import Conversation
        conv = Conversation(id="test-conv-admin", user_id=admin_user.id, title="Admin conversation")
        db.add(conv)
        db.commit()
        resp = client.delete(f"/api/conversations/{conv.id}", headers=user_headers)
        assert resp.status_code == 404

    def test_update_title(self, client, user_headers, db, normal_user, conversation):
        resp = client.put(f"/api/conversations/{conversation.id}", headers=user_headers, json={
            "title": "Updated title"
        })
        assert resp.status_code == 200


class TestModels:
    def test_list_models(self, client, user_headers):
        resp = client.get("/api/models", headers=user_headers)
        assert resp.status_code == 200
        assert "models" in resp.json()

    def test_catalog(self, client, user_headers):
        resp = client.get("/api/models/catalog", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "categories" in data


class TestRAG:
    def test_upload_security_txt(self, client, user_headers):
        content = b"Security analysis of firewall penetration testing methodology"
        resp = client.post("/api/rag/upload-file", headers=user_headers, files={
            "file": ("test.txt", io.BytesIO(content), "text/plain")
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

    def test_upload_non_security(self, client, user_headers):
        content = b"Cooking recipe for spaghetti bolognese"
        resp = client.post("/api/rag/upload-file", headers=user_headers, files={
            "file": ("recipe.txt", io.BytesIO(content), "text/plain")
        })
        assert resp.status_code == 400

    def test_upload_invalid_extension(self, client, user_headers):
        resp = client.post("/api/rag/upload-file", headers=user_headers, files={
            "file": ("virus.exe", io.BytesIO(b"hack"), "application/octet-stream")
        })
        assert resp.status_code == 400

    def test_list_documents(self, client, user_headers):
        resp = client.get("/api/rag/documents", headers=user_headers)
        assert resp.status_code == 200
        assert "documents" in resp.json()
