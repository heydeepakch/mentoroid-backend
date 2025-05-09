from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Any
from models.quiz import Quiz, QuizCreate, QuizInDB, QuizSubmission
from models.user import User
from utils.auth import get_current_user, check_teacher_permission
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import openai
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/", response_model=Quiz)
async def create_quiz(
    quiz_in: QuizCreate,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Create a new quiz.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course exists and user is the teacher
    course = await db.courses.find_one({"_id": ObjectId(quiz_in.course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["teacher_id"] != ObjectId(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    quiz = QuizInDB(
        **quiz_in.dict(),
        created_by=ObjectId(current_user.id)
    )
    
    result = await db.quizzes.insert_one(quiz.dict(by_alias=True))
    quiz.id = result.inserted_id
    
    return quiz

@router.get("/course/{course_id}", response_model=List[Quiz])
async def list_course_quizzes(
    course_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all quizzes for a course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course exists and user has access
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
    
    quizzes = await db.quizzes.find(
        {"course_id": ObjectId(course_id)}
    ).to_list(length=None)
    
    return quizzes

@router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(
    quiz_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific quiz.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    quiz = await db.quizzes.find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify course access
    course = await db.courses.find_one({"_id": quiz["course_id"]})
    if current_user.role == "student" and ObjectId(current_user.id) not in course["students"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    return quiz

@router.post("/{quiz_id}/submit", response_model=QuizSubmission)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Submit a quiz.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    quiz = await db.quizzes.find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify course access
    course = await db.courses.find_one({"_id": quiz["course_id"]})
    if current_user.role == "student" and ObjectId(current_user.id) not in course["students"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    # Calculate score
    score = 0
    total_points = 0
    feedback = []
    
    for question in quiz["questions"]:
        total_points += question["points"]
        student_answer = next(
            (ans["answer"] for ans in submission.answers if ans["question_id"] == str(question["_id"])),
            None
        )
        
        if student_answer:
            if question["type"] == "mcq":
                if student_answer == question["correct_answer"]:
                    score += question["points"]
            elif question["type"] in ["short", "long"]:
                # Use AI to evaluate descriptive answers
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an educational assistant evaluating student answers."},
                            {"role": "user", "content": f"Question: {question['question']}\nCorrect Answer: {question['correct_answer']}\nStudent Answer: {student_answer}\nEvaluate the answer and provide a score out of {question['points']} points."}
                        ]
                    )
                    evaluation = response.choices[0].message.content
                    # Extract score from evaluation (you might want to improve this parsing)
                    score += float(evaluation.split("score:")[-1].strip().split()[0])
                    feedback.append(f"Q: {question['question']}\nA: {student_answer}\nFeedback: {evaluation}")
                except Exception as e:
                    feedback.append(f"Error evaluating answer: {str(e)}")
    
    submission.score = (score / total_points) * 100 if total_points > 0 else 0
    submission.feedback = "\n\n".join(feedback)
    
    # Save submission
    result = await db.quiz_submissions.insert_one(submission.dict(by_alias=True))
    submission.id = result.inserted_id
    
    return submission

@router.post("/generate", response_model=Quiz)
async def generate_quiz(
    course_id: str,
    num_questions: int = 5,
    request: Request = None,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Generate a quiz using AI.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course exists and user is the teacher
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course["teacher_id"] != ObjectId(current_user.id) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not the teacher of this course"
        )
    
    # Get course materials for context
    materials_text = "\n".join([
        f"Material: {m['title']}\n{m.get('description', '')}"
        for m in course["materials"]
    ])
    
    try:
        # Generate quiz using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational assistant creating quizzes."},
                {"role": "user", "content": f"Create a quiz with {num_questions} questions based on this course material:\n\n{materials_text}\n\nGenerate a mix of multiple-choice and short-answer questions."}
            ]
        )
        
        # Parse the generated quiz (you'll need to implement proper parsing)
        generated_quiz = response.choices[0].message.content
        
        # Create quiz object
        quiz = QuizInDB(
            title=f"AI Generated Quiz - {course['title']}",
            description="Quiz generated using AI based on course materials",
            course_id=ObjectId(course_id),
            created_by=ObjectId(current_user.id),
            questions=[]  # You'll need to parse the generated questions
        )
        
        result = await db.quizzes.insert_one(quiz.dict(by_alias=True))
        quiz.id = result.inserted_id
        
        return quiz
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quiz: {str(e)}"
        ) 