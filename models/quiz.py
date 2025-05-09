from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class Question(BaseModel):
    question: str
    type: str = Field(..., pattern="^(mcq|short|long)$")
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    points: int = 1

class QuizBase(BaseModel):
    title: str
    description: str
    course_id: PyObjectId
    questions: List[Question] = []

    model_config = {
        "arbitrary_types_allowed": True
    }

class QuizCreate(QuizBase):
    pass

class QuizInDB(QuizBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_points: int = 0

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class Quiz(QuizBase):
    id: str = Field(alias="_id")
    created_by: str
    created_at: datetime
    updated_at: datetime
    total_points: int

    model_config = {
        "populate_by_name": True
    }

class QuizSubmission(BaseModel):
    quiz_id: PyObjectId
    student_id: PyObjectId
    answers: List[dict]  # List of {question_id: answer}
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = None
    feedback: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    } 