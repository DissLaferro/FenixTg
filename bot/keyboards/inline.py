from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..database import crud

async def get_roles_keyboard():
    roles = await crud.get_all_roles()
    keyboard = []
    for role in roles:
        keyboard.append([
            InlineKeyboardButton(text=role["name"], callback_data=f"role_{role['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_moderation_keyboard(application_id: int, has_previous_rejected: bool = False):
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{application_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{application_id}")
        ],
        [
            InlineKeyboardButton(text="💬 Спросить", callback_data=f"ask_{application_id}")
        ]
    ]
    
    if has_previous_rejected:
        buttons.append([
            InlineKeyboardButton(text="📜 Посмотреть предыдущую анкету", callback_data=f"previous_{application_id}")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_verdict_keyboard(application_id: int, has_previous_rejected: bool = False):
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{application_id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{application_id}")
        ]
    ]
    
    if has_previous_rejected:
        buttons.append([
            InlineKeyboardButton(text="📜 Посмотреть предыдущую анкету", callback_data=f"previous_{application_id}")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
