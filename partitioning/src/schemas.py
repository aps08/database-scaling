from datetime import date
from pydantic import BaseModel

class OrderCreate(BaseModel):
    order_date: date
    customer_id: int
    amount: float

class OrderResponse(OrderCreate):
    id: int

class UserCreate(BaseModel):
    user_id: int
    username: str
    email: str

class CustomerCreate(BaseModel):
    name: str
    region: str

class CustomerResponse(CustomerCreate):
    id: int
