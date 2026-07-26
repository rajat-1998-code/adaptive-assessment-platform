from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_status_endpoint_returns_configuration():
    response = client.get("/api/v1/auth")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "token_type": "jwt",
        "access_token_expire_minutes": 15,
        "refresh_token_expire_days": 7,
    }


def test_docs_load_and_expose_authentication_route():
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200

    schema = openapi_response.json()
    assert "/api/v1/auth" in schema["paths"]
    assert schema["paths"]["/api/v1/auth"]["get"]["tags"] == ["Authentication"]
