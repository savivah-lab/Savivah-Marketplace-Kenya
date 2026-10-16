from fastapi import APIRouter, Depends, HTTPException
from schemas.reset_password import ForgotData
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import hash_password
from sqlalchemy import select, update
from core.db import get_db
from models.user import User

router=APIRouter(prefix="/api/reset", tags=["reset"])
@router.post("")
async def reset(userdata:ForgotData, db: AsyncSession=Depends(get_db)):
    data=(await db.execute(select(User).where (User.email==userdata.email))).scalar_one_or_none()
    if not data:
        raise HTTPException(status_code=404, detail="Not Found")
    passwordhash=hash_password(userdata.password)
    await db.execute(update(User).where(User.email==data.email).values(password_hash=passwordhash))
    await db.commit()
    message="Password has been reset Successfully"
    return message
    
