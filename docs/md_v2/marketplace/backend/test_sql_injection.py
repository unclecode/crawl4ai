"""SQL injection regression test for the marketplace backend.

Runs the real server.py on a copy of the backend folder, with a throwaway .env,
same approach as the private repro script. No fixtures, standalone pytest file.

Run with: <python with fastapi/httpx/pyyaml/dotenv/multipart> -m pytest test_sql_injection.py -v
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def client():
    work = Path(tempfile.mkdtemp()) / "backend"
    shutil.copytree(SRC, work, ignore=shutil.ignore_patterns("__pycache__", "uploads", "test_sql_injection.py"))
    (work / ".env").write_text("MARKETPLACE_ADMIN_PASSWORD=x\nMARKETPLACE_JWT_SECRET=y\n")

    old_cwd = os.getcwd()
    os.chdir(work)
    sys.path.insert(0, str(work))

    # Fresh import each run since module state (db connection) is process-global
    sys.modules.pop("server", None)
    sys.modules.pop("database", None)
    sys.modules.pop("config", None)
    import server

    from fastapi.testclient import TestClient
    c = TestClient(server.app, raise_server_exceptions=False)
    c.server_module = server
    yield c

    os.chdir(old_cwd)
    sys.path.remove(str(work))


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post("/marketplace/api/admin/login", json={"password": "x"})
    assert r.status_code == 200
    return r.json()["token"]


BASE = "/marketplace/api"


def test_apps_category_union_injection_blocked(client):
    cols = len(client.server_module.db.conn.execute("PRAGMA table_info(apps)").fetchall())
    union = "' UNION SELECT " + ",".join(["NULL", "sql"] + ["NULL"] * (cols - 2)) + " FROM sqlite_master WHERE type='table'--"
    r = client.get(f"{BASE}/apps", params={"category": union})
    assert r.status_code == 200
    assert r.json() == []  # no app has this literal category string, and no injected rows


def test_apps_type_union_injection_blocked(client):
    cols = len(client.server_module.db.conn.execute("PRAGMA table_info(apps)").fetchall())
    union = "' UNION SELECT " + ",".join(["NULL", "sql"] + ["NULL"] * (cols - 2)) + " FROM sqlite_master WHERE type='table'--"
    r = client.get(f"{BASE}/apps", params={"type": union})
    assert r.status_code == 200
    assert r.json() == []


def test_app_slug_or_true_injection_blocked(client):
    r = client.get(f"{BASE}/apps/x' OR '1'='1")
    assert r.status_code == 404


def test_articles_category_union_injection_blocked(client):
    cols = len(client.server_module.db.conn.execute("PRAGMA table_info(articles)").fetchall())
    union = "' UNION SELECT " + ",".join(["NULL", "sql"] + ["NULL"] * (cols - 2)) + " FROM sqlite_master WHERE type='table'--"
    r = client.get(f"{BASE}/articles", params={"category": union})
    assert r.status_code == 200
    assert r.json() == []


def test_article_slug_or_true_injection_blocked(client):
    r = client.get(f"{BASE}/articles/x' OR '1'='1")
    assert r.status_code == 404


def test_normal_filters_still_work(client):
    """A real category value must still return its apps."""
    cur = client.server_module.db.conn
    cur.execute(
        "INSERT INTO apps (name, slug, category) VALUES ('Demo App', 'demo-app', 'demo-category')"
    )
    cur.commit()

    r = client.get(f"{BASE}/apps", params={"category": "demo-category"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["slug"] == "demo-app"


def test_admin_create_app_rejects_unknown_column(client, admin_token):
    r = client.post(
        f"{BASE}/admin/apps",
        json={"name": "x", "slug) VALUES ('x'); DROP TABLE apps; --": "x"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Rejected before any SQL runs, so the malicious key is never executed
    assert r.status_code == 400
    tables = client.server_module.db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    assert any(row[0] == "apps" for row in tables)


def test_admin_update_app_rejects_unknown_column(client, admin_token):
    r = client.post(
        f"{BASE}/admin/apps",
        json={"name": "victim", "slug": "victim-app"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    app_id = r.json()["id"]

    r = client.put(
        f"{BASE}/admin/apps/{app_id}",
        json={"not_a_real_column": "evil"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] != "not_a_real_column"


def test_admin_create_app_error_detail_is_generic(client, admin_token):
    """Forcing a real DB error (duplicate unique slug) must not leak str(e)."""
    client.post(
        f"{BASE}/admin/apps",
        json={"name": "dup", "slug": "dup-app"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    r = client.post(
        f"{BASE}/admin/apps",
        json={"name": "dup2", "slug": "dup-app"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert "UNIQUE constraint" not in detail
    assert "sqlite3" not in detail.lower()
