"""Bot buyruqlari: /start (referal bilan), /test, /natija, /til, /yordam va inline tugmalar."""

import logging

import aiohttp
from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message, User

from . import keyboards
from .backend import Backend, UrlResolver
from .texts import LANGS, display_name, lang_of, results_text, stages_text, t

logger = logging.getLogger(__name__)


def build_router(backend: Backend, urls: UrlResolver) -> Router:
    router = Router()

    async def register(user: User, start_param: str = "") -> tuple[str, dict | None]:
        """Foydalanuvchini backendga yozadi va (til, bosqichlar holati) qaytaradi. Backend ishlamasa – (Telegram tili, None)."""
        try:
            data = await backend.register(user, start_param)
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("Foydalanuvchini yozib bo‘lmadi: %s", exc)
            return lang_of(user.language_code), None
        return lang_of(user.language_code, data.get("language")), data

    async def send_menu(message: Message, user: User, start_param: str = ""):
        lang, progress = await register(user, start_param)
        stages = (progress or {}).get("stages") or []
        text = t(lang, "welcome", name=display_name(user), count=len(stages) or 3, stages=stages_text(lang, progress or {}))
        if progress and progress.get("subscription_required") and not progress.get("subscribed"):
            text += "\n\n" + t(lang, "channels_text")
        base = await urls.get()
        if not base:
            text += "\n\n" + t(lang, "no_webapp")
        await message.answer(text, reply_markup=keyboards.main_menu(base, lang, progress))

    async def send_results(message: Message, user: User):
        lang, _ = await register(user)
        try:
            data = await backend.results(user.id)
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("Natijalarni olib bo‘lmadi: %s", exc)
            await message.answer(t(lang, "backend_error"))
            return
        if not data["attempts"]:
            await message.answer(t(lang, "no_results"), reply_markup=keyboards.start_only(await urls.get(), lang))
            return
        await message.answer(
            results_text(lang, data), reply_markup=keyboards.results_menu(await urls.get(), lang, data["attempts"])
        )

    async def send_help(message: Message, user: User):
        lang, _ = await register(user)
        await message.answer(t(lang, "help"), reply_markup=keyboards.start_only(await urls.get(), lang))

    async def send_invite(message: Message, user: User):
        lang, progress = await register(user)
        if not progress or not progress.get("referral_link"):
            await message.answer(t(lang, "backend_error"))
            return
        pending = progress.get("pending_friends") or 0
        text = t(
            lang,
            "invite_text",
            friends=progress.get("friends", 0),
            pending=t(lang, "invite_pending", n=pending) if pending else "",
            link=progress["referral_link"],
        )
        await message.answer(text, reply_markup=keyboards.invite_menu(lang, progress["referral_link"]))

    @router.message(CommandStart())
    async def on_start(message: Message, command: CommandObject):
        await send_menu(message, message.from_user, command.args or "")

    @router.message(Command("test"))
    async def on_test(message: Message):
        await send_menu(message, message.from_user)

    @router.message(Command("natija", "result", "results"))
    async def on_results(message: Message):
        await send_results(message, message.from_user)

    @router.message(Command("yordam", "help"))
    async def on_help(message: Message):
        await send_help(message, message.from_user)

    @router.message(Command("til", "lang", "language", "yazyk"))
    async def on_lang(message: Message):
        await message.answer(t("uz", "choose_language"), reply_markup=keyboards.language_menu())

    @router.callback_query(F.data == "results")
    async def cb_results(callback: CallbackQuery):
        await callback.answer()
        await send_results(callback.message, callback.from_user)

    @router.callback_query(F.data == "help")
    async def cb_help(callback: CallbackQuery):
        await callback.answer()
        await send_help(callback.message, callback.from_user)

    @router.callback_query(F.data == "invite")
    async def cb_invite(callback: CallbackQuery):
        await callback.answer()
        await send_invite(callback.message, callback.from_user)

    @router.callback_query(F.data == "check")
    async def cb_check(callback: CallbackQuery):
        lang, progress = await register(callback.from_user)
        if progress and progress.get("subscription_required") and not progress.get("subscribed"):
            await callback.answer(t(lang, "not_subscribed"), show_alert=True)
            return
        await callback.answer()
        await send_menu(callback.message, callback.from_user)

    @router.callback_query(F.data == "lang")
    async def cb_lang(callback: CallbackQuery):
        await callback.answer()
        await callback.message.answer(t("uz", "choose_language"), reply_markup=keyboards.language_menu())

    @router.callback_query(F.data.startswith("setlang:"))
    async def cb_setlang(callback: CallbackQuery):
        code = callback.data.split(":", 1)[1]
        if code not in LANGS:
            await callback.answer()
            return
        try:
            await backend.register(callback.from_user)
            await backend.set_language(callback.from_user.id, code)
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning("Tilni saqlab bo‘lmadi: %s", exc)
            await callback.answer(t(code, "backend_error"), show_alert=True)
            return
        await callback.answer(t(code, "language_set"))
        await send_menu(callback.message, callback.from_user)

    @router.message()
    async def on_other(message: Message):
        user = message.from_user
        lang = lang_of(user.language_code if user else None)
        await message.answer(t(lang, "unknown"), reply_markup=keyboards.main_menu(await urls.get(), lang))

    return router
