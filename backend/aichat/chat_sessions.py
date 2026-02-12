# backend/chat_sessions.py

# глобальный словарь для хранения истории сессий
SESSION_CACHE = {}

def get_history(session_id):
    """Получить историю сессии по session_id"""
    return SESSION_CACHE.get(session_id, [])

def append_history(session_id, role, content):
    """Добавить сообщение в историю"""
    if session_id not in SESSION_CACHE:
        SESSION_CACHE[session_id] = []
    SESSION_CACHE[session_id].append({"role": role, "content": content})
