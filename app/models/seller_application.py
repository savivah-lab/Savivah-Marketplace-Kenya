"""
A customer's application to become a seller. One row per application; the
latest row for a user decides their sellerStatus.

Status flow:
    pending_payment -> pending_review -> approved | rejected
A rejected user may apply again (creates a new row).
"""
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base
from models.user import User


class SellerApplication(Base):
    __tablename__ = "seller_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Reuse the exact type and table of users.id so the foreign key always matches.
    user_id = Column(User.__table__.c.id.type, ForeignKey(User.__table__.c.id), nullable=False, index=True)

    full_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    identification_type = Column(String(20), nullable=False)      # national_id | passport
    identification_number = Column(String(50), nullable=False)   # sensitive: never return in API responses
    business_name = Column(String(160), nullable=False)
    business_registration_number = Column(String(60), nullable=True)
    product_permit = Column(String(120), nullable=False)

    status = Column(String(30), nullable=False, default="pending_payment", index=True)
    fee_amount = Column(Numeric(10, 2), nullable=False)
    pesapal_merchant_reference = Column(String(64), unique=True, index=True, nullable=True)
    pesapal_order_tracking_id = Column(String(64), nullable=True)
    reviewer_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
