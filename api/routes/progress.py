from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from bson import ObjectId
from datetime import datetime

from ...models.user_progress import UserProgress
from ...models.quiz_submission import QuizSubmission
from ...models.user import User
from ..dependencies import get_current_user, get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Not found"}}
)

@router.get("/course/{course_id}", response_model=UserProgress)
async def get_course_progress(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    progress = await db[UserProgress.Collection.name].find_one({
        "user_id": current_user.id,
        "course_id": ObjectId(course_id)
    })
    
    if not progress:
        # Initialize progress if not exists
        progress = UserProgress(
            user_id=current_user.id,
            course_id=ObjectId(course_id)
        ).model_dump(by_alias=True)
        await db[UserProgress.Collection.name].insert_one(progress)
        progress = await db[UserProgress.Collection.name].find_one({"_id": progress["_id"]})
    
    return UserProgress.model_validate(progress)

@router.post("/material/{material_id}/complete")
async def mark_material_complete(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Get material to verify course_id
    material = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    course_id = material["course_id"]
    
    # Update progress
    result = await db[UserProgress.Collection.name].update_one(
        {
            "user_id": current_user.id,
            "course_id": course_id
        },
        {
            "$addToSet": {"completed_materials": ObjectId(material_id)},
            "$set": {
                "current_material": ObjectId(material_id),
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Recalculate progress percentage
    await update_progress_percentage(db, current_user.id, course_id)
    
    return {"message": "Material marked as completed"}

@router.get("/analytics/course/{course_id}")
async def get_course_analytics(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not current_user.is_instructor and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can view course analytics"
        )
    
    # Get all progress records for the course
    cursor = db[UserProgress.Collection.name].find({"course_id": ObjectId(course_id)})
    progress_records = await cursor.to_list(length=None)
    
    # Get quiz submissions
    quiz_cursor = db[QuizSubmission.Collection.name].find({"course_id": ObjectId(course_id)})
    quiz_submissions = await quiz_cursor.to_list(length=None)
    
    # Calculate analytics
    total_students = len(progress_records)
    completed_students = len([p for p in progress_records if p["progress_percentage"] == 100])
    avg_progress = sum(p["progress_percentage"] for p in progress_records) / total_students if total_students > 0 else 0
    
    quiz_stats = calculate_quiz_statistics(quiz_submissions)
    
    return {
        "total_students": total_students,
        "completed_students": completed_students,
        "average_progress": avg_progress,
        "quiz_statistics": quiz_stats
    }

async def update_progress_percentage(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId,
    course_id: ObjectId
):
    # Get total materials and quizzes in course
    total_materials = await db[Material.Collection.name].count_documents({"course_id": course_id})
    total_quizzes = await db[Quiz.Collection.name].count_documents({"course_id": course_id})
    total_items = total_materials + total_quizzes
    
    if total_items == 0:
        return
    
    # Get user progress
    progress = await db[UserProgress.Collection.name].find_one({
        "user_id": user_id,
        "course_id": course_id
    })
    
    if not progress:
        return
    
    # Calculate percentage
    completed_items = len(progress.get("completed_materials", [])) + len(progress.get("completed_quizzes", []))
    percentage = (completed_items / total_items) * 100
    
    # Update progress
    await db[UserProgress.Collection.name].update_one(
        {"_id": progress["_id"]},
        {
            "$set": {
                "progress_percentage": percentage,
                "updated_at": datetime.utcnow()
            }
        }
    )

def calculate_quiz_statistics(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not submissions:
        return {
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "completion_rate": 0
        }
    
    completed = [s for s in submissions if s["status"] == "completed"]
    scores = [s["total_score"] for s in completed]
    
    return {
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "completion_rate": (len(completed) / len(submissions)) * 100
    } 