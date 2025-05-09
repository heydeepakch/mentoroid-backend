from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Any
from models.user import User, UserInDB
from utils.auth import get_current_user, check_admin_permission
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

router = APIRouter()

@router.get("/", response_model=List[User])
async def list_users(
    request: Request,
    current_user: User = Depends(check_admin_permission)
) -> Any:
    """
    List all users (admin only).
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    users = await db.users.find().to_list(length=None)
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific user.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to view their own profile or admins to view any profile
    if str(user["_id"]) != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_in: UserInDB,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a user.
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to update their own profile or admins to update any profile
    if str(user["_id"]) != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update user
    update_data = user_in.dict(exclude_unset=True)
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return updated_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(check_admin_permission)
) -> Any:
    """
    Delete a user (admin only).
    """
    db: AsyncIOMotorDatabase = request.app.mongodb
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    await db.users.delete_one({"_id": ObjectId(user_id)})
    
    return {"message": "User deleted successfully"} 