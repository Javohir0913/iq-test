"""Bot buyruqlari: /start, /test, /natija, /yordam va inline tugmalar."""

import logging

import aiohttp
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, User

from . import keyboards
from .backend import Backend, UrlResolver
from .texts import display_name, lang_of, results_text, t

logger = logging.getLogger(__name__)


def build_router(backend: Backend, urls: UrlResolver) -> Router:
    router = Router()

    async def send_menu(message: Message, user: User):
        lang = lang_of(user.language_code)
        meta = await backend.meta()
        text = t(
            lang,
            "welcome",
            name=display_name(user),
            count=meta["question_count"],
            minutes=meta["duration_minutes"],
        )
        base = await urls.get()
        if not base:
            text += "\n\n" + t(lang, "no_webapp")
        await message.answer(text, reply_markup=keyboards.main_menu(base, lang))

    async def send_results(message: Message, user: User):
        lang = lang_of(user.language_code)
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
        lang = lang_of(user.language_code)
        meta = await backend.meta()
        await message.answer(
            t(lang, "help", minutes=meta["duration_minutes"]), reply_markup=keyboards.start_only(await urls.get(), lang)
        )

    @router.message(CommandStart())
    async def on_start(message: Message):
        await send_menu(message, message.from_user)

    @router.message(Command("test"))
    async def on_test(message: Message):
        lang = lang_of(message.from_user.language_code)
        base = await urls.get()
        if not base:
            await message.answer(t(lang, "no_webapp"))
            return
        await message.answer(t(lang, "open_test"), reply_markup=keyboards.start_only(base, lang))

    @router.message(Command("natija", "result", "results"))
    async def on_results(message: Message):
        await send_results(message, message.from_user)

    @router.message(Command("yordam", "help"))
    async def on_help(message: Message):
        await send_help(message, message.from_user)

    @router.callback_query(F.data == "results")
    async def cb_results(callback: CallbackQuery):
        await callback.answer()
        await send_results(callback.message, callback.from_user)

    @router.callback_query(F.data == "help")
    async def cb_help(callback: CallbackQuery):
        await callback.answer()
        await send_help(callback.message, callback.from_user)

    @router.message()
    async def on_other(message: Message):
        lang = lang_of(message.from_user.language_code if message.from_user else None)
        await message.answer(t(lang, "unknown"), reply_markup=keyboards.main_menu(await urls.get(), lang))

    return router
