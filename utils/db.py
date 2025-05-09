from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "lms_db")

# Global database instance
_db: Optional[AsyncIOMotorDatabase] = None

async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance with connection pooling.
    Returns the same instance if already connected.
    """
    global _db
    if _db is None:
        client = AsyncIOMotorClient(MONGODB_URL)
        _db = client[DATABASE_NAME]
    return _db

async def init_indexes():
    """
    Initialize database indexes for better query performance.
    Should be called once during application startup.
    """
    db = await get_database()
    
    # Drop existing indexes to clean up
    await db.users.drop_indexes()
    
    # User indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("last_login")
    
    # Course indexes
    await db.courses.create_index("instructor_id")
    await db.courses.create_index("title")
    await db.courses.create_index("created_at")
    
    # Material indexes
    await db.materials.create_index("course_id")
    await db.materials.create_index("created_by")
    await db.materials.create_index([("title", "text"), ("description", "text")])
    
    # Quiz indexes
    await db.quizzes.create_index("course_id")
    await db.quizzes.create_index("created_by")
    
    # Progress indexes
    await db.user_progress.create_index([("user_id", 1), ("course_id", 1)], unique=True)
    await db.user_progress.create_index("last_accessed")
    
    # Quiz submission indexes
    await db.quiz_submissions.create_index([("user_id", 1), ("quiz_id", 1)])
    await db.quiz_submissions.create_index("course_id")
    await db.quiz_submissions.create_index("submitted_at")
    
    # Chat indexes
    await db.chats.create_index([("user_id", 1), ("course_id", 1)])
    await db.chats.create_index("created_at")
    
    # Audit log indexes
    await db.audit_log.create_index("timestamp")
    await db.audit_log.create_index("user_id")
    await db.audit_log.create_index("action_type")

async def close_db_connection():
    """
    Close the database connection.
    Should be called during application shutdown.
    """
    global _db
    if _db is not None:
        client = _db.client
        client.close()
        _db = None

async def get_collection(collection_name: str) -> AsyncIOMotorDatabase:
    """
    Get a specific collection from the database.
    """
    db = await get_database()
    return db[collection_name]

async def create_audit_log(
    db: AsyncIOMotorDatabase,
    user_id: str,
    action_type: str,
    details: dict,
    resource_id: Optional[str] = None
):
    """
    Create an audit log entry for tracking system actions.
    """
    log_entry = {
        "user_id": user_id,
        "action_type": action_type,
        "details": details,
        "resource_id": resource_id,
        "timestamp": datetime.utcnow(),
        "ip_address": None  # Should be set from request in route handlers
    }
    
    await db.audit_log.insert_one(log_entry) 