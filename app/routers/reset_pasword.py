import hmac
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.security import hash_password
from models.user import User
from models.password_reset import PasswordResetCode
from schemas.reset_password import ForgotData, ResetData
# from services.email import send_email   # use whatever sends your verification email

router = APIRouter(prefix="/api/reset", tags=["reset"])

CODE_TTL_MINUTES = 15
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
GENERIC_OK = {"message": "If an account exists for that email, a reset code has been sent."}
SECRET = os.environ["SECRET_KEY"]


def _hash_code(email: str, code: str) -> str:
    return hmac.new(SECRET.encode(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


@router.post("/request")
async def forgot_password(data: ForgotData, db: AsyncSession = Depends(get_db)):
    email = data.email.lower().strip()
    user = (await db.execute(
        select(User).where(func.lower(User.email) == email)
    )).scalar_one_or_none()

    if not user:
        return GENERIC_OK

    now = datetime.now(timezone.utc)

    last = (await db.execute(
        select(PasswordResetCode)
        .where(PasswordResetCode.email == email)
        .order_by(PasswordResetCode.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if last and (now - last.created_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        return GENERIC_OK

    code = f"{secrets.randbelow(10**6):06d}"

    await db.execute(delete(PasswordResetCode).where(PasswordResetCode.email == email))
    db.add(PasswordResetCode(
        email=email,
        code_hash=_hash_code(email, code),
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    ))
    await db.commit()

    # await send_email(
    #     to=user.email,
    #     subject="Your Savivah password reset code",
    #     body=f"Your code is {code}. It expires in {CODE_TTL_MINUTES} minutes. "
    #          f"If you didn't request this, you can ignore this email.",
    # )
    return GENERIC_OK


@router.post("")
async def reset_password(data: ResetData, db: AsyncSession = Depends(get_db)):
    email = data.email.lower().strip()
    now = datetime.now(timezone.utc)
    invalid = HTTPException(status_code=400, detail="Invalid or expired code")

    record = (await db.execute(
        select(PasswordResetCode).where(PasswordResetCode.email == email)
    )).scalar_one_or_none()

    if not record or record.expires_at < now:
        raise invalid

    if record.attempts >= MAX_ATTEMPTS:
        await db.execute(delete(PasswordResetCode).where(PasswordResetCode.email == email))
        await db.commit()
        raise invalid

    if not hmac.compare_digest(record.code_hash, _hash_code(email, data.code)):
        record.attempts += 1
        await db.commit()
        raise invalid

    await db.execute(
        update(User)
        .where(func.lower(User.email) == email)
        .values(password_hash=hash_password(data.new_password))
    )
    await db.execute(delete(PasswordResetCode).where(PasswordResetCode.email == email))
    await db.commit()
    return {"message": "Password has been reset successfully"}
