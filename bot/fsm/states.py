from aiogram.fsm.state import State, StatesGroup

class ApplicationForm(StatesGroup):
    # Базовые вопросы
    name_age = State()
    source = State()
    about = State()
    
    # Выбор роли
    choosing_role = State()
    
    # Специфичные вопросы роли (динамические)
    role_questions = State()
    
    # Ожидание решения
    waiting = State()
