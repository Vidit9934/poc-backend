import pytest
from fastapi.testclient import TestClient


FAKE_TOOL_CALLS = [
    {"tool": "classify_ticket", "input": {"category": "billing"}},
    {"tool": "score_sentiment", "input": {"score": 3, "evidence": "Polite tone"}},
    {
        "tool": "draft_response",
        "input": {
            "reply_md": "Hi Alice, we're looking into this.",
            "tone": "professional_warm",
            "sop_ids": ["sop-refund-001"],
        },
    },
]

FAKE_DRAFT = FAKE_TOOL_CALLS[-1]["input"]

FAKE_SOPS = [
    {"id": "sop-refund-001", "title": "Duplicate charge refund SOP", "text": "...", "embedding": None},
]


@pytest.fixture(autouse=True)
def patch_network(monkeypatch):
    monkeypatch.setattr("app.retrieval.load_sops", lambda *a, **kw: None)
    monkeypatch.setattr("app.main.top_k", lambda *a, **kw: FAKE_SOPS)
    monkeypatch.setattr(
        "app.main.run_loop",
        lambda *a, **kw: (FAKE_TOOL_CALLS, FAKE_DRAFT),
    )


@pytest.fixture()
def client():
    from app.main import app
    return TestClient(app)


def test_triage_valid_payload(client):
    payload = {
        "ticket_id": "T-001",
        "customer_email": "a@b.com",
        "subject": "Duplicate charge",
        "body": "Charged twice",
    }
    r = client.post("/triage", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["ticket_id"] == "T-001"
    assert body["classification"] == "billing"
    assert body["sentiment_score"] == 3
    assert body["final_draft"] == "Hi Alice, we're looking into this."
    assert body["sop_chunks_used"] == [{"id": "sop-refund-001", "title": "Duplicate charge refund SOP"}]
    assert [tc["tool"] for tc in body["tool_calls"]] == [
        "classify_ticket", "score_sentiment", "draft_response"
    ]
    assert body["error"] is None


def test_triage_invalid_payload(client):
    r = client.post("/triage", json={"ticket_id": "T-001"})
    assert r.status_code == 422


def test_triage_invalid_email(client):
    payload = {"ticket_id": "T-002", "customer_email": "not-an-email", "subject": "hi", "body": "ok"}
    r = client.post("/triage", json=payload)
    assert r.status_code == 422


def test_triage_loop_error_returns_200_with_error_field(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.run_loop",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("Connection failed")),
    )
    payload = {"ticket_id": "T-ERR", "customer_email": "a@b.com", "subject": "hi", "body": "ok"}
    r = client.post("/triage", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["error"] is not None
    assert "Connection failed" in body["error"]
