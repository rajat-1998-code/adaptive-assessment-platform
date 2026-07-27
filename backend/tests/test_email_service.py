from app.services.email.service import EmailMessagePayload, EmailService, EmailTemplateRenderer


class InMemoryEmailTransport:
    """Test transport that records payloads instead of sending them."""

    def __init__(self):
        self.messages: list[EmailMessagePayload] = []

    def send(self, payload: EmailMessagePayload) -> None:
        self.messages.append(payload)


def test_welcome_template_renders_html_content():
    renderer = EmailTemplateRenderer()
    html = renderer.render(
        "welcome.html",
        {
            "app_name": "Adaptive Assessment Platform",
            "headline": "Welcome",
            "preheader": "Start learning smarter.",
            "recipient_name": "Rajat",
            "support_email": "noreply@localhost",
            "mailhog_ui_url": "http://localhost:8025",
            "frontend_base_url": "http://localhost:3000",
            "app_environment": "development",
            "dashboard_url": "http://localhost:3000",
        },
    )

    assert "Adaptive Assessment Platform" in html
    assert "Open your dashboard" in html
    assert "http://localhost:8025" in html


def test_mailhog_link_hidden_outside_development():
    renderer = EmailTemplateRenderer()
    html = renderer.render(
        "welcome.html",
        {
            "app_name": "Adaptive Assessment Platform",
            "headline": "Welcome",
            "preheader": "Start learning smarter.",
            "recipient_name": "Rajat",
            "support_email": "noreply@localhost",
            "mailhog_ui_url": "http://localhost:8025",
            "frontend_base_url": "http://localhost:3000",
            "app_environment": "production",
            "dashboard_url": "http://localhost:3000",
        },
    )

    assert "http://localhost:8025" not in html


def test_otp_template_renders_code_and_expiry():
    renderer = EmailTemplateRenderer()
    html = renderer.render(
        "otp.html",
        {
            "app_name": "Adaptive Assessment Platform",
            "headline": "Verify",
            "preheader": "Use the code below.",
            "recipient_name": "Rajat",
            "support_email": "noreply@localhost",
            "mailhog_ui_url": "http://localhost:8025",
            "frontend_base_url": "http://localhost:3000",
            "app_environment": "development",
            "otp_code": "123456",
            "otp_expiry_minutes": 10,
        },
    )

    assert "123456" in html
    assert "10 minutes" in html


def test_magic_link_template_renders_sign_in_url():
    renderer = EmailTemplateRenderer()
    html = renderer.render(
        "magic_link.html",
        {
            "app_name": "Adaptive Assessment Platform",
            "headline": "Magic Link",
            "preheader": "Use the secure link below.",
            "recipient_name": "Rajat",
            "support_email": "noreply@localhost",
            "mailhog_ui_url": "http://localhost:8025",
            "frontend_base_url": "http://localhost:3000",
            "app_environment": "development",
            "magic_link_url": "http://localhost:3000/auth/magic-link?token=test",
            "magic_link_expiry_minutes": 15,
        },
    )

    assert "http://localhost:3000/auth/magic-link?token=test" in html
    assert "15 minutes" in html


def test_email_service_builds_and_sends_welcome_email():
    transport = InMemoryEmailTransport()
    service = EmailService(transport=transport)

    service.send_welcome_email(to_address="learner@example.com", recipient_name="Rajat")

    assert len(transport.messages) == 1
    message = transport.messages[0]
    assert message.to_address == "learner@example.com"
    assert message.subject == "Welcome to Adaptive Assessment Platform"
    assert "Open your dashboard" in message.html_body
    assert "Visit your dashboard" in message.text_body


def test_email_service_builds_and_sends_otp_and_magic_link_emails():
    transport = InMemoryEmailTransport()
    service = EmailService(transport=transport)

    service.send_otp_email(
        to_address="learner@example.com",
        recipient_name="Rajat",
        otp_code="654321",
    )
    service.send_magic_link_email(
        to_address="learner@example.com",
        recipient_name="Rajat",
        magic_link_url="http://localhost:3000/auth/magic-link?token=abc",
    )

    assert len(transport.messages) == 2
    assert "654321" in transport.messages[0].html_body
    assert "http://localhost:3000/auth/magic-link?token=abc" in transport.messages[1].html_body
