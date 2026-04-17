from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config.loader import get_secrets

_ALGORITHM = "HS256"
_EXPIRY_DAYS = 365


def generate_unsubscribe_token(email: str) -> str:
    payload = {
        "sub": email.lower().strip(),
        "exp": datetime.now(timezone.utc) + timedelta(days=_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, get_secrets().unsubscribe_secret, algorithm=_ALGORITHM)


def decode_unsubscribe_token(token: str) -> str | None:
    """Return the email address, or None if the token is invalid/expired."""
    try:
        payload = jwt.decode(token, get_secrets().unsubscribe_secret, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
