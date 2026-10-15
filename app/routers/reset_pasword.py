from fastapi import APIRouter, Depends, HTTPException
from schemas.reset_password import resetdata 
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import hash_password
from sqlalchemy import select, update
from core.db import get_db
from models.user import User

router=APIRouter(prefix="/api/reset", tags=["reset"])
@router.post("")
async def reset(data:resetdata, db: AsyncSession=Depends(get_db)):
    data=(await db.execute(select(User).where (User.email==data.email))).scalar_one_or_none()
    if not data:
        return data
        raise HTTPException(status_code=404, detail="Not Found")
    password_hash=hash_password(data.password)
    await db.execute(update(User).where(User.email==data.email).values(password_hash=password_hash))
    await db.commit()
