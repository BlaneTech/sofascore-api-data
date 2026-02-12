from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.database import get_db
import secrets
import os

ADMIN_SECRET = os.getenv("ADMIN_SECRET")
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER), db: AsyncSession = Depends(get_db)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key manquante"
        )
    
    from app.db.models import APIKey
    
    query = select(APIKey).where(
        APIKey.key == api_key,
        APIKey.is_active == True
    )
    result = await db.execute(query)
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key invalide"
        )
    
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key expirée"
        )
    
    api_key_obj.last_used_at = datetime.utcnow()
    api_key_obj.request_count += 1
    await db.commit()
    
    return api_key_obj


def generate_api_key():
    return f"goga_{secrets.token_urlsafe(32)}"