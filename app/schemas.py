from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from .models import UserRole, ReportCategory, ReportStatus


# ---------- Auth ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Reports ----------

class ReportCreate(BaseModel):
    category: ReportCategory
    description: str
    latitude: float
    longitude: float
    photo_url: Optional[str] = None


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class ReportOut(BaseModel):
    id: str
    user_id: str
    category: ReportCategory
    description: str
    photo_url: Optional[str]
    latitude: float
    longitude: float
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class StatusHistoryOut(BaseModel):
    old_status: Optional[ReportStatus]
    new_status: ReportStatus
    changed_at: datetime

    class Config:
        from_attributes = True


class ReportDetailOut(ReportOut):
    history: List[StatusHistoryOut] = []
