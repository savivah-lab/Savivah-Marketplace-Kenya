import time
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from deps import get_current_user
from models.user import User
from models.seller_application import SellerApplication
from schemas.seller import SellerApplicationRequest, SellerApplicationResponse, SellerApplicationStatus
from services import pesapal
from services.seller_applications import MERCHANT_REF_PREFIX, latest_application, registration_fee

router = APIRouter(prefix="/api/seller", tags=["seller"])


@router.post("/applications", response_model=SellerApplicationResponse)
async def submit_application(
    body: SellerApplicationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "seller":
        raise HTTPException(status_code=400, detail="This account is already a seller")
    fee = registration_fee()

    existing = await latest_application(db, user.id)
    if existing and existing.status == "pending_review":
        raise HTTPException(status_code=409, detail="Your application is already under review")

    if existing and existing.status == "pending_payment":
        application = existing  # user closed the Pesapal tab earlier: update details and retry payment
    else:
        application = SellerApplication(id=uuid.uuid4(), user_id=user.id, status="pending_payment")
        db.add(application)

    application.full_name = body.fullName
    application.email = body.email
    application.phone_number = body.phoneNumber
    application.identification_type = body.identificationType
    application.identification_number = body.identificationNumber
    application.business_name = body.businessName
    application.business_registration_number = body.businessRegistrationNumber or None
    application.product_permit = body.productPermit
    application.fee_amount = fee

    application_id = application.id
    merchant_reference = f"{MERCHANT_REF_PREFIX}{str(application_id)[:8]}-{int(time.time() * 1000)}"
    application.pesapal_merchant_reference = merchant_reference

    # Commit BEFORE calling Pesapal, same rule as checkout: a Pesapal outage
    # must never lose the application the user just filled in.
    await db.commit()

    first_name, *rest = (body.fullName or "Savivah Seller").split(" ")
    last_name = " ".join(rest) or first_name

    try:
        pesapal_order = await pesapal.submit_order_request(
            merchant_reference=merchant_reference, amount=fee,
            description="Savivah seller registration fee",
            email=body.email, phone=body.phoneNumber, first_name=first_name, last_name=last_name,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Payment provider error: {e}")

    application = (await db.execute(
        select(SellerApplication).where(SellerApplication.id == application_id)
    )).scalar_one()
    application.pesapal_order_tracking_id = pesapal_order["order_tracking_id"]
    await db.commit()

    return SellerApplicationResponse(
        message="Application saved. Complete the registration fee payment on Pesapal to submit it for review.",
        applicationId=application_id,
        status="pending_payment",
        redirectUrl=pesapal_order["redirect_url"],
    )


@router.get("/applications/me", response_model=SellerApplicationStatus)
async def my_application(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role == "seller":
        return SellerApplicationStatus(status="approved")
    application = await latest_application(db, user.id)
    if not application:
        return SellerApplicationStatus(status="none")
    return SellerApplicationStatus(
        status=application.status, submittedAt=application.created_at, reviewerNote=application.reviewer_note,
    )
