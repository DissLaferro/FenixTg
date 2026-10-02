from aiogram import Bot
from aiogram.types import ChatInviteLink
from datetime import datetime, timedelta
from ..config import PLAYER_GROUP_ID

async def generate_invite_link(bot: Bot) -> str:
    """Генерирует одноразовую инвайт-ссылку в группу игроков"""
    expire_date = datetime.now() + timedelta(hours=24)
    
    link: ChatInviteLink = await bot.create_chat_invite_link(
        chat_id=PLAYER_GROUP_ID,
        expire_date=expire_date,
        member_limit=1
    )
    
    return link.invite_link
