from pydantic import Basemodel
import uuid
class PaymentBase(BaseModel):
    store_id: uuid.UUID
    store_name: str
    amount: float
    method: str | None = None
    payout_account: str | None = None





class PayoutOutResponse(PaymentBase):
    id: uuid.UUID
    status: str

    class Config:
        from_attributes = True
