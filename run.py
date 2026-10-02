import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем папку bot в путь Python
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from bot.config import BOT_TOKEN, ADMIN_GROUP_ID
from bot.database.db import init_db
from bot.handlers import user, admin_commands, moderation, dialogue

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Прокси (если нужен) - установите в .env: PROXY_URL=http://user:pass@host:port
PROXY_URL = os.getenv("PROXY_URL", None)

async def main():
    # Инициализация БД
    await init_db()
    
    # Создание сессии с прокси (если настроен)
    if PROXY_URL:
        logging.info(f"Using proxy: {PROXY_URL}")
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(
            token=BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    else:
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    
    # Диспетчер
    dp = Dispatcher()
    
    # Регистрация роутеров
    # Важно: dialogue должен быть последним, т.к. ловит все сообщения
    dp.include_router(user.router)
    dp.include_router(admin_commands.router)
    dp.include_router(moderation.router)
    dp.include_router(dialogue.router)
    
    # Запуск
    logging.info(f"Bot started. Admin group: {ADMIN_GROUP_ID}")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
