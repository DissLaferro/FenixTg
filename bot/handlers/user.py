from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ..fsm.states import ApplicationForm
from ..database import crud
from ..keyboards.inline import get_roles_keyboard

router = Router()

# Базовые вопросы
BASE_QUESTIONS = [
    ("name_age", "👤 Ваше имя и возраст?"),
    ("source", "🔍 Откуда вы узнали о нас?"),
    ("about", "📝 Расскажите о себе (опыт в игре, интересы, цели):")
]

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Создаем пользователя в БД
    await crud.create_user(user_id, message.from_user.username)
    
    # Проверяем, есть ли pending заявка
    pending_app = await crud.get_pending_application_by_user(user_id)
    if pending_app:
        await message.answer("⏳ Ваша заявка уже на рассмотрении. Пожалуйста, ожидайте решения.")
        return
    
    # Начинаем анкетирование
    await state.set_state(ApplicationForm.name_age)
    await state.update_data(answers={}, current_question_index=0)
    await message.answer(BASE_QUESTIONS[0][1])

@router.message(ApplicationForm.name_age)
async def process_name_age(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["name_age"] = message.text
    await state.update_data(answers=answers)
    
    await state.set_state(ApplicationForm.source)
    await message.answer(BASE_QUESTIONS[1][1])

@router.message(ApplicationForm.source)
async def process_source(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["source"] = message.text
    await state.update_data(answers=answers)
    
    await state.set_state(ApplicationForm.about)
    await message.answer(BASE_QUESTIONS[2][1])

@router.message(ApplicationForm.about)
async def process_about(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    answers["about"] = message.text
    await state.update_data(answers=answers)
    
    # Переходим к выбору роли
    await state.set_state(ApplicationForm.choosing_role)
    keyboard = await get_roles_keyboard()
    await message.answer("🎭 Выберите роль:", reply_markup=keyboard)

@router.callback_query(ApplicationForm.choosing_role, F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_id = int(callback.data.split("_")[1])
    
    # Получаем вопросы для роли
    questions = await crud.get_role_questions(role_id)
    
    if not questions:
        # Нет дополнительных вопросов - завершаем анкету
        await finish_application(callback.message, state, role_id)
        await callback.answer()
        return
    
    # Сохраняем вопросы и начинаем их задавать
    await state.update_data(
        role_id=role_id,
        role_questions=questions,
        current_question_index=0
    )
    await state.set_state(ApplicationForm.role_questions)
    await callback.message.answer(questions[0])
    await callback.answer()

@router.message(ApplicationForm.role_questions)
async def process_role_question(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get("answers", {})
    questions = data.get("role_questions", [])
    idx = data.get("current_question_index", 0)
    
    # Сохраняем ответ
    answers[f"role_q_{idx}"] = {"question": questions[idx], "answer": message.text}
    await state.update_data(answers=answers)
    
    # Следующий вопрос
    idx += 1
    if idx < len(questions):
        await state.update_data(current_question_index=idx)
        await message.answer(questions[idx])
    else:
        # Все вопросы пройдены
        role_id = data.get("role_id")
        await finish_application(message, state, role_id)

async def finish_application(message: Message, state: FSMContext, role_id: int):
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Создаем заявку в БД
    application_id = await crud.create_application(user_id, role_id)
    
    # Сохраняем ответы
    answers = data.get("answers", {})
    
    # Базовые ответы
    await crud.add_answer(application_id, BASE_QUESTIONS[0][1], answers.get("name_age", ""))
    await crud.add_answer(application_id, BASE_QUESTIONS[1][1], answers.get("source", ""))
    await crud.add_answer(application_id, BASE_QUESTIONS[2][1], answers.get("about", ""))
    
    # Ответы на специфичные вопросы роли
    role_answers = {k: v for k, v in answers.items() if k.startswith("role_q_")}
    for key in sorted(role_answers.keys()):
        item = role_answers[key]
        await crud.add_answer(application_id, item["question"], item["answer"])
    
    # Отправляем в админ-чат
    from .moderation import send_to_moderation
    await send_to_moderation(message.bot, application_id, user_id, role_id)
    
    await state.clear()
    await message.answer("✅ Ваша заявка отправлена на рассмотрение. Ожидайте решения.")
