from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from api.routes import subscribers, settings, health
from api.middleware import verify_api_key

app = FastAPI(title="Anthropic Monitor", version="0.1.0", docs_url="/docs")
app.middleware("http")(verify_api_key)

app.include_router(subscribers.router, prefix="/subscribers", tags=["Subscribers"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(health.router, tags=["Health"])


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request) -> HTMLResponse:
    from monitor.health import get_last_run
    from subscribers.store import list_subscribers
    from config.loader import get_config

    subs = await list_subscribers()
    cfg = get_config()
    last_run = get_last_run()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Anthropic Monitor</title>
    <style>
      body {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; color: #222; padding: 0 20px; }}
      h1 {{ color: #c7522a; }} table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #eee; }}
      .badge {{ background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
      .badge.warn {{ background: #fff3e0; color: #e65100; }}
      a {{ color: #c7522a; }}
    </style>
    </head>
    <body>
      <h1>Anthropic Monitor</h1>
      <p>Last run: <strong>{last_run.strftime('%Y-%m-%d %H:%M UTC') if last_run else 'Never'}</strong></p>
      <p>Feeds monitored: <strong>{len([f for f in cfg.feeds if f.enabled])}</strong></p>
      <p>Subscribers: <strong>{len(subs)}</strong></p>
      <h2>Quick Links</h2>
      <ul>
        <li><a href="/subscribers">Manage Subscribers</a></li>
        <li><a href="/settings">Edit Settings</a></li>
        <li><a href="/health">Health Status (JSON)</a></li>
        <li><a href="/docs">API Docs</a></li>
      </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
