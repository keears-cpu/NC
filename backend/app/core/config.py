from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/AKfycbzG8g6-l-y8uf9OZ3zxlK74MgrrtLOWsHkI2R6ugGHpbGJTEdGMbYT5XHZjhswiXWjG/exec"
)


@dataclass(frozen=True)
class AppSettings:
    google_apps_script_url: str | None
    google_apps_script_timeout_seconds: float
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
        portone_store_id=os.getenv("PORTONE_STORE_ID"),
        portone_channel_key=os.getenv("PORTONE_CHANNEL_KEY"),
        portone_api_secret=os.getenv("PORTONE_API_SECRET"),
        portone_webhook_secret=os.getenv("PORTONE_WEBHOOK_SECRET"),
        payment_client_base_url=os.getenv("PAYMENT_CLIENT_BASE_URL"),
        payment_redirect_path=os.getenv("PAYMENT_REDIRECT_PATH", "/payment/redirect"),
        payment_webhook_url=os.getenv("PAYMENT_WEBHOOK_URL"),
    )
