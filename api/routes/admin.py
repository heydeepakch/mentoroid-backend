from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta

from ...models.user import User
from ...models.course import Course
from ...models.material import Material
from ...models.quiz import Quiz
from ..dependencies import get_current_user, get_db, verify_admin
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
    responses={404: {"description": "Not found"}}
)

@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Get system statistics
    total_users = await db[User.Collection.name].count_documents({})
    total_courses = await db[Course.Collection.name].count_documents({})
    total_materials = await db[Material.Collection.name].count_documents({})
    total_quizzes = await db[Quiz.Collection.name].count_documents({})
    
    # Get active users in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = await db[User.Collection.name].count_documents({
        "last_login": {"$gte": week_ago}
    })
    
    # Get instructor statistics
    instructors = await db[User.Collection.name].count_documents({
        "is_instructor": True
    })
    
    # Get course completion statistics
    completed_courses = await db[UserProgress.Collection.name].count_documents({
        "progress_percentage": 100
    })
    
    return {
        "system_stats": {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_materials": total_materials,
            "total_quizzes": total_quizzes,
            "active_users_7d": active_users,
            "total_instructors": instructors,
            "completed_courses": completed_courses
        }
    }

@router.get("/users", response_model=List[User])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db[User.Collection.name].find().skip(skip).limit(limit)
    users = await cursor.to_list(length=None)
    return [User.model_validate(user) for user in users]

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_update: Dict[str, bool],
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db[User.Collection.name].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if "is_instructor" in role_update:
        update_data["is_instructor"] = role_update["is_instructor"]
    if "is_admin" in role_update:
        update_data["is_admin"] = role_update["is_admin"]
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid role updates provided"
        )
    
    await db[User.Collection.name].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    return {"message": "User roles updated successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db[User.Collection.name].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's data
    await db[User.Collection.name].delete_one({"_id": ObjectId(user_id)})
    await db[UserProgress.Collection.name].delete_many({"user_id": ObjectId(user_id)})
    await db[QuizSubmission.Collection.name].delete_many({"user_id": ObjectId(user_id)})
    
    return {"message": "User and associated data deleted successfully"}

@router.get("/audit-log")
async def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db["audit_log"].find().sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=None)
    return logs

@router.post("/system/maintenance")
async def run_system_maintenance(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Clean up expired sessions
    week_ago = datetime.utcnow() - timedelta(days=7)
    await db["sessions"].delete_many({
        "last_activity": {"$lt": week_ago}
    })
    
    # Archive old audit logs
    month_ago = datetime.utcnow() - timedelta(days=30)
    await db["audit_log_archive"].insert_many(
        await db["audit_log"].find({"timestamp": {"$lt": month_ago}}).to_list(None)
    )
    await db["audit_log"].delete_many({"timestamp": {"$lt": month_ago}})
    
    # Update course statistics
    courses = await db[Course.Collection.name].find().to_list(None)
    for course in courses:
        enrolled = await db[UserProgress.Collection.name].count_documents({
            "course_id": course["_id"]
        })
        completed = await db[UserProgress.Collection.name].count_documents({
            "course_id": course["_id"],
            "progress_percentage": 100
        })
        await db[Course.Collection.name].update_one(
            {"_id": course["_id"]},
            {
                "$set": {
                    "enrolled_count": enrolled,
                    "completion_count": completed,
                    "last_updated": datetime.utcnow()
                }
            }
        )
    
    return {"message": "System maintenance completed successfully"} 