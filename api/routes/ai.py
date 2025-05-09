from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Any, Optional
from models.user import User
from utils.auth import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import openai
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/personalize")
async def get_personalized_content(
    course_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get personalized content recommendations based on student's performance.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course access
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if current_user.role == "student" and ObjectId(current_user.id) not in course["students"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    # Get student's quiz submissions
    submissions = await db.quiz_submissions.find(
        {"student_id": ObjectId(current_user.id), "course_id": ObjectId(course_id)}
    ).to_list(length=None)
    
    try:
        # Use OpenAI to generate personalized recommendations
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational assistant providing personalized learning recommendations."},
                {"role": "user", "content": f"Based on the student's quiz submissions and course materials, provide personalized learning recommendations. Course: {course['title']}, Submissions: {submissions}"}
            ]
        )
        
        return {
            "recommendations": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )

@router.post("/generate-content")
async def generate_learning_content(
    topic: str,
    difficulty: str = "intermediate",
    request: Request = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Generate learning content using AI.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational content creator."},
                {"role": "user", "content": f"Create comprehensive learning content about {topic} at {difficulty} level. Include explanations, examples, and practice questions."}
            ]
        )
        
        return {
            "content": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}"
        )

@router.post("/analyze-performance")
async def analyze_performance(
    course_id: str,
    student_id: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Analyze student performance using AI.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course access
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # If student_id is provided, verify permissions
    if student_id:
        if current_user.role not in ["admin", "teacher"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        target_id = ObjectId(student_id)
    else:
        target_id = ObjectId(current_user.id)
    
    # Get student's submissions
    submissions = await db.quiz_submissions.find(
        {"student_id": target_id, "course_id": ObjectId(course_id)}
    ).to_list(length=None)
    
    try:
        # Use OpenAI to analyze performance
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational analyst."},
                {"role": "user", "content": f"Analyze the student's performance in {course['title']} based on their quiz submissions: {submissions}. Provide insights on strengths, weaknesses, and improvement areas."}
            ]
        )
        
        return {
            "analysis": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing performance: {str(e)}"
        )

@router.post("/chat-assistant")
async def chat_with_assistant(
    message: str,
    course_id: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Chat with AI learning assistant.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    context = ""
    
    # If course_id is provided, add course context
    if course_id:
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if course:
            context = f"Course context: {course['title']} - {course['description']}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI learning assistant helping students with their studies."},
                {"role": "user", "content": f"{context}\n\nStudent question: {message}"}
            ]
        )
        
        return {
            "response": response.choices[0].message.content
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat assistant: {str(e)}"
        ) 