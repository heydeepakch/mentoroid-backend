from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from typing import List, Any, Dict
from models.chat import Message, ChatRoom, MessageCreate, MessageResponse
from models.user import User
from utils.auth import get_current_user, check_teacher_permission
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import json
from datetime import datetime

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, course_id: str):
        await websocket.accept()
        if course_id not in self.active_connections:
            self.active_connections[course_id] = []
        self.active_connections[course_id].append(websocket)

    def disconnect(self, websocket: WebSocket, course_id: str):
        if course_id in self.active_connections:
            self.active_connections[course_id].remove(websocket)
            if not self.active_connections[course_id]:
                del self.active_connections[course_id]

    async def broadcast(self, message: str, course_id: str):
        if course_id in self.active_connections:
            for connection in self.active_connections[course_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{course_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    course_id: str,
    request: Request
):
    await manager.connect(websocket, course_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save message to database
            db: AsyncIOMotorDatabase = request.app.mongodb
            message = Message(
                course_id=ObjectId(course_id),
                sender_id=ObjectId(message_data["sender_id"]),
                text=message_data["text"],
                reply_to=ObjectId(message_data["reply_to"]) if message_data.get("reply_to") else None
            )
            
            result = await db.messages.insert_one(message.dict(by_alias=True))
            message.id = result.inserted_id
            
            # Get sender and course info for the response
            sender = await db.users.find_one({"_id": message.sender_id})
            course = await db.courses.find_one({"_id": message.course_id})
            
            response = MessageResponse(
                **message.dict(by_alias=True),
                sender_name=sender["name"],
                course_name=course["title"]
            )
            
            # Broadcast to all connections in the course
            await manager.broadcast(response.json(), course_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, course_id)

@router.post("/rooms", response_model=ChatRoom)
async def create_chat_room(
    room: ChatRoom,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Create a new chat room for a course.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Verify course exists and user is the teacher
    course = await db.courses.find_one({"_id": ObjectId(room.course_id)})
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
    
    result = await db.chat_rooms.insert_one(room.dict(by_alias=True))
    room.id = result.inserted_id
    
    return room

@router.get("/rooms/{course_id}", response_model=List[ChatRoom])
async def list_chat_rooms(
    course_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all chat rooms for a course.
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
    
    rooms = await db.chat_rooms.find(
        {"course_id": ObjectId(course_id)}
    ).to_list(length=None)
    
    return rooms

@router.get("/messages/{course_id}", response_model=List[MessageResponse])
async def get_messages(
    course_id: str,
    limit: int = 50,
    request: Request = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get recent messages for a course.
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
    
    # Get messages with sender and course info
    pipeline = [
        {"$match": {"course_id": ObjectId(course_id)}},
        {"$sort": {"timestamp": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "sender_id",
                "foreignField": "_id",
                "as": "sender"
            }
        },
        {"$unwind": "$sender"},
        {
            "$project": {
                "_id": 1,
                "course_id": 1,
                "sender_id": 1,
                "text": 1,
                "timestamp": 1,
                "is_pinned": 1,
                "reply_to": 1,
                "sender_name": "$sender.name",
                "course_name": course["title"]
            }
        }
    ]
    
    messages = await db.messages.aggregate(pipeline).to_list(length=None)
    return messages

@router.post("/messages/{course_id}/pin/{message_id}")
async def pin_message(
    course_id: str,
    message_id: str,
    request: Request,
    current_user: User = Depends(check_teacher_permission)
) -> Any:
    """
    Pin a message in a course chat.
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
    
    # Update message
    result = await db.messages.update_one(
        {"_id": ObjectId(message_id), "course_id": ObjectId(course_id)},
        {"$set": {"is_pinned": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {"message": "Message pinned successfully"} 