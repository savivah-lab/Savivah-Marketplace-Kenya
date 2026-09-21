import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SellerApplicationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    fullName: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phoneNumber: str = Field(min_length=7, max_length=20)
    identificationType: Literal["national_id", "passport"]
    identificationNumber: str = Field(min_length=4, max_length=50)
    businessName: str = Field(min_length=2, max_length=160)
    businessRegistrationNumber: Optional[str] = Field(default=None, max_length=60)
    productPermit: str = Field(min_length=2, max_length=120)


class SellerApplicationResponse(BaseModel):
    message: str
    applicationId: uuid.UUID
    status: str
    redirectUrl: str


class SellerApplicationStatus(BaseModel):
    status: str
    submittedAt: Optional[datetime] = None
    reviewerNote: Optional[str] = None
