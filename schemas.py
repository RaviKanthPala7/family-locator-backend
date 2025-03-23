from pydantic import BaseModel, EmailStr
from datetime import datetime

# User Schema for Registration
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


# Response Schema for User
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        orm_mode = True

# Schema for Adding Location
class LocationCreate(BaseModel):
    latitude: float
    longitude: float

# Response Schema for Location Retrieval
class LocationResponse(BaseModel):
    id: int
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        orm_mode = True
