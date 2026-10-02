import aiosqlite
from .db import get_db
from typing import List, Optional, Dict

# ==================== USERS ====================
async def create_user(telegram_id: int, username: str = None):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await db.commit()
    finally:
        await db.close()

async def get_user(telegram_id: int) -> Optional[Dict]:
    db = await get_db()
    try:
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"telegram_id": row[0], "username": row[1], "created_at": row[2]}
        return None
    finally:
        await db.close()

# ==================== ROLES ====================
async def create_role(name: str, questions: List[str] = None):
    db = await get_db()
    try:
        cursor = await db.execute("INSERT INTO roles (name) VALUES (?)", (name,))
        role_id = cursor.lastrowid
        
        if questions and questions[0].lower() != "пусто":
            for idx, question in enumerate(questions, 1):
                await db.execute(
                    "INSERT INTO role_questions (role_id, question_text, question_order) VALUES (?, ?, ?)",
                    (role_id, question.strip(), idx)
                )
        await db.commit()
    finally:
        await db.close()

async def get_all_roles() -> List[Dict]:
    db = await get_db()
    try:
        async with db.execute("SELECT id, name FROM roles") as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        await db.close()

async def get_role_questions(role_id: int) -> List[str]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT question_text FROM role_questions WHERE role_id = ? ORDER BY question_order",
            (role_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    finally:
        await db.close()

async def delete_role(name: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM roles WHERE name = ?", (name,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()

# ==================== APPLICATIONS ====================
async def create_application(user_id: int, role_id: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO applications (user_id, role_id, status) VALUES (?, ?, 'pending')",
            (user_id, role_id)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()

async def add_answer(application_id: int, question_text: str, answer_text: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO answers (application_id, question_text, answer_text) VALUES (?, ?, ?)",
            (application_id, question_text, answer_text)
        )
        await db.commit()
    finally:
        await db.close()

async def get_application(application_id: int) -> Optional[Dict]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0], "user_id": row[1], "role_id": row[2],
                    "status": row[3], "created_at": row[4]
                }
        return None
    finally:
        await db.close()

async def get_application_answers(application_id: int) -> List[Dict]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT question_text, answer_text FROM answers WHERE application_id = ?",
            (application_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"question": row[0], "answer": row[1]} for row in rows]
    finally:
        await db.close()

async def update_application_status(application_id: int, status: str):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (status, application_id)
        )
        await db.commit()
    finally:
        await db.close()

async def get_user_rejected_applications(user_id: int) -> List[Dict]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT id, created_at FROM applications WHERE user_id = ? AND status = 'rejected' ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "created_at": row[1]} for row in rows]
    finally:
        await db.close()

async def get_pending_application_by_user(user_id: int) -> Optional[int]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT id FROM applications WHERE user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
    finally:
        await db.close()

# ==================== DIALOGUES ====================
async def create_dialogue(admin_id: int, user_id: int) -> int:
    db = await get_db()
    try:
        # Deactivate all previous dialogs for this admin
        await db.execute("UPDATE dialogues SET active = 0 WHERE admin_id = ?", (admin_id,))
        
        cursor = await db.execute(
            "INSERT INTO dialogues (admin_id, user_id, active) VALUES (?, ?, 1)",
            (admin_id, user_id)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()

async def get_active_dialogue(admin_id: int) -> Optional[Dict]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT id, user_id FROM dialogues WHERE admin_id = ? AND active = 1",
            (admin_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"id": row[0], "user_id": row[1]}
        return None
    finally:
        await db.close()

async def get_active_dialogue_by_user(user_id: int) -> Optional[Dict]:
    db = await get_db()
    try:
        async with db.execute(
            "SELECT id, admin_id FROM dialogues WHERE user_id = ? AND active = 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"id": row[0], "admin_id": row[1]}
        return None
    finally:
        await db.close()

async def deactivate_dialogue(admin_id: int):
    db = await get_db()
    try:
        await db.execute("UPDATE dialogues SET active = 0 WHERE admin_id = ?", (admin_id,))
        await db.commit()
    finally:
        await db.close()
