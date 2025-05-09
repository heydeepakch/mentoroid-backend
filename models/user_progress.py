from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from .user import PyObjectId

class UserProgress(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "64f5a25e3f6b3c2a1d8b4567",
                "course_id": "64f5a25e3f6b3c2a1d8b4568",
                "completed_materials": ["64f5a25e3f6b3c2a1d8b4569"],
                "completed_quizzes": ["64f5a25e3f6b3c2a1d8b4570"],
                "current_material": "64f5a25e3f6b3c2a1d8b4571",
                "progress_percentage": 45.5,
                "last_accessed": "2024-05-09T10:30:00",
                "time_spent": 3600
            }
        }
    )

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    course_id: PyObjectId = Field(...)
    completed_materials: List[PyObjectId] = Field(default_factory=list)
    completed_quizzes: List[PyObjectId] = Field(default_factory=list)
    current_material: Optional[PyObjectId] = None
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    time_spent: int = Field(default=0, description="Time spent in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Collection:
        name = "user_progress" 