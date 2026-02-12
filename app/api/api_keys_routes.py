from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import APIKey
from app.auth import generate_api_key
from app.schemas import APIResponse
from app.core.config import settings
import os

router = APIRouter(prefix="/admin/api-keys", tags=["Admin - API Keys"])

# ADMIN_SECRET = os.getenv("ADMIN_SECRET")

def verify_admin(admin_secret: str):
    if admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Non autorisé")


@router.post("/create", response_model=APIResponse)
async def create_api_key(
    name: str,
    owner_email: str,
    expires_in_days: int = None,
    rate_limit: int = 1000,
    admin_secret: str = None,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_secret)
    
    key = generate_api_key()
    
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    api_key = APIKey(
        key=key,
        name=name,
        owner_email=owner_email,
        expires_at=expires_at,
        rate_limit=rate_limit
    )
    
    db.add(api_key)
    await db.commit()
    
    return APIResponse(
        success=True,
        data={
            "api_key": key,
            "name": name,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    )


@router.get("", response_model=APIResponse)
async def list_api_keys(
    admin_secret: str = None,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_secret)
    
    query = select(APIKey)
    result = await db.execute(query)
    keys = result.scalars().all()
    
    keys_data = [
        {
            "id": k.id,
            "name": k.name,
            "owner_email": k.owner_email,
            "api_key" : k.key,
            "is_active": k.is_active,
            "request_count": k.request_count,
            "created_at": k.created_at.isoformat(),
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None
        }
        for k in keys
    ]
    
    return APIResponse(success=True, data={"api_keys": keys_data})


@router.delete("/{key_id}", response_model=APIResponse)
async def revoke_api_key(
    key_id: int,
    admin_secret: str = None,
    db: AsyncSession = Depends(get_db)
):
    verify_admin(admin_secret)
    
    query = select(APIKey).where(APIKey.id == key_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key non trouvée")
    
    api_key.is_active = False
    await db.commit()
    
    return APIResponse(success=True, data={"message": "API Key révoquée"})