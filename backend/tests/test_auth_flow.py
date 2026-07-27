"""Integration tests for email/password register, login, logout, and refresh."""

from app.auth.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
LOGOUT_URL = "/api/v1/auth/logout"
REFRESH_URL = "/api/v1/auth/refresh"


def _register(client, email="learner@example.com", password="Sup3rSecure1"):
    return client.post(REGISTER_URL, json={"email": email, "password": password})


# --- Registration -----------------------------------------------------------


def test_register_creates_user_and_sets_auth_cookies(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "learner@example.com"
    assert body["role"] == "student"
    assert body["is_active"] is True
    assert body["is_email_verified"] is False
    assert "id" in body

    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    assert REFRESH_TOKEN_COOKIE_NAME in response.cookies


def test_register_normalizes_email_casing(client):
    response = _register(client, email="Learner@Example.COM")

    assert response.status_code == 201
    assert response.json()["email"] == "learner@example.com"


def test_register_rejects_duplicate_email(client):
    first = _register(client, email="duplicate@example.com")
    assert first.status_code == 201

    second = _register(client, email="duplicate@example.com")
    assert second.status_code == 409
    assert "already exists" in second.json()["error"]


def test_register_rejects_duplicate_email_case_insensitively(client):
    first = _register(client, email="CaseTest@Example.com")
    assert first.status_code == 201

    second = _register(client, email="casetest@example.com")
    assert second.status_code == 409


def test_register_rejects_password_that_is_too_short(client):
    response = _register(client, password="Ab1")

    assert response.status_code == 422
    details = response.json()["details"]
    assert any("at least 8 characters" in error["msg"] for error in details)


def test_register_rejects_password_without_a_number(client):
    response = _register(client, password="NoNumbersHere")

    assert response.status_code == 422
    details = response.json()["details"]
    assert any("at least one number" in error["msg"] for error in details)


def test_register_rejects_password_without_a_letter(client):
    response = _register(client, password="12345678")

    assert response.status_code == 422
    details = response.json()["details"]
    assert any("at least one letter" in error["msg"] for error in details)


def test_register_rejects_malformed_email(client):
    response = client.post(REGISTER_URL, json={"email": "not-an-email", "password": "Sup3rSecure1"})

    assert response.status_code == 422


# --- Login -------------------------------------------------------------------


def test_login_succeeds_with_correct_credentials(client):
    _register(client, email="login@example.com", password="LoginPass1")

    response = client.post(LOGIN_URL, json={"email": "login@example.com", "password": "LoginPass1"})

    assert response.status_code == 200
    assert response.json()["email"] == "login@example.com"
    assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
    assert REFRESH_TOKEN_COOKIE_NAME in response.cookies


def test_login_rejects_wrong_password(client):
    _register(client, email="login2@example.com", password="LoginPass1")

    response = client.post(
        LOGIN_URL, json={"email": "login2@example.com", "password": "WrongPassword1"}
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"


def test_login_rejects_unknown_email(client):
    response = client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "WhoKnows1"})

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"


def test_login_rejects_inactive_account(client):
    from sqlalchemy import text

    from app.core.database import engine

    _register(client, email="inactive@example.com", password="InactivePass1")

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET is_active = false WHERE email = :email"),
            {"email": "inactive@example.com"},
        )

    response = client.post(
        LOGIN_URL, json={"email": "inactive@example.com", "password": "InactivePass1"}
    )

    assert response.status_code == 403
    assert response.json()["error"] == "This account has been deactivated"


# --- Refresh -------------------------------------------------------------------


def test_refresh_issues_a_new_token_pair(client):
    register_response = _register(client, email="refresh@example.com", password="RefreshPass1")
    original_refresh_cookie = register_response.cookies[REFRESH_TOKEN_COOKIE_NAME]

    response = client.post(REFRESH_URL)

    assert response.status_code == 200
    assert response.json()["email"] == "refresh@example.com"
    assert response.cookies[REFRESH_TOKEN_COOKIE_NAME] != original_refresh_cookie


def test_refresh_fails_without_a_cookie(client):
    response = client.post(REFRESH_URL)

    assert response.status_code == 401
    assert response.json()["error"] == "Refresh token is missing"


def test_refresh_fails_when_reusing_an_already_rotated_token(client):
    _register(client, email="rotate@example.com", password="RotatePass1")
    old_refresh_cookie = client.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    first_refresh = client.post(REFRESH_URL)
    assert first_refresh.status_code == 200

    # Manually replay the pre-rotation refresh cookie.
    client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, old_refresh_cookie)
    replayed = client.post(REFRESH_URL)

    assert replayed.status_code == 401


# --- Logout --------------------------------------------------------------------


def test_logout_clears_cookies(client):
    _register(client, email="logout@example.com", password="LogoutPass1")

    response = client.post(LOGOUT_URL)

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    # An expired/removed cookie is sent back with an empty value.
    assert response.cookies.get(ACCESS_TOKEN_COOKIE_NAME) in (None, "")
    assert response.cookies.get(REFRESH_TOKEN_COOKIE_NAME) in (None, "")


def test_logout_revokes_the_refresh_token(client):
    _register(client, email="logout2@example.com", password="LogoutPass1")
    old_refresh_cookie = client.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    client.post(LOGOUT_URL)

    client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, old_refresh_cookie)
    response = client.post(REFRESH_URL)

    assert response.status_code == 401


def test_logout_without_a_session_is_a_no_op(client):
    response = client.post(LOGOUT_URL)

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
