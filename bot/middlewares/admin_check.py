from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from ..config import ADMIN_GROUP_ID

class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, что сообщение из админ-группы
        chat_id = event.chat.id if hasattr(event, 'chat') else event.message.chat.id
        
        if chat_id != ADMIN_GROUP_ID:
            # Не из админ-группы - не пускаем
            if isinstance(event, Message):
                await event.reply("❌ Эта команда доступна только в админ-чате.")
            return None
        
        return await handler(event, data)
