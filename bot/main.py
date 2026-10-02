import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from .config import BOT_TOKEN
from .database.db import init_db
from .handlers import user, admin_commands, moderation, dialogue
from .config import ADMIN_GROUP_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    await init_db()
    
    # Создание бота
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
