from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Any
from models.course import Course, CourseCreate, CourseInDB, Material
from models.user import User
from utils.auth import get_current_user, check_teacher_permission
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=Course)
async def create_course(
    course_in: CourseCreate,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Create a new course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    course = CourseInDB(
        **course_in.dict(),
        teacher_id=ObjectId(current_user.id)
    )
    
    result = await db.courses.insert_one(course.dict(by_alias=True))
    course.id = result.inserted_id
    
    return course

@router.get("/", response_model=List[Course])
async def list_courses(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all courses (filtered by role).
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    if current_user.role == "student":
        # Students see only enrolled courses
        courses = await db.courses.find(
            {"students": ObjectId(current_user.id)}
        ).to_list(length=None)
    elif current_user.role == "teacher":
        # Teachers see their own courses
        courses = await db.courses.find(
            {"teacher_id": ObjectId(current_user.id)}
        ).to_list(length=None)
    else:
        # Admins see all courses
        courses = await db.courses.find().to_list(length=None)
    
    return courses

@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions
    if current_user.role == "student" and ObjectId(current_user.id) not in course["students"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    elif current_user.role == "teacher" and course["teacher_id"] != ObjectId(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    return course

@router.put("/{course_id}", response_model=Course)
async def update_course(
    course_id: str,
    course_in: CourseCreate,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Update a course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the teacher
    if course["teacher_id"] != ObjectId(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    # Update course
    update_data = course_in.dict(exclude_unset=True)
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": update_data}
    )
    
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    return updated_course

@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Delete a course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the teacher
    if course["teacher_id"] != ObjectId(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    # Delete course
    await db.courses.delete_one({"_id": ObjectId(course_id)})
    
    return {"message": "Course deleted successfully"}

@router.post("/{course_id}/materials", response_model=Course)
async def add_material(
    course_id: str,
    material: Material,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Add material to a course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if user is the teacher
    if course["teacher_id"] != ObjectId(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    # Add material
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$push": {"materials": material.dict(by_alias=True)}}
    )
    
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    return updated_course 