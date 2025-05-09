from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class MaterialBase(BaseModel):
    title: str
    description: str
    type: str = Field(..., pattern="^(document|video|link|assignment)$")
    content_url: str
    course_id: PyObjectId
    tags: List[str] = Field(default_factory=list)
    difficulty_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    estimated_time: int  # in minutes

class MaterialCreate(MaterialBase):
    pass

class MaterialInDB(MaterialBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    likes: int = 0
    is_published: bool = True

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class Material(MaterialBase):
    id: str = Field(alias="_id")
    created_by: str
    created_at: datetime
    updated_at: datetime
    views: int
    likes: int
    is_published: bool

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    ) 