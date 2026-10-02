from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from ..database import crud
from ..middlewares.admin_check import AdminCheckMiddleware

router = Router()
router.message.middleware(AdminCheckMiddleware())

@router.message(Command("add_role"))
async def cmd_add_role(message: Message):
    """
    Формат: /add_role Название роли | Вопрос 1 | Вопрос 2 | ...
    Или: /add_role Название роли | пусто
    """
    text = message.text.replace("/add_role", "").strip()
    
    if "|" not in text:
        await message.answer("❌ Неверный формат. Используйте:\n/add_role Название роли | Вопрос 1 | Вопрос 2\nили /add_role Название роли | пусто")
        return
    
    parts = [p.strip() for p in text.split("|")]
    role_name = parts[0]
    questions = parts[1:] if len(parts) > 1 else None
    
    try:
        # Удаляем старую роль с таким именем (если есть)
        await crud.delete_role(role_name)
        # Создаем новую
        await crud.create_role(role_name, questions)
        await message.answer(f"✅ Роль «{role_name}» {'создана без дополнительных вопросов' if questions and questions[0].lower() == 'пусто' else 'создана с ' + str(len(questions)) + ' вопросами'}")
    except Exception as e:
        await message.answer(f"❌ Ошибка создания роли: {e}")

@router.message(Command("remove_role"))
async def cmd_remove_role(message: Message):
    """
    Формат: /remove_role Название роли
    """
    role_name = message.text.replace("/remove_role", "").strip()
    
    if not role_name:
        await message.answer("❌ Укажите название роли: /remove_role Название роли")
        return
    
    deleted = await crud.delete_role(role_name)
    if deleted:
        await message.answer(f"✅ Роль «{role_name}» удалена")
    else:
        await message.answer(f"❌ Роль «{role_name}» не найдена")
