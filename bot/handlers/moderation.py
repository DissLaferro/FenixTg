from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from ..database import crud
from ..keyboards.inline import get_moderation_keyboard, get_verdict_keyboard
from ..config import ADMIN_GROUP_ID

router = Router()

# Хранилище для текущих активных диалогов
active_dialogues = {}

async def send_to_moderation(bot: Bot, application_id: int, user_id: int, role_id: int):
    """Отправляет анкету на модерацию в админ-чат"""
    
    # Получаем данные
    user = await crud.get_user(user_id)
    answers = await crud.get_application_answers(application_id)
    
    # Проверяем, есть ли предыдущие отказы
    previous_apps = await crud.get_user_rejected_applications(user_id)
    has_previous = len(previous_apps) > 0
    
    # Формируем сообщение
    role_name = ""
    roles = await crud.get_all_roles()
    for r in roles:
        if r["id"] == role_id:
            role_name = r["name"]
            break
    
    text = f"📋 <b>Новая заявка #{application_id}</b>\n\n"
    text += f"👤 <b>Пользователь:</b> @{user['username'] or 'no_username'} (ID: {user_id})\n"
    text += f"🎭 <b>Роль:</b> {role_name}\n\n"
    
    if has_previous:
        text += "⚠️ <b>Внимание:</b> У данного пользователя есть отклоненные заявки!\n\n"
    
    text += "<b>Ответы:</b>\n"
    for idx, ans in enumerate(answers, 1):
        text += f"{idx}. {ans['question']}\n   <i>{ans['answer']}</i>\n\n"
    
    keyboard = get_moderation_keyboard(application_id, has_previous)
    
    await bot.send_message(ADMIN_GROUP_ID, text, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data.startswith("accept_"))
async def process_accept(callback: CallbackQuery, bot: Bot):
    application_id = int(callback.data.split("_")[1])
    
    # Обновляем статус
    await crud.update_application_status(application_id, "accepted")
    
    # Получаем user_id
    app = await crud.get_application(application_id)
    
    # Генерируем инвайт-ссылку
    from ..utils.invite import generate_invite_link
    invite_link = await generate_invite_link(bot)
    
    # Отправляем игроку
    try:
        await bot.send_message(
            app["user_id"],
            f"🎉 Поздравляем! Ваша заявка принята.\n\n"
            f"🔗 Ссылка для вступления в группу:\n{invite_link}\n\n"
            f"⚠️ Ссылка одноразовая и действительна 24 часа."
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Заявка #{application_id} принята. Инвайт отправлен игроку.")
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось отправить инвайт: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def process_reject(callback: CallbackQuery):
    application_id = int(callback.data.split("_")[1])
    
    # Обновляем статус
    await crud.update_application_status(application_id, "rejected")
    
    # Получаем user_id
    app = await crud.get_application(application_id)
    
    # Отправляем игроку
    try:
        await callback.bot.send_message(
            app["user_id"],
            "❌ К сожалению, ваша заявка отклонена. Вы можете подать новую заявку через некоторое время."
        )
    except Exception as e:
        pass
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Заявка #{application_id} отклонена.")
    await callback.answer()

@router.callback_query(F.data.startswith("ask_"))
async def process_ask(callback: CallbackQuery, bot: Bot):
    application_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id
    
    # Получаем данные заявки
    app = await crud.get_application(application_id)
    user_id = app["user_id"]
    
    # Создаем диалог
    await crud.create_dialogue(admin_id, user_id)
    
    # Пересылаем историю админу в ЛС
    answers = await crud.get_application_answers(application_id)
    
    text = f"💬 <b>Диалог с игроком ID: {user_id}</b>\n"
    text += f"Заявка #{application_id}\n\n"
    text += "<b>История анкеты:</b>\n"
    for idx, ans in enumerate(answers, 1):
        text += f"{idx}. {ans['question']}\n   <i>{ans['answer']}</i>\n\n"
    
    text += "\n✍️ Напишите сообщение игроку. Для выхода из режима диалога отправьте: Backward"
    
    try:
        await bot.send_message(admin_id, text, parse_mode="HTML")
        await callback.message.answer(f"💬 Админ {callback.from_user.mention} начал диалог с игроком.")
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось начать диалог: {e}\nВозможно, бот заблокирован в ЛС.")
    
    await callback.answer()

@router.callback_query(F.data.startswith("previous_"))
async def process_previous(callback: CallbackQuery):
    application_id = int(callback.data.split("_")[1])
    
    # Получаем текущую заявку, чтобы узнать user_id
    app = await crud.get_application(application_id)
    user_id = app["user_id"]
    
    # Получаем предыдущие отклоненные заявки
    previous_apps = await crud.get_user_rejected_applications(user_id)
    
    if not previous_apps:
        await callback.answer("Предыдущих анкет нет")
        return
    
    # Берем последнюю отклоненную (не текущую)
    for prev in previous_apps:
        if prev["id"] != application_id:
            answers = await crud.get_application_answers(prev["id"])
            text = f"📜 <b>Предыдущая анкета #{prev['id']}</b>\n"
            text += f"Дата: {prev['created_at']}\n\n"
            
            for idx, ans in enumerate(answers, 1):
                text += f"{idx}. {ans['question']}\n   <i>{ans['answer']}</i>\n\n"
            
            await callback.message.answer(text, parse_mode="HTML")
            break
    
    await callback.answer()
