from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from config.loader import reload_config
from config.schema import AppConfig

router = APIRouter()
_CONFIG_PATH = Path("monitor.config.json")


@router.get("/", response_class=HTMLResponse)
async def settings_page() -> HTMLResponse:
    config_text = _CONFIG_PATH.read_text() if _CONFIG_PATH.exists() else "{}"
    html = f"""
    <!DOCTYPE html><html><head><title>Settings</title>
    <style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;}}
    textarea{{width:100%;height:400px;font-family:monospace;font-size:13px;}}
    button{{padding:8px 16px;background:#c7522a;color:white;border:none;cursor:pointer;border-radius:4px;}}
    a{{color:#c7522a;}}</style></head>
    <body><h1>Configuration</h1>
    <form method="post">
    <textarea name="config">{config_text}</textarea><br><br>
    <button type="submit">Save</button>
    </form>
    <p><a href="/">← Dashboard</a></p></body></html>
    """
    return HTMLResponse(html)


@router.post("/")
async def save_settings(config: AppConfig) -> dict:
    try:
        _CONFIG_PATH.write_text(json.dumps(config.model_dump(mode="json"), indent=2))
        reload_config()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(400, f"Invalid config: {e}") from e
