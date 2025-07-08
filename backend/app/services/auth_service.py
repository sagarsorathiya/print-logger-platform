"""
Authentication service for handling user login and token management.
"""

from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.models import User


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if user.is_ldap_user:
            # For LDAP users, we would normally check against LDAP
            # For now, just allow any password for demo purposes
            return user
        
        if not user.hashed_password:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_access_token(self, data: dict) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        payload = self.verify_token(token)
        username = payload.get("sub")
        
        user = self.db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def create_demo_users(self):
        """Create demo users for testing."""
        # Check if admin user exists
        admin = self.db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Get the first company
            from backend.app.models.models import Company
            company = self.db.query(Company).first()
            if company:
                admin_user = User(
                    username="admin",
                    email="admin@acme.com",
                    full_name="Administrator",
                    hashed_password=self.get_password_hash("admin123"),
                    role="admin",
                    company_id=company.id,
                    is_active=True,
                    is_ldap_user=False
                )
                self.db.add(admin_user)
                self.db.commit()
                self.db.refresh(admin_user)
                print("✅ Created demo admin user: admin/admin123")
