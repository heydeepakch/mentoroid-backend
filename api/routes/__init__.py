"""
Route handlers for the LMS API
"""

from .auth import router as auth_router
from .users import router as users_router
from .courses import router as courses_router
from .quizzes import router as quizzes_router
from .chat import router as chat_router
from .materials import router as materials_router
from .progress import router as progress_router
from .admin import router as admin_router
from .ai import router as ai_router

__all__ = [
    "auth_router",
    "users_router",
    "courses_router",
    "quizzes_router",
    "chat_router",
    "materials_router",
    "progress_router",
    "admin_router",
    "ai_router"
] 