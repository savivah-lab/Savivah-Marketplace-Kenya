from pydantic import BaseModel
import uuid

class AdminLoginRequest(BaseModel):
    email: EmailStr
    fullName: str
    password: str
    totpCode: str | None = None  # required once 2FA is enabled for the admin account


class AdminOut(BaseModel):
    id: uuid.UUID
    fullName: str
    email: str


class AdminTokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    admin: AdminOut
    class config:
        from_attributes=True

class AdminStats(BaseModel):
    commission_earned: float
    in_escrow: float
    total_orders: int


class SellerSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    verified: bool
    owner_name: str
    owner_email: str
    pending_escrow: float
    total_earned: float
    total_orders: int
    class config:
        from_attributes=True


class DisputeResolveRequest(BaseModel):
    resolution: str  # "refund" | "release" | "reject"
