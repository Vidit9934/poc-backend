from fastapi.testclient import TestClient


def test_health(monkeypatch):
    monkeypatch.setattr("app.retrieval.load_sops", lambda *a, **kw: None)
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
