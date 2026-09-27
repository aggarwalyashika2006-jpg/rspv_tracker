from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=100,
    )

    role: str = "ATTENDEE"


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class UserResponse(BaseModel):

    id: int

    name: str

    email: EmailStr

    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):

    access_token: str

    token_type: str

    user: UserResponse


class EventCreate(BaseModel):

    event_name: str

    description: Optional[str] = None

    event_type: str = "Workshop"

    event_date: str

    start_time: str

    end_time: str

    venue: Optional[str] = None

    online_link: Optional[str] = None

    maximum_capacity: int = Field(
        gt=0,
        le=100000,
    )

    registration_deadline: Optional[str] = None


class EventResponse(BaseModel):

    id: int

    organizer_id: int

    event_name: str

    description: Optional[str]

    event_type: str

    event_date: str

    start_time: str

    end_time: str

    venue: Optional[str]

    online_link: Optional[str]

    maximum_capacity: int

    registration_deadline: Optional[str]

    status: str

    class Config:
        from_attributes = True