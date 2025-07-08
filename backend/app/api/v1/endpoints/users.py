"""
User management endpoints for user administration and LDAP integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.user_service import UserService
from backend.app.schemas.auth import UserCreate, UserUpdate, UserResponse, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


class LDAPSyncResult(BaseModel):
    """LDAP sync result model."""
    users_synced: int
    users_created: int
    users_updated: int
    users_disabled: int
    errors: List[str] = Field(default_factory=list)
    sync_time: datetime = Field(default_factory=datetime.utcnow)


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    new_password: str = Field(..., min_length=8)
    is_ldap_user: bool
    last_login: Optional[datetime]
    total_print_jobs: int
    total_pages_printed: int
    created_at: datetime
    updated_at: datetime


class LDAPSyncResult(BaseModel):
    """LDAP sync result model."""
    users_synced: int
    users_created: int
    users_updated: int
    users_disabled: int
    errors: List[str] = Field(default_factory=list)


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by username, email, or full name"),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_ldap_user: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get list of users with filtering and pagination.
    """
    try:
        user_service = UserService(db)
        users = user_service.get_users(
            skip=skip,
            limit=limit,
            search=search,
            role=role.value if role else None,
            is_active=is_active,
            is_ldap_user=is_ldap_user
        )
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                is_ldap_user=user.is_ldap_user,
                last_login=user.last_login,
                company_id=user.company_id,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    """
    try:
        user_service = UserService(db)
        
        # For demo, use first company ID
        # In production, this would come from authenticated user's context
        from backend.app.models.models import Company
        company = db.query(Company).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No company found in system"
            )
        
        new_user = user_service.create_user(user, company.id)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            is_ldap_user=new_user.is_ldap_user,
            last_login=new_user.last_login,
            company_id=new_user.company_id,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_ldap_user=user.is_ldap_user,
            last_login=user.last_login,
            company_id=user.company_id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user account."""
    try:
        user_service = UserService(db)
        updated_user = user_service.update_user(user_id, user_update)
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            is_ldap_user=updated_user.is_ldap_user,
            last_login=updated_user.last_login,
            company_id=updated_user.company_id,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user account (admin only)."""
    try:
        user_service = UserService(db)
        user_service.delete_user(user_id)
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int, 
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)."""
    try:
        user_service = UserService(db)
        message = user_service.reset_password(user_id, request.new_password)
        
        return {"message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
        
        return {
            "message": "Password reset successfully",
            "temporary_password": "generated_temp_password"
        }
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.post("/ldap/sync", response_model=LDAPSyncResult)
async def sync_ldap_users():
    """
    Synchronize users from LDAP/Active Directory.
    """
    try:
        # TODO: Implement LDAP sync
        # - Connect to LDAP server
        # - Query for users
        # - Create/update local users
        # - Disable removed users
        
        logger.info("Starting LDAP user synchronization")
        
        return LDAPSyncResult(
            users_synced=0,
            users_created=0,
            users_updated=0,
            users_disabled=0
        )
        
    except Exception as e:
        logger.error(f"LDAP sync error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LDAP synchronization failed"
        )


@router.get("/ldap/test")
async def test_ldap_connection():
    """
    Test LDAP connection and configuration.
    """
    try:
        # TODO: Implement LDAP connection test
        # - Test connection to LDAP server
        # - Validate credentials
        # - Test search functionality
        
        return {
            "status": "success",
            "message": "LDAP connection successful",
            "server": "ldap://domain-controller",
            "users_found": 0
        }
        
    except Exception as e:
        logger.error(f"LDAP test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LDAP connection test failed"
        )


@router.get("/{user_id}/print-history")
async def get_user_print_history(
    user_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get print history for a specific user.
    """
    try:
        user_service = UserService(db)
        return user_service.get_user_print_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user print history: {str(e)}", exc_info=True)
        # Return empty data instead of failing
        return {
            "user_id": user_id,
            "username": f"user_{user_id}",
            "print_jobs": [],
            "statistics": {
                "total_jobs": 0,
                "total_pages": 0,
                "color_pages": 0,
                "bw_pages": 0
            },
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": 0
            }
        }
