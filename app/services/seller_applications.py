import os
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.seller_application import SellerApplication
from models.user import User

# Merchant references for seller fees start with this, so the Pesapal
# callback/IPN handlers can tell them apart from order payments ("SVH-...").
MERCHANT_REF_PREFIX = "SVA-"


def registration_fee() -> float:
    """Seller registration fee in KES, set via the SELLER_REGISTRATION_FEE_KES env var."""
    try:
        fee = float(os.getenv("SELLER_REGISTRATION_FEE_KES", ""))
    except ValueError:
        fee = 0.0
    if fee <= 0:
        raise HTTPException(status_code=503, detail="Seller registration is not open yet")
    return fee


async def latest_application(db: AsyncSession, user_id) -> Optional[SellerApplication]:
    result = await db.execute(
        select(SellerApplication)
        .where(SellerApplication.user_id == user_id)
        .order_by(SellerApplication.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def seller_status_for_user(db: AsyncSession, user: User) -> str:
    """'none' | 'pending_payment' | 'pending_review' | 'approved' | 'rejected'"""
    if user.role == "seller":
        return "approved"
    application = await latest_application(db, user.id)
    return application.status if application else "none"


async def mark_application_paid(db: AsyncSession, merchant_reference: str) -> bool:
    """
    Call this from the Pesapal IPN handler AFTER it has confirmed with Pesapal
    that the payment is COMPLETED. Returns True if the reference belongs to a
    seller application (so the caller knows it has been handled), else False.
    Safe to call more than once for the same payment.
    """
    application = (await db.execute(
        select(SellerApplication)
        .where(SellerApplication.pesapal_merchant_reference == merchant_reference)
        .with_for_update()
    )).scalar_one_or_none()
    if application is None:
        return False
    if application.status == "pending_payment":
        application.status = "pending_review"
        await db.commit()
    return True
