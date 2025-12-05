from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator


class UserCreate(BaseModel):
    username: str
    password: str
    role: str

    @validator("username")
    def validate_username(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username cannot exceed 50 characters")
        return v.strip()

    @validator("password")
    def validate_password(cls, v: str) -> str:
        if not v or len(v) == 0:
            raise ValueError("Password cannot be empty")
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters")
        return v

    @validator("role")
    def validate_role(cls, v: str) -> str:
        if v not in ["admin", "waiter"]:
            raise ValueError("Role must be either 'admin' or 'waiter'")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    role: str


class DishCreate(BaseModel):
    name: str
    description: str
    price: float

    @validator("name")
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Dish name cannot be empty")
        if len(v) > 100:
            raise ValueError("Dish name cannot exceed 100 characters")
        return v.strip()

    @validator("price")
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 1000000:
            raise ValueError("Price is too high")
        return round(v, 2)


class DishResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available: bool


class OrderItemCreate(BaseModel):
    dish_id: int
    quantity: int

    @validator("quantity")
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        if v > 100:
            raise ValueError("Quantity cannot exceed 100")
        return v


class OrderItemResponse(BaseModel):
    id: int
    dish_id: int
    dish_name: str
    dish_price: float
    quantity: int


class OrderCreate(BaseModel):
    table_number: int
    items: List[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    code: Optional[str] = None
    table_number: int
    status: str
    created_at: datetime
    waiter_id: int
    waiter_name: str
    items: List[OrderItemResponse]


class OrderUpdate(BaseModel):
    table_number: Optional[int] = None
    status: Optional[str] = None
    items: Optional[List[OrderItemCreate]] = None


class TableResponse(BaseModel):
    id: int
    number: int
    is_available: bool
    current_order_id: Optional[int]


class RestaurantConfigUpdate(BaseModel):
    total_tables: int

    @validator("total_tables")
    def validate_total_tables(cls, v: int) -> int:
        if v < 1:
            raise ValueError("количество столов не может быть меньше 1")
        if v > 100:
            raise ValueError("Количество столов не может превышать 100")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v: str) -> str:
        if not v or len(v) == 0:
            raise ValueError("Password cannot be empty")
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters")
        return v


