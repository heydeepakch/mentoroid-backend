from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from ...models.material import Material
from ...models.user import User
from ..dependencies import get_current_user, get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/materials",
    tags=["materials"],
    responses={404: {"description": "Not found"}}
)

@router.post("/", response_model=Material)
async def create_material(
    material: Material,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not current_user.is_instructor and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can create materials"
        )
    
    material.created_by = current_user.id
    material.updated_at = datetime.utcnow()
    result = await db[Material.Collection.name].insert_one(material.model_dump(by_alias=True))
    created_material = await db[Material.Collection.name].find_one({"_id": result.inserted_id})
    return Material.model_validate(created_material)

@router.get("/{material_id}", response_model=Material)
async def get_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    material = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update views count
    await db[Material.Collection.name].update_one(
        {"_id": ObjectId(material_id)},
        {"$inc": {"views": 1}}
    )
    
    return Material.model_validate(material)

@router.get("/course/{course_id}", response_model=List[Material])
async def get_course_materials(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    cursor = db[Material.Collection.name].find({"course_id": ObjectId(course_id)})
    materials = await cursor.to_list(length=None)
    return [Material.model_validate(material) for material in materials]

@router.put("/{material_id}", response_model=Material)
async def update_material(
    material_id: str,
    material_update: Material,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    existing = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if str(existing["created_by"]) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator or admin can update materials"
        )
    
    material_update.id = ObjectId(material_id)
    material_update.updated_at = datetime.utcnow()
    update_data = material_update.model_dump(by_alias=True)
    
    await db[Material.Collection.name].update_one(
        {"_id": ObjectId(material_id)},
        {"$set": update_data}
    )
    
    updated = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    return Material.model_validate(updated)

@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    material = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if str(material["created_by"]) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator or admin can delete materials"
        )
    
    await db[Material.Collection.name].delete_one({"_id": ObjectId(material_id)})
    return {"message": "Material deleted successfully"}

@router.post("/{material_id}/like")
async def toggle_like_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    material = await db[Material.Collection.name].find_one({"_id": ObjectId(material_id)})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    liked_by = material.get("liked_by", [])
    user_id_str = str(current_user.id)
    
    if user_id_str in liked_by:
        # Unlike
        await db[Material.Collection.name].update_one(
            {"_id": ObjectId(material_id)},
            {
                "$pull": {"liked_by": user_id_str},
                "$inc": {"likes": -1}
            }
        )
        return {"message": "Material unliked successfully"}
    else:
        # Like
        await db[Material.Collection.name].update_one(
            {"_id": ObjectId(material_id)},
            {
                "$addToSet": {"liked_by": user_id_str},
                "$inc": {"likes": 1}
            }
        )
        return {"message": "Material liked successfully"} 