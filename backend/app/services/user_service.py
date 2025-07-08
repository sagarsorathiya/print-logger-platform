"""
User management service for CRUD operations and user administration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from fastapi import HTTPException, status

from backend.app.models.models import User, Company, PrintJob
from backend.app.schemas.auth import UserCreate, UserUpdate, UserResponse
from backend.app.services.auth_service import AuthService


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_ldap_user: Optional[bool] = None,
        company_id: Optional[int] = None
    ) -> List[User]:
        """Get users with filtering and pagination."""
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_ldap_user is not None:
            query = query.filter(User.is_ldap_user == is_ldap_user)
        
        if company_id:
            query = query.filter(User.company_id == company_id)
        
        # Order by username
        query = query.order_by(User.username)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, user_data: UserCreate, company_id: int) -> User:
        """Create a new user."""
        # Check if username already exists
        existing_user = self.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = self.db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Validate company exists
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company ID"
            )
        
        # Create user data
        user_dict = user_data.dict(exclude={'password'})
        user_dict['company_id'] = company_id
        
        # Handle password
        if user_data.password and not user_data.ldap_dn:
            user_dict['hashed_password'] = self.auth_service.get_password_hash(user_data.password)
        
        # Set LDAP flag
        user_dict['is_ldap_user'] = bool(user_data.ldap_dn)
        
        # Create user
        user = User(**user_dict)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email already exists (if being updated)
        if user_update.email and user_update.email != user.email:
            existing_email = self.db.query(User).filter(
                and_(User.email == user_update.email, User.id != user_id)
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (soft delete by deactivating)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def reset_password(self, user_id: int, new_password: str) -> str:
        """Reset user password."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_ldap_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reset password for LDAP users"
            )
        
        # Hash and update password
        user.hashed_password = self.auth_service.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        return "Password reset successfully"
    
    def get_user_print_history(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get print history for a user."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build query
        query = self.db.query(PrintJob).filter(PrintJob.username == user.username)
        
        # Apply date filters
        if start_date:
            query = query.filter(PrintJob.print_time >= start_date)
        if end_date:
            query = query.filter(PrintJob.print_time <= end_date)
        
        # Get total count for statistics
        total_jobs = query.count()
        
        # Calculate statistics
        stats_query = query
        total_pages = stats_query.with_entities(
            func.coalesce(func.sum(PrintJob.total_pages), 0)
        ).scalar() or 0
        
        color_pages = stats_query.with_entities(
            func.coalesce(func.sum(PrintJob.color_pages), 0)
        ).scalar() or 0
        
        bw_pages = total_pages - color_pages
        
        # Get paginated results
        print_jobs = query.order_by(desc(PrintJob.print_time)).offset(skip).limit(limit).all()
        
        return {
            "user_id": user_id,
            "username": user.username,
            "print_jobs": [
                {
                    "id": job.id,
                    "document_name": job.document_name,
                    "printer_name": job.printer_name,
                    "total_pages": job.total_pages,
                    "color_pages": job.color_pages,
                    "print_time": job.print_time,
                    "status": job.status
                }
                for job in print_jobs
            ],
            "statistics": {
                "total_jobs": total_jobs,
                "total_pages": int(total_pages),
                "color_pages": int(color_pages),
                "bw_pages": int(bw_pages)
            },
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_jobs
            }
        }
    
    def get_user_statistics(self) -> List[Dict[str, Any]]:
        """Get user printing statistics."""
        # Query for user statistics
        stats = self.db.query(
            PrintJob.username,
            func.count(PrintJob.id).label('total_jobs'),
            func.coalesce(func.sum(PrintJob.total_pages), 0).label('total_pages'),
            func.coalesce(func.sum(PrintJob.color_pages), 0).label('color_pages'),
            func.max(PrintJob.print_time).label('last_print')
        ).group_by(PrintJob.username).order_by(desc('total_pages')).limit(50).all()
        
        return [
            {
                "username": stat.username,
                "total_jobs": stat.total_jobs,
                "total_pages": int(stat.total_pages),
                "color_pages": int(stat.color_pages),
                "bw_pages": int(stat.total_pages - stat.color_pages),
                "last_print": stat.last_print
            }
            for stat in stats
        ]
