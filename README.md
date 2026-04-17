# Anthropic Monitor

Enterprise-grade blog monitor that watches Anthropic's news and research pages, generates AI-powered summaries using Claude, and delivers alerts to Slack and email subscribers — with full business-hours awareness.

Yes — this solution includes an Anthropic monitor out of the box via the default feeds in `monitor.config.json` (`/news` and `/research`).

## Quickstart

```bash
# 1. Clone and install
git clone <repo-url> && cd anthropic-monitor
pip install -e ".[dev]"

# 2. Configure secrets
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY, SMTP_*, UNSUBSCRIBE_SECRET, CONFIG_API_KEY

# 3. Configure feeds and schedule
# Edit monitor.config.json — add feeds, adjust schedule, enable channels

# 4. Add yourself as a subscriber
python -c "import asyncio; from subscribers.store import add_subscriber; asyncio.run(add_subscriber('you@company.com', 'Your Name'))"

# 5. Run manually to test
python -m monitor.scheduler

# 6. Start the config screen
uvicorn api.main:app --reload
# Open http://localhost:8000 — use CONFIG_API_KEY as the X-API-Key header
```

## Configuration

### `monitor.config.json` — Non-sensitive settings

| Field | Description |
|---|---|
| `feeds[]` | List of URLs to monitor. Add any blog URL here — not limited to Anthropic. |
| `schedule.check_interval_hours` | How often to check (default: 2) |
| `schedule.business_hours` | Start/end time, timezone, weekdays only |
| `notifications.channels` | `["email"]`, `["slack"]`, or `["email", "slack"]` |
| `notifications.email.digest_on_next_business_day` | Queue overnight/weekend posts for morning digest |
| `summaries.model` | Claude model for generating summaries |

### `.env` — Secrets (never commit this file)

See `.env.example` for all required fields.

## Deployment

### GitHub Actions (recommended)
1. Push to GitHub
2. Add all `.env` values as repository secrets (Settings → Secrets → Actions)
3. The monitor runs every 2 hours automatically; business hours logic is handled in code

### Docker
```bash
docker build -t anthropic-monitor .
docker run -v $(pwd)/state:/app/state -v $(pwd)/queue:/app/queue \
  --env-file .env anthropic-monitor
```

## Adding a New Notification Channel

1. Create `src/notifiers/yourservice.py` implementing `BaseNotifier`
2. Implement `send(posts)` and `send_digest(posts, label)`
3. Add `"yourservice"` to `notifications.channels` in config
4. Wire it into `src/monitor/scheduler.py` alongside the existing notifiers

## Managing Subscribers

Via the config screen at `http://localhost:8000/subscribers`, or via API:

```bash
# Add
curl -X POST http://localhost:8000/subscribers \
  -H "X-API-Key: $CONFIG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com", "name": "User Name"}'

# List
curl http://localhost:8000/subscribers -H "X-API-Key: $CONFIG_API_KEY"

# Remove
curl -X DELETE http://localhost:8000/subscribers/user@company.com \
  -H "X-API-Key: $CONFIG_API_KEY"
```

Every email includes a one-click unsubscribe link. No login required.

## Running Tests

```bash
pytest                    # All tests with coverage
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
ruff check src/ tests/    # Lint
mypy src/                 # Type check
```

## Health Monitoring

- `GET /health` — returns `{"status": "healthy"|"degraded", "last_run": "..."}`
- If no successful run is detected within `health.max_silence_hours`, an alert email is sent to `ADMIN_EMAIL`
- Point an uptime monitor (e.g., UptimeRobot) at `/health` for external alerting

## Cowork Skill

A Cowork skill is included so you can ask Claude to check for new Anthropic posts directly in chat — no GitHub access or API keys required.

### Install

1. Download `cowork-skill/anthropic-monitor-skill.zip` from this repo
2. Open Cowork → Skills → Upload skill → select the ZIP
3. Ask Claude: *"Check for new Anthropic posts"* or *"Run the news monitor"*

### How it works

The skill instructs Claude to fetch `anthropic.com/news` and `anthropic.com/research` directly (public GET requests), extract new post links, and summarize the top results in chat.

This is separate from the GitHub Actions monitor — the cron job handles email delivery to subscribers; the skill gives you an on-demand chat summary.

### Rebuild the skill ZIP

```bash
cd cowork-skill
python3 -c "
import zipfile
with zipfile.ZipFile('anthropic-monitor-skill.zip', 'w') as z:
    z.write('anthropic-monitor/Skill.md', 'Skill.md')
print('Done')
"
```

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md).
