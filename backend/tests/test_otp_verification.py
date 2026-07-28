"""Integration tests for Stage 6: OTP-based email verification."""

import re

from app.auth.constants import OTP_MAX_ATTEMPTS

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
RESEND_URL = "/api/v1/auth/resend-otp"

OTP_PATTERN = re.compile(r"\b(\d{6})\b")


def _register(client, email="otp@example.com", password="OtpPass123"):
    return client.post(REGISTER_URL, json={"email": email, "password": password})


def _latest_otp_code(fake_email_transport) -> str:
    """Pull the OTP straight out of the most recent captured email body."""

    message = fake_email_transport.messages[-1]
    match = OTP_PATTERN.search(message.text_body)
    assert match, f"No OTP found in captured email: {message.text_body!r}"
    return match.group(1)


# --- Registration sends an OTP -----------------------------------------------


def test_register_sends_a_verification_otp(client, fake_email_transport):
    response = _register(client)

    assert response.status_code == 201
    assert len(fake_email_transport.messages) == 1
    message = fake_email_transport.messages[0]
    assert message.to_address == "otp@example.com"
    assert OTP_PATTERN.search(message.text_body)


# --- Verify-email ------------------------------------------------------------


def test_verify_email_with_correct_code_marks_user_verified(client, fake_email_transport):
    _register(client)
    code = _latest_otp_code(fake_email_transport)

    response = client.post(VERIFY_URL, json={"code": code})

    assert response.status_code == 200
    assert response.json()["is_email_verified"] is True


def test_verify_email_requires_authentication():
    from fastapi.testclient import TestClient

    from app.main import app

    unauthenticated_client = TestClient(app)
    response = unauthenticated_client.post(VERIFY_URL, json={"code": "123456"})

    assert response.status_code == 401


def test_verify_email_rejects_wrong_code(client, fake_email_transport):
    _register(client)
    real_code = _latest_otp_code(fake_email_transport)
    wrong_code = "".join("9" if digit != "9" else "8" for digit in real_code)

    response = client.post(VERIFY_URL, json={"code": wrong_code})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid verification code"


def test_verify_email_rejects_non_numeric_code(client):
    _register(client)

    response = client.post(VERIFY_URL, json={"code": "abcdef"})

    assert response.status_code == 422


def test_verify_email_rejects_wrong_length_code(client):
    _register(client)

    response = client.post(VERIFY_URL, json={"code": "123"})

    assert response.status_code == 422


def test_verify_email_fails_when_no_otp_was_ever_issued(client):
    from app.core.redis_client import redis_client

    _register(client)

    # Simulate the OTP's Redis TTL having already expired.
    keys = [k for k in redis_client.keys("auth:otp:*") if "cooldown" not in k]
    if keys:
        redis_client.delete(*keys)

    response = client.post(VERIFY_URL, json={"code": "123456"})

    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()


def test_verify_email_enforces_the_retry_limit(client, fake_email_transport):
    _register(client)
    real_code = _latest_otp_code(fake_email_transport)
    wrong_code = "".join("9" if digit != "9" else "8" for digit in real_code)

    for _ in range(OTP_MAX_ATTEMPTS):
        response = client.post(VERIFY_URL, json={"code": wrong_code})
        assert response.status_code == 400

    locked_out_response = client.post(VERIFY_URL, json={"code": wrong_code})
    assert locked_out_response.status_code == 429

    # Even the correct code is now rejected until a new one is requested.
    still_locked = client.post(VERIFY_URL, json={"code": real_code})
    assert still_locked.status_code == 429


def test_verify_email_rejects_already_verified_account(client, fake_email_transport):
    _register(client)
    code = _latest_otp_code(fake_email_transport)
    client.post(VERIFY_URL, json={"code": code})

    response = client.post(VERIFY_URL, json={"code": code})

    assert response.status_code == 400
    assert "already verified" in response.json()["error"].lower()


# --- Resend-otp ----------------------------------------------------------------


def test_resend_otp_requires_authentication():
    from fastapi.testclient import TestClient

    from app.main import app

    unauthenticated_client = TestClient(app)
    response = unauthenticated_client.post(RESEND_URL)

    assert response.status_code == 401


def test_resend_otp_is_rate_limited_immediately_after_register(client):
    _register(client)

    response = client.post(RESEND_URL)

    assert response.status_code == 429


def test_resend_otp_rejects_already_verified_account(client, fake_email_transport):
    _register(client)
    code = _latest_otp_code(fake_email_transport)
    client.post(VERIFY_URL, json={"code": code})

    response = client.post(RESEND_URL)

    assert response.status_code == 400
    assert "already verified" in response.json()["error"].lower()


def test_resend_otp_issues_a_new_working_code_once_cooldown_is_cleared(
    client, fake_email_transport
):
    _register(client)

    # Bypass the cooldown directly (rather than sleeping in a test) by
    # clearing its Redis key, then confirm resend still produces a valid,
    # verifiable code.
    from app.core.redis_client import redis_client

    cooldown_keys = redis_client.keys("auth:otp:cooldown:*")
    if cooldown_keys:
        redis_client.delete(*cooldown_keys)

    response = client.post(RESEND_URL)
    assert response.status_code == 200
    assert len(fake_email_transport.messages) == 2

    new_code = _latest_otp_code(fake_email_transport)
    verify_response = client.post(VERIFY_URL, json={"code": new_code})
    assert verify_response.status_code == 200
    assert verify_response.json()["is_email_verified"] is True
