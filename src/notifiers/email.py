from __future__ import annotations

import resend
import structlog
from jinja2 import Environment, BaseLoader

from config.loader import get_secrets
from monitor.models import Post
from notifiers.base import BaseNotifier
from subscribers.store import list_subscribers
from subscribers.tokens import generate_unsubscribe_token

log = structlog.get_logger()

_POST_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: auto; color: #222;">
  <h2 style="color: #c7522a;">New from Anthropic</h2>
  {% for post in posts %}
  <div style="border-left: 4px solid #c7522a; padding: 12px 16px; margin-bottom: 24px;">
    <h3 style="margin: 0 0 6px;"><a href="{{ post.url }}" style="color: #1a0dab;">{{ post.title }}</a></h3>
    <p style="font-size: 12px; color: #888; margin: 0 0 8px;">{{ post.source_name }}</p>
    {% if post.summary %}
    <p style="margin: 0;">{{ post.summary }}</p>
    {% endif %}
  </div>
  {% endfor %}
  <hr style="border: none; border-top: 1px solid #eee;">
  <p style="font-size: 11px; color: #aaa;">
    You're receiving this because you subscribed to Anthropic Monitor alerts.<br>
    <a href="{{ unsubscribe_base_url }}?token={{ unsubscribe_token }}">Unsubscribe</a>
  </p>
</body>
</html>
"""

_DIGEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: auto; color: #222;">
  <h2 style="color: #c7522a;">{{ label }} — Anthropic Digest</h2>
  <p style="color: #555;">Here's what you missed outside business hours:</p>
  {% for post in posts %}
  <div style="border-left: 4px solid #c7522a; padding: 12px 16px; margin-bottom: 24px;">
    <h3 style="margin: 0 0 6px;"><a href="{{ post.url }}" style="color: #1a0dab;">{{ post.title }}</a></h3>
    <p style="font-size: 12px; color: #888; margin: 0 0 8px;">{{ post.source_name }}</p>
    {% if post.summary %}
    <p style="margin: 0;">{{ post.summary }}</p>
    {% endif %}
  </div>
  {% endfor %}
  <hr style="border: none; border-top: 1px solid #eee;">
  <p style="font-size: 11px; color: #aaa;">
    <a href="{{ unsubscribe_base_url }}?token={{ unsubscribe_token }}">Unsubscribe</a>
  </p>
</body>
</html>
"""

_env = Environment(loader=BaseLoader())


class EmailNotifier(BaseNotifier):
    def __init__(self, unsubscribe_base_url: str = "http://localhost:8000/unsubscribe") -> None:
        self._unsubscribe_base_url = unsubscribe_base_url

    async def send(self, posts: list[Post]) -> None:
        subscribers = await list_subscribers()
        if not subscribers:
            log.info("email_skipped_no_subscribers")
            return
        for sub in subscribers:
            await self._send_to(sub["email"], posts, template=_POST_TEMPLATE, subject=self._subject(posts))

    async def send_digest(self, posts: list[Post], label: str = "Weekend Roundup") -> None:
        subscribers = await list_subscribers()
        if not subscribers:
            return
        for sub in subscribers:
            await self._send_to(
                sub["email"], posts, template=_DIGEST_TEMPLATE,
                subject=f"{label} — Anthropic Monitor Digest", label=label,
            )

    async def _send_to(
        self, email: str, posts: list[Post], template: str, subject: str, label: str = ""
    ) -> None:
        secrets = get_secrets()
        resend.api_key = secrets.resend_api_key

        token = generate_unsubscribe_token(email)
        html = _env.from_string(template).render(
            posts=posts,
            unsubscribe_base_url=self._unsubscribe_base_url,
            unsubscribe_token=token,
            label=label,
        )

        try:
            resend.Emails.send({
                "from": secrets.resend_from_address,
                "to": [email],
                "subject": subject,
                "html": html,
            })
            log.info("email_sent", recipient=email, subject=subject)
        except Exception:
            log.error("email_failed", recipient=email)

    @staticmethod
    def _subject(posts: list[Post]) -> str:
        if len(posts) == 1:
            return f"New: {posts[0].title}"
        return f"{len(posts)} new posts from Anthropic"
