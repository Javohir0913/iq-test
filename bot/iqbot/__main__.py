"""Bot ishga tushirish: python -m iqbot

Token bo‘lmasa bot xato bermaydi – kutish rejimida turadi (konteyner qayta-qayta o‘chib yonmasligi uchun).
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonCommands, MenuButtonWebApp, WebAppInfo

from .backend import Backend, UrlResolver
from .config import load_config
from .handlers import build_router
from .texts import t

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("iqbot")


async def setup_profile(bot: Bot, backend: Backend):
    """Buyruqlar va tavsiflar – uz standart, ru alohida."""
    meta = await backend.meta()
    fmt = {"count": meta["question_count"], "minutes": meta["duration_minutes"]}
    for lang, code in (("uz", None), ("ru", "ru")):
        names = ("start", "test", "natija", "yordam")
        commands = [BotCommand(command=name, description=t(lang, f"commands.{name}")) for name in names]
        await bot.set_my_commands(commands, language_code=code)
        await bot.set_my_short_description(t(lang, "short_description", **fmt), language_code=code)
        await bot.set_my_description(t(lang, "description", **fmt), language_code=code)


async def keep_menu_button(bot: Bot, urls: UrlResolver):
    """Menyu tugmasini Mini App manziliga moslab turadi (tunnel manzili o‘zgarsa ham)."""
    current = None
    while True:
        try:
            base = await urls.get()
            if base != current:
                if base:
                    button = MenuButtonWebApp(text=t("uz", "menu_button"), web_app=WebAppInfo(url=f"{base}/start"))
                    await bot.set_chat_menu_button(menu_button=button)
                    logger.info("Mini App manzili: %s", base)
                else:
                    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
                    logger.warning("HTTPS manzil yo‘q (PUBLIC_URL yoki tunnel) – Mini App tugmalari o‘chirilgan.")
                current = base
        except Exception as exc:
            logger.warning("Menyu tugmasini yangilab bo‘lmadi: %s", exc)
        await asyncio.sleep(60)


async def main():
    config = load_config()
    if not config.token:
        logger.warning("TELEGRAM_BOT_TOKEN berilmagan – bot kutish rejimida. Tokenni .env ga yozib, qayta ishga tushiring.")
        await asyncio.Event().wait()
        return

    bot = Bot(config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
    backend = Backend(config)
    urls = UrlResolver(config, backend)
    dp = Dispatcher()
    dp.include_router(build_router(backend, urls))

    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s", me.username)
    try:
        await setup_profile(bot, backend)
    except Exception as exc:  # profil sozlanmasa ham bot ishlayversin
        logger.warning("Bot profilini sozlab bo‘lmadi: %s", exc)
    menu_task = asyncio.create_task(keep_menu_button(bot, urls))

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        menu_task.cancel()
        await backend.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
