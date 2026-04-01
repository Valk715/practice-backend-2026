from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

class UserOut(BaseModel):
    id: int
    email: str
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ResourceBase(BaseModel):
    name: str
    description: str
    capacity: int
    equipment: str

class ResourceCreate(ResourceBase):
    pass

class ResourceOut(ResourceBase):
    id: int
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    resource_id: int
    start_time: datetime
    end_time: datetime

class BookingOut(BaseModel):
    id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    class Config:
        from_attributes = True