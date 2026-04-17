from __future__ import annotations

import pytest


def test_roundtrip(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "a" * 32)
    monkeypatch.setenv("CONFIG_API_KEY", "test")

    from subscribers.tokens import decode_unsubscribe_token, generate_unsubscribe_token

    token = generate_unsubscribe_token("user@example.com")
    assert decode_unsubscribe_token(token) == "user@example.com"


def test_invalid_token(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "a" * 32)
    monkeypatch.setenv("CONFIG_API_KEY", "test")

    from subscribers.tokens import decode_unsubscribe_token

    assert decode_unsubscribe_token("not-a-real-token") is None


def test_email_normalized(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("UNSUBSCRIBE_SECRET", "a" * 32)
    monkeypatch.setenv("CONFIG_API_KEY", "test")

    from subscribers.tokens import decode_unsubscribe_token, generate_unsubscribe_token

    token = generate_unsubscribe_token("USER@Example.COM")
    assert decode_unsubscribe_token(token) == "user@example.com"
