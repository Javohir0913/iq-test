"""Backend bilan ichki tarmoq orqali aloqa (nginx'siz, to‘g‘ridan-to‘g‘ri backend:8000)."""

import json
import time

import aiohttp

from .config import Config

DEFAULT_META = {"question_count": 35, "duration_minutes": 40}


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
            headers={"X-Bot-Token": self.config.token, "Host": "localhost"},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()


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
