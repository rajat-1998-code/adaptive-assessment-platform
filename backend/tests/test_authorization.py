"""Integration tests for role-based access control and route protection."""

from sqlalchemy import text

from app.auth.constants import ROLE_ADMIN, ROLE_PROFESSIONAL
from app.core.database import engine

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"
AUTHORIZATION_URL = "/api/v1/auth/me/authorization"
STUDENT_PORTAL_URL = "/api/v1/auth/student/portal"
PROFESSIONAL_WORKSPACE_URL = "/api/v1/auth/professional/workspace"
ADMIN_USERS_URL = "/api/v1/auth/admin/users"


def _register(client, email: str, password: str = "Sup3rSecure1") -> dict:
    response = client.post(REGISTER_URL, json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()


def _set_role(email: str, role: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET role = :role WHERE email = :email"),
            {"role": role, "email": email},
        )


def test_me_requires_authentication(client):
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required"


def test_student_can_access_own_profile_and_authorization_summary(client):
    _register(client, email="student@example.com")

    me_response = client.get(ME_URL)
    authz_response = client.get(AUTHORIZATION_URL)

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "student"
    assert authz_response.status_code == 200
    assert authz_response.json() == {
        "role": "student",
        "permissions": ["assessments:take", "profile:read"],
    }


def test_student_only_route_allows_student(client):
    _register(client, email="student-portal@example.com")

    response = client.get(STUDENT_PORTAL_URL)

    assert response.status_code == 200
    assert response.json()["role"] == "student"


def test_student_is_blocked_from_professional_and_admin_routes(client):
    _register(client, email="blocked-student@example.com")

    professional_response = client.get(PROFESSIONAL_WORKSPACE_URL)
    admin_response = client.get(ADMIN_USERS_URL)

    assert professional_response.status_code == 403
    assert admin_response.status_code == 403
    assert (
        professional_response.json()["error"]
        == "You do not have permission to access this resource"
    )
    assert admin_response.json()["error"] == "You do not have permission to access this resource"


def test_professional_role_can_access_professional_workspace(client):
    _register(client, email="professional@example.com")
    _set_role("professional@example.com", ROLE_PROFESSIONAL)

    response = client.get(PROFESSIONAL_WORKSPACE_URL)

    assert response.status_code == 200
    assert response.json()["role"] == ROLE_PROFESSIONAL


def test_professional_role_is_blocked_from_admin_and_student_only_routes(client):
    _register(client, email="professional-blocked@example.com")
    _set_role("professional-blocked@example.com", ROLE_PROFESSIONAL)

    student_response = client.get(STUDENT_PORTAL_URL)
    admin_response = client.get(ADMIN_USERS_URL)

    assert student_response.status_code == 403
    assert admin_response.status_code == 403


def test_admin_can_access_admin_and_professional_routes(client):
    _register(client, email="admin@example.com")
    member = _register(client, email="member@example.com")
    _set_role("admin@example.com", ROLE_ADMIN)

    # Registering the member user above signs that user in, replacing the
    # admin session cookie on the shared test client. Log back in as the
    # (now promoted) admin before exercising the admin-only routes.
    login_response = client.post(
        LOGIN_URL, json={"email": "admin@example.com", "password": "Sup3rSecure1"}
    )
    assert login_response.status_code == 200

    admin_response = client.get(ADMIN_USERS_URL)
    role_update_response = client.patch(
        f"{ADMIN_USERS_URL}/{member['id']}/role",
        json={"role": ROLE_PROFESSIONAL},
    )
    professional_response = client.get(PROFESSIONAL_WORKSPACE_URL)

    assert admin_response.status_code == 200
    assert {entry["email"] for entry in admin_response.json()} == {
        "admin@example.com",
        "member@example.com",
    }
    assert role_update_response.status_code == 200
    assert role_update_response.json()["role"] == ROLE_PROFESSIONAL
    assert professional_response.status_code == 200
    assert professional_response.json()["role"] == ROLE_ADMIN


def test_admin_is_blocked_from_student_only_route(client):
    _register(client, email="strict-admin@example.com")
    _set_role("strict-admin@example.com", ROLE_ADMIN)

    response = client.get(STUDENT_PORTAL_URL)

    assert response.status_code == 403
