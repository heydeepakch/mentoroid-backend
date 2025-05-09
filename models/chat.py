from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class Message(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    sender_id: PyObjectId
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_pinned: bool = False
    reply_to: Optional[PyObjectId] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class ChatRoom(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    course_id: PyObjectId
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

class MessageCreate(BaseModel):
    text: str
    reply_to: Optional[PyObjectId] = None

    model_config = {
        "arbitrary_types_allowed": True
    }

class MessageResponse(Message):
    sender_name: str
    course_name: str 