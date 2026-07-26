from app.auth.models import MagicLinkToken, RefreshToken, User, UserSession


def test_auth_models_register_expected_tables():
    assert User.__table__.name == "users"
    assert UserSession.__table__.name == "user_sessions"
    assert RefreshToken.__table__.name == "refresh_tokens"
    assert MagicLinkToken.__table__.name == "magic_link_tokens"


def test_user_relationships_are_wired_to_auth_models():
    assert User.refresh_tokens.property.mapper.class_ is RefreshToken
    assert User.sessions.property.mapper.class_ is UserSession
    assert User.magic_link_tokens.property.mapper.class_ is MagicLinkToken


def test_auth_foreign_keys_target_expected_parent_tables():
    session_user_fk = next(iter(UserSession.__table__.c.user_id.foreign_keys))
    refresh_user_fk = next(iter(RefreshToken.__table__.c.user_id.foreign_keys))
    refresh_session_fk = next(iter(RefreshToken.__table__.c.session_id.foreign_keys))
    magic_link_user_fk = next(iter(MagicLinkToken.__table__.c.user_id.foreign_keys))

    assert session_user_fk.target_fullname == "users.id"
    assert refresh_user_fk.target_fullname == "users.id"
    assert refresh_session_fk.target_fullname == "user_sessions.id"
    assert magic_link_user_fk.target_fullname == "users.id"
