from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_GOOGLE_APPS_SCRIPT_URL = (
    "https://script.google.com/macros/s/AKfycbzYFr7_0T5p7AZv-SsKTdWQ7qOuh4rxbmdJrwos1mqzUTxSMvUPoiowq1F1sqMtnpd2/exec"
)


@dataclass(frozen=True)
class AppSettings:
    google_apps_script_url: str | None
    google_apps_script_timeout_seconds: float


def get_settings() -> AppSettings:
    timeout_raw = os.getenv("GOOGLE_APPS_SCRIPT_TIMEOUT_SECONDS", "8.0")
    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 8.0
    return AppSettings(
        google_apps_script_url=os.getenv("GOOGLE_APPS_SCRIPT_URL", DEFAULT_GOOGLE_APPS_SCRIPT_URL),
        google_apps_script_timeout_seconds=timeout,
    )
