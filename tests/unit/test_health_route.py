from __future__ import annotations

import pytest

from api.routes import health as health_route


@pytest.mark.asyncio
async def test_health_reports_nano_banaa_plugin_available(tmp_path, monkeypatch):
    plugin_zip = tmp_path / "anthropic-monitor-skill.zip"
    plugin_zip.write_text("zip")
    monkeypatch.setenv("NANO_BANAA_PLUGIN_PATH", str(plugin_zip))

    payload = await health_route.health()

    assert payload["nano_banaa_plugin"]["status"] == "available"


@pytest.mark.asyncio
async def test_health_reports_nano_banaa_plugin_missing(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "NANO_BANAA_PLUGIN_PATH", str(tmp_path / "missing-anthropic-monitor-skill.zip")
    )

    payload = await health_route.health()

    assert payload["nano_banaa_plugin"]["status"] == "missing"
