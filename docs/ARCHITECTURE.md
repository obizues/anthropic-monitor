# Architecture

## Overview

Anthropic Monitor is a scheduled service with four distinct concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions Cron                   │
│                    (every 2 hours)                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   scheduler.run_once()                   │
│                                                         │
│  1. Fetch all configured feeds (scraper)                │
│  2. Diff against seen state (detector)                  │
│  3. Enrich new posts with Claude summaries (summarizer) │
│  4. Route to notifiers based on business hours          │
└──────┬──────────────────────┬──────────────────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐     ┌──────────────────┐
│   Slack     │     │   Email          │
│  (always    │     │  (business hrs)  │
│  immediate) │     │  OR → queue      │
└─────────────┘     └────────┬─────────┘
                             │ outside hours
                             ▼
                    ┌────────────────┐
                    │  queue/        │
                    │  pending.json  │
                    └────────┬───────┘
                             │ 9am next business day
                             ▼
                    ┌────────────────┐
                    │  Email Digest  │
                    └────────────────┘
```

## Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| Scraper | `src/monitor/scraper.py` | Fetch HTML, extract post links |
| Detector | `src/monitor/detector.py` | Diff against persisted seen-set |
| Summarizer | `src/monitor/summarizer.py` | Claude API — fetch content, generate summary |
| Business Hours | `src/monitor/business_hours.py` | Determine if current time is within configured window |
| Queue | `src/monitor/queue.py` | Persist posts for next-day digest |
| Health | `src/monitor/health.py` | Heartbeat tracking, dead-man's-switch alerts |
| Scheduler | `src/monitor/scheduler.py` | Orchestrates all of the above |
| Email Notifier | `src/notifiers/email.py` | SMTP delivery, HTML templates, unsubscribe links |
| Slack Notifier | `src/notifiers/slack.py` | Block Kit formatted webhook posts |
| Webhook Notifier | `src/notifiers/webhook.py` | Generic HTTP POST for any destination |
| Subscriber Store | `src/subscribers/store.py` | SQLite-backed subscriber CRUD |
| Token Manager | `src/subscribers/tokens.py` | Signed JWT unsubscribe tokens |
| Config Screen | `src/api/` | FastAPI dashboard for settings and subscriber management |

## Data Flow

```
Feed URL
  → httpx GET
  → BeautifulSoup parse
  → Post objects
  → diff vs state/seen_posts.json
  → new Posts only
  → httpx GET (post content)
  → Claude API (summarize)
  → enriched Posts
  → business_hours check
     ├── in hours  → notify immediately
     └── out hours → append to queue/pending.json
                     → drain at 9am → digest
```

## State Files

| File | Purpose | Reset safe? |
|---|---|---|
| `state/seen_posts.json` | URLs already notified — prevents duplicates | No — clears history, causes re-notification |
| `state/health.json` | Last successful run timestamp | Yes — just loses heartbeat history |
| `state/subscribers.db` | SQLite subscriber list | No — loss of subscribers |
| `queue/pending.json` | Posts queued for next digest | Yes — those posts won't be digested |

## Extending

### Add a new feed
Edit `monitor.config.json` → add to `feeds[]`. No code changes required.

### Add a new notifier
1. Implement `BaseNotifier` in `src/notifiers/`
2. Add to `scheduler.py` alongside existing notifiers
3. Add channel name to `notifications.channels` in config

### Migrate to Cowork
The `scheduler.run_once()` function is the entry point. Wrapping it as a Cowork skill requires:
1. A Cowork-compatible trigger definition pointing at `run_once()`
2. Injecting secrets via Cowork's secret management instead of `.env`
3. Using Cowork's scheduling instead of GitHub Actions cron
