from __future__ import annotations

import asyncio
import structlog

from config.loader import get_config
from monitor.business_hours import is_business_hours
from monitor.detector import find_new_posts
from monitor.health import alert_if_unhealthy, record_heartbeat
from monitor.queue import drain, enqueue
from monitor.scraper import fetch_posts
from monitor.summarizer import enrich_with_summary
from notifiers.email import EmailNotifier
from notifiers.slack import SlackNotifier

log = structlog.get_logger()


async def run_once() -> None:
    """Single monitor cycle — fetch, detect, summarize, notify or queue."""
    cfg = get_config()
    all_posts = []

    for feed in cfg.feeds:
        if not feed.enabled:
            continue
        posts = await fetch_posts(str(feed.url), feed.name)
        all_posts.extend(posts)

    new_posts = find_new_posts(all_posts)
    if not new_posts:
        log.info("no_new_posts")
        record_heartbeat()
        return

    # Enrich with Claude summaries
    enriched = [await enrich_with_summary(p) for p in new_posts]

    notif_cfg = cfg.notifications
    in_hours = is_business_hours()

    # Slack: always send immediately (users manage their own DND)
    if "slack" in notif_cfg.channels and notif_cfg.slack.enabled:
        await SlackNotifier().send(enriched)

    # Email: respect business hours
    if "email" in notif_cfg.channels and notif_cfg.email.enabled:
        if in_hours or notif_cfg.email.post_outside_business_hours:
            await EmailNotifier().send(enriched)
        else:
            enqueue(enriched)
            log.info("posts_queued_for_digest", count=len(enriched))

    record_heartbeat()


async def flush_queue() -> None:
    """Called at start of business day to drain queued posts into a digest."""
    queued = drain()
    if not queued:
        return
    cfg = get_config().notifications
    if "email" in cfg.channels and cfg.email.enabled:
        await EmailNotifier().send_digest(queued)
    if "slack" in cfg.channels and cfg.slack.enabled:
        await SlackNotifier().send_digest(queued)


async def health_check() -> None:
    await alert_if_unhealthy()


def main() -> None:
    asyncio.run(run_once())


if __name__ == "__main__":
    main()
