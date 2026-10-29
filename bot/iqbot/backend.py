"""Backend bilan ichki tarmoq orqali aloqa (nginx'siz, to‘g‘ridan-to‘g‘ri backend:8000)."""

import json
import time

import aiohttp
from aiogram.types import User

from .config import Config

DEFAULT_META = {"question_count": 20, "duration_minutes": 25, "stages": []}


class Backend:
    def __init__(self, config: Config):
        self.config = config
        self._session: aiohttp.ClientSession | None = None

    async def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _headers(self) -> dict:
        return {"X-Bot-Token": self.config.token, "Host": "localhost"}

    async def meta(self) -> dict:
        try:
            s = await self.session()
            async with s.get(f"{self.config.backend_url}/api/v1/test/meta", headers={"Host": "localhost"}) as resp:
                if resp.status == 200:
                    return await resp.json()
        except (aiohttp.ClientError, TimeoutError):
            pass
        return DEFAULT_META

    async def results(self, telegram_id: int) -> dict:
        s = await self.session()
        async with s.get(
            f"{self.config.backend_url}/api/v1/bot/results",
            params={"telegram_id": str(telegram_id)},
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def register(self, user: User, start_param: str = "") -> dict:
        """Foydalanuvchini yozadi (birinchi kirishda referal bilan) va bosqichlar holatini qaytaradi."""
        s = await self.session()
        payload = {
            "id": user.id,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.username or "",
            "language_code": user.language_code or "",
            "start_param": start_param[:64],
        }
        async with s.post(
            f"{self.config.backend_url}/api/v1/bot/register", json=payload, headers=self._headers()
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def set_language(self, telegram_id: int, language: str) -> None:
        s = await self.session()
        async with s.post(
            f"{self.config.backend_url}/api/v1/bot/language",
            json={"telegram_id": telegram_id, "language": language},
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()


class UrlResolver:
    """Mini App manzili: PUBLIC_URL (https) yoki Cloudflare quick tunnel manzili (60 s kesh)."""

    def __init__(self, config: Config, backend: Backend):
        self.config = config
        self.backend = backend
        self._cached: tuple[float, str] | None = None

    async def get(self) -> str:
        if self.config.public_url.startswith("https://"):
            return self.config.public_url
        if not self.config.tunnel_metrics_url:
            return ""
        if self._cached and time.monotonic() - self._cached[0] < 60:
            return self._cached[1]
        url = ""
        try:
            s = await self.backend.session()
            timeout = aiohttp.ClientTimeout(total=3)
            async with s.get(f"{self.config.tunnel_metrics_url}/quicktunnel", timeout=timeout) as resp:
                if resp.status == 200:
                    host = json.loads(await resp.text()).get("hostname", "")
                    url = f"https://{host}" if host else ""
        except (aiohttp.ClientError, TimeoutError, ValueError):
            pass
        self._cached = (time.monotonic(), url)
        return url
