from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class VehicleCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=60)

    price: Decimal = Field(
        ge=0,
        max_digits=11,
        decimal_places=2,
    )

    quantity: int = Field(
        strict=True,
        ge=0,
        le=1000000,
    )


class VehicleResponse(VehicleCreate):
    id: str
class StockChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(
        strict=True,
        gt=0,
        le=1000000,
    )

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()


class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool