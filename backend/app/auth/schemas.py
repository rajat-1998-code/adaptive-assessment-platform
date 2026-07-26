"""Schemas used by the authentication module."""

from pydantic import BaseModel, ConfigDict


class AuthStatusResponse(BaseModel):
    """Simple response used to verify the auth module is wired correctly."""

    enabled: bool
    token_type: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    model_config = ConfigDict(from_attributes=True)
