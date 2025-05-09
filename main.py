import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorDatabase

# Add the project root directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from backend.api.routes import (
    auth_router,
    users_router,
    courses_router,
    quizzes_router,
    chat_router,
    materials_router,
    progress_router,
    admin_router,
    ai_router
)
from backend.utils.db import get_database, init_indexes, close_db_connection
from backend.utils.ai_helpers import AIHelper

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection and indexes
    db = await get_database()
    await init_indexes()
    
    # Store db instance in app state
    app.state.db = db
    
    # Initialize AI helper
    app.state.ai_helper = AIHelper(db)
    
    yield
    
    # Cleanup
    await close_db_connection()

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-Powered Learning Management System",
        description="A modern LMS with AI-enhanced features for personalized learning",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS with specific settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        expose_headers=["*"],
        max_age=3600,
    )

    # Include routers with proper prefixes and tags
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(courses_router, prefix="/api/courses", tags=["Courses"])
    app.include_router(quizzes_router, prefix="/api/quizzes", tags=["Quizzes"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(materials_router, prefix="/api/materials", tags=["Materials"])
    app.include_router(progress_router, prefix="/api/progress", tags=["Progress"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(ai_router, prefix="/api/ai", tags=["AI"])

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to the AI-Powered Learning Management System API",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0"
        }

    return app

# Create FastAPI application instance
app = create_app()

# Dependency to get database from app state
async def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db

# Dependency to get AI helper from app state
async def get_ai_helper(request: Request) -> AIHelper:
    return request.app.state.ai_helper 