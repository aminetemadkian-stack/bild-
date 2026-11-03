"""End-to-end checks: agent tools through the real HTTP stack (demo provider, no network).

Requires fastapi and httpx (httpx is needed by fastapi.testclient).
The Host header is set to 127.0.0.1 so the local-only guard accepts the requests.
"""
import pytest

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

LOCAL = "http://127.0.0.1:8000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "integration.db"))
    monkeypatch.setattr(settings, "llm_provider", "demo")
    with TestClient(app, base_url=LOCAL) as c:
        yield c


def test_catalog_lists_every_agent_with_tools(client):
    body = client.get("/api/v1/agents/catalog").json()
    ids = {a["id"] for a in body["agents"]}
    assert {"architecture", "cost", "structure"} <= ids
    cost = next(a for a in body["agents"] if a["id"] == "cost")
    assert "quantity_takeoff" in {t["id"] for t in cost["tools"]}


def test_cost_agent_runs_takeoff_tool_in_demo_chat(client):
    response = client.post(
        "/api/v1/chat",
        data={"prompt": "متره دیوار سوله ۲۵×۶۰ متر با ارتفاع ۳ متر", "agent_id": "cost"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] == "cost"
    assert "quantity_takeoff" in body["tools_used"]
    assert "1500" in body["answer"]


def test_chat_without_dimensions_uses_no_tool(client):
    body = client.post(
        "/api/v1/chat", data={"prompt": "برای فروشگاه برنامه فضا بده", "agent_id": "architecture"}
    ).json()
    assert body["tools_used"] == []


def test_dxf_endpoint_returns_dxf_attachment(client):
    response = client.post(
        "/api/v1/concept/dxf",
        json={"name": "QuickService", "type": "commercial", "width": 25, "length": 60, "height": 3},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/dxf")
    assert "attachment" in response.headers["content-disposition"]
    assert response.text.rstrip().endswith("EOF")


def test_drawing_endpoint_returns_schematic_svg(client):
    body = client.post(
        "/api/v1/concept/drawing",
        json={"name": "Test", "type": "commercial", "width": 25, "length": 60, "height": 3},
    ).json()
    assert body["svg"].startswith("<svg")
    assert "NOT FOR PERMIT" in body["svg"]


def test_foreign_host_is_rejected(client):
    response = client.get("/health", headers={"host": "evil.example.com"})
    assert response.status_code == 403


def test_cross_origin_post_is_rejected(client):
    response = client.post(
        "/api/v1/chat",
        data={"prompt": "hi", "agent_id": "auto"},
        headers={"origin": "https://attacker.example"},
    )
    assert response.status_code == 403


def test_local_origin_is_allowed(client):
    response = client.get("/health", headers={"origin": "http://localhost:8000"})
    assert response.status_code == 200
