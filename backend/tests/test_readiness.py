from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_readiness_reports_database_and_redis_connected():
    """
    Readiness check should confirm both PostgreSQL and Redis are
    actually reachable.

    NOTE: This test requires Postgres and Redis to be running
    (e.g. via `docker compose up -d`) since it performs real
    connections, not mocks. If either service is down, this test
    is expected to fail — that's the point: it proves connectivity,
    not just that the code compiles.
    """
    response = client.get("/health/ready")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["redis"] == "connected"
