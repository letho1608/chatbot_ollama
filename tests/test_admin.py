"""Admin API endpoint tests: stats, users, activity, audit, system."""

import json


class TestAdminAccess:
    def test_admin_can_access(self, client, admin_headers):
        resp = client.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200

    def test_user_cannot_access(self, client, user_headers):
        resp = client.get("/api/admin/stats", headers=user_headers)
        assert resp.status_code == 403


class TestAdminStats:
    def test_stats_structure(self, client, admin_headers):
        resp = client.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        for key in ["users", "conversations", "messages", "storage_bytes"]:
            assert key in data


class TestAdminUsers:
    def test_list_users(self, client, admin_headers, normal_user):
        resp = client.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        usernames = [u["username"] for u in data["users"]]
        assert "admin" in usernames

    def test_user_detail(self, client, admin_headers, normal_user):
        resp = client.get(f"/api/admin/users/{normal_user.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == normal_user.username


class TestAdminConversations:
    def test_list_conversations(self, client, admin_headers):
        resp = client.get("/api/admin/conversations", headers=admin_headers)
        assert resp.status_code == 200
        assert "conversations" in resp.json()


class TestAdminActivity:
    def test_activity_feed(self, client, admin_headers):
        resp = client.get("/api/admin/activity", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "activities" in data


class TestAdminAudit:
    def test_audit_log(self, client, admin_headers):
        resp = client.get("/api/admin/audit", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data


class TestAdminSystem:
    def test_system_info(self, client, admin_headers):
        resp = client.get("/api/admin/system", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        for key in ["python_version", "platform", "ram_total"]:
            assert key in data


class TestAdminTunnel:
    def test_tunnel_status(self, client, admin_headers):
        resp = client.get("/api/admin/tunnel", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert "url" in data
