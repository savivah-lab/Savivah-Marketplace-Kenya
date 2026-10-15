from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ForgotData(BaseModel):
    email: EmailStr


class ResetData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  # Pydantic v2

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(alias="newPassword", min_length=8)
