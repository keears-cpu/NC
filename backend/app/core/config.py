from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/AKfycbw823je6-pogsZ7GQkDPyJUNPvAXJZ65xAK795Kfp0inZ5mtVP6RWL7u6kQVkxQ1NjJ/exec"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class AppSettings:
    google_apps_script_url: str | None
    google_apps_script_timeout_seconds: float
    storage_backend: str
    database_url: str | None
    supabase_url: str | None
    supabase_publishable_key: str | None
    supabase_service_role_key: str | None
    supabase_project_ref: str | None
    portone_store_id: str | None
    portone_channel_key: str | None
    portone_api_secret: str | None
    portone_webhook_secret: str | None
    payment_client_base_url: str | None
    payment_redirect_path: str
    payment_webhook_url: str | None


def get_settings() -> AppSettings:
    timeout_raw = os.getenv("GOOGLE_APPS_SCRIPT_TIMEOUT_SECONDS", "8.0")
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 8.0
    return AppSettings(
        google_apps_script_url=os.getenv("GOOGLE_APPS_SCRIPT_URL", DEFAULT_GOOGLE_APPS_SCRIPT_URL),
        google_apps_script_timeout_seconds=timeout,
        storage_backend=os.getenv("STORAGE_BACKEND", "apps_script"),
        database_url=os.getenv("DATABASE_URL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_publishable_key=os.getenv("SUPABASE_PUBLISHABLE_KEY"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_project_ref=os.getenv("SUPABASE_PROJECT_REF"),
        portone_store_id=os.getenv("PORTONE_STORE_ID"),
        portone_channel_key=os.getenv("PORTONE_CHANNEL_KEY"),
        portone_api_secret=os.getenv("PORTONE_API_SECRET"),
        portone_webhook_secret=os.getenv("PORTONE_WEBHOOK_SECRET"),
        payment_client_base_url=os.getenv("PAYMENT_CLIENT_BASE_URL"),
        payment_redirect_path=os.getenv("PAYMENT_REDIRECT_PATH", "/payment/redirect"),
        payment_webhook_url=os.getenv("PAYMENT_WEBHOOK_URL"),
    )
