from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .user import PyObjectId

class QuizAnswer(BaseModel):
    question_id: PyObjectId
    selected_options: List[str]
    is_correct: bool
    points_earned: float

class QuizSubmission(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "64f5a25e3f6b3c2a1d8b4567",
                "quiz_id": "64f5a25e3f6b3c2a1d8b4568",
                "course_id": "64f5a25e3f6b3c2a1d8b4569",
                "answers": [
                    {
                        "question_id": "64f5a25e3f6b3c2a1d8b4570",
                        "selected_options": ["A", "C"],
                        "is_correct": True,
                        "points_earned": 10.0
                    }
                ],
                "total_score": 85.5,
                "max_score": 100.0,
                "time_taken": 1200,
                "status": "completed",
                "submitted_at": "2024-05-09T10:30:00"
            }
        }
    )

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    quiz_id: PyObjectId = Field(...)
    course_id: PyObjectId = Field(...)
    answers: List[QuizAnswer] = Field(default_factory=list)
    total_score: float = Field(default=0.0, ge=0.0)
    max_score: float = Field(...)
    time_taken: int = Field(default=0, description="Time taken in seconds")
    status: str = Field(default="in_progress", pattern="^(in_progress|completed|abandoned)$")
    feedback: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Collection:
        name = "quiz_submissions" 