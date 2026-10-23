"""Bot sozlamalari – faqat muhit o‘zgaruvchilaridan (.env)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    token: str
    public_url: str
    backend_url: str
    tunnel_metrics_url: str = ""


def load_config() -> Config:
    return Config(
        token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        public_url=os.environ.get("PUBLIC_URL", "").strip().rstrip("/"),
        backend_url=os.environ.get("BACKEND_INTERNAL_URL", "http://backend:8000").rstrip("/"),
        tunnel_metrics_url=os.environ.get("TUNNEL_METRICS_URL", "").strip().rstrip("/"),
    )
