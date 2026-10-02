from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from ..database import crud
from ..keyboards.inline import get_verdict_keyboard

router = Router()

@router.message(Command("backward"))
async def cmd_backward(message: Message):
    """Выход из режима диалога"""
    admin_id = message.from_user.id
    
    # Получаем активный диалог
    dialogue = await crud.get_active_dialogue(admin_id)
    
    if not dialogue:
        await message.answer("❌ У вас нет активного диалога.")
        return
    
    user_id = dialogue["user_id"]
    
    # Деактивируем диалог
    await crud.deactivate_dialogue(admin_id)
    
    # Получаем последнюю pending заявку этого пользователя
    app_id = await crud.get_pending_application_by_user(user_id)
    
    if app_id:
        # Проверяем предыдущие отказы
        previous_apps = await crud.get_user_rejected_applications(user_id)
        has_previous = len([p for p in previous_apps if p["id"] != app_id]) > 0
        
        keyboard = get_verdict_keyboard(app_id, has_previous)
        await message.answer(
            "✅ Режим диалога завершен. Выберите вердикт:",
            reply_markup=keyboard
        )
    else:
        await message.answer("✅ Режим диалога завершен.")

@router.message()
async def handle_dialogue_message(message: Message):
    """Пересылка сообщений в режиме диалога"""
    sender_id = message.from_user.id
    
    # Проверяем, есть ли активный диалог от админа
    dialogue_as_admin = await crud.get_active_dialogue(sender_id)
    
    # Проверяем, есть ли активный диалог с игроком
    dialogue_as_user = await crud.get_active_dialogue_by_user(sender_id)
    
    if dialogue_as_admin:
        # Админ пишет игроку
        user_id = dialogue_as_admin["user_id"]
        try:
            await message.bot.send_message(
                user_id,
                f"📨 <b>Сообщение от администрации:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
            await message.answer("✅ Отправлено игроку")
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить сообщение: {e}")
    
    elif dialogue_as_user:
        # Игрок отвечает админу
        admin_id = dialogue_as_user["admin_id"]
        try:
            await message.bot.send_message(
                admin_id,
                f"📨 <b>Ответ от игрока:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
        except Exception as e:
            pass  # Игнорируем ошибки при отправке игроку
    # Если нет активного диалога - сообщение обрабатывается другими хэндлерами
