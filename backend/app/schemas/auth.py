"""
Pydantic schemas for authentication and users.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    admin = "admin"
    user = "user"
    viewer = "viewer"


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(default=False)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    role: UserRole
    company_id: int


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.user
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: Optional[str] = Field(None, min_length=8)
    ldap_dn: Optional[str] = Field(None, max_length=500)
    
    @validator('password')
    def validate_password(cls, v, values):
        # If not LDAP user, password is required
        if not values.get('ldap_dn') and not v:
            raise ValueError('Password is required for non-LDAP users')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    is_ldap_user: bool
    last_login: Optional[datetime]
    company_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Schema for current user information."""
    user_id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    company_name: str
    last_login: Optional[datetime]


class PasswordReset(BaseModel):
    """Schema for password reset."""
    user_id: int
    new_password: str = Field(..., min_length=8)


class LDAPSyncResult(BaseModel):
    """Schema for LDAP synchronization results."""
    users_synced: int
    users_created: int
    users_updated: int
    users_disabled: int
    errors: list[str] = Field(default_factory=list)
    sync_time: datetime = Field(default_factory=datetime.utcnow)
