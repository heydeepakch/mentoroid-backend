from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class Material(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: str = Field(..., pattern="^(pdf|video|link)$")
    url: str
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class CourseBase(BaseModel):
    title: str
    description: str
    teacher_id: PyObjectId
    objectives: List[str] = []

class CourseCreate(CourseBase):
    pass

class CourseInDB(CourseBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    students: List[PyObjectId] = []
    materials: List[Material] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class Course(CourseBase):
    id: str = Field(alias="_id")
    students: List[str] = []
    materials: List[Material] = []
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True
    } 