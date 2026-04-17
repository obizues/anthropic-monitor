from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeedConfig(BaseModel):
    name: str
    url: HttpUrl
    enabled: bool = True


class BusinessHoursConfig(BaseModel):
    enabled: bool = True
    start: str = "09:00"
    end: str = "17:00"
    timezone: str = "America/New_York"
    weekdays_only: bool = True


class ScheduleConfig(BaseModel):
    check_interval_hours: int = Field(2, ge=1, le=24)
    business_hours: BusinessHoursConfig = BusinessHoursConfig()


class SlackNotificationConfig(BaseModel):
    enabled: bool = True
    post_outside_business_hours: bool = True


class EmailNotificationConfig(BaseModel):
    enabled: bool = True
    post_outside_business_hours: bool = False
    digest_on_next_business_day: bool = True


class NotificationConfig(BaseModel):
    channels: list[str] = ["email"]
    slack: SlackNotificationConfig = SlackNotificationConfig()
    email: EmailNotificationConfig = EmailNotificationConfig()


class SummaryConfig(BaseModel):
    enabled: bool = True
    model: str = "claude-opus-4-7"
    max_sentences: int = Field(3, ge=1, le=10)


class HealthConfig(BaseModel):
    max_silence_hours: int = Field(6, ge=1)
    admin_alert_on_failure: bool = True


class AppConfig(BaseModel):
    feeds: list[FeedConfig] = []
    schedule: ScheduleConfig = ScheduleConfig()
    notifications: NotificationConfig = NotificationConfig()
    summaries: SummaryConfig = SummaryConfig()
    health: HealthConfig = HealthConfig()


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    resend_api_key: str
    resend_from_address: str = "Anthropic Monitor <onboarding@resend.dev>"
    slack_webhook_url: str = ""
    unsubscribe_secret: str
    config_api_key: str
    admin_email: str = ""
