from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    id: int
    name: str
    email: EmailStr
    country: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    country: str
    created_at: datetime
    target_shard: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserScatterGatherResponse(BaseModel):
    id: int
    name: str
    email: str
    country: str
    located_on_shard: int


class OrderCreate(BaseModel):
    user_id: int
    amount: float
    status: Optional[str] = "completed"


class OrderResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime
    target_shard: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
