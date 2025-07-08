"""
Database models for the Print Tracking Portal.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from backend.app.models.base import BaseModel


class Company(BaseModel):
    """Company/Organization model for multi-tenant support."""
    
    __tablename__ = "companies"
    
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True)
    logo_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sites = relationship("Site", back_populates="company")
    users = relationship("User", back_populates="company")


class Site(BaseModel):
    """Site/Location model for multi-site support."""
    
    __tablename__ = "sites"
    
    site_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    company = relationship("Company", back_populates="sites")
    agents = relationship("Agent", back_populates="site")
    print_jobs = relationship("PrintJob", back_populates="site")


class User(BaseModel):
    """User model with LDAP support."""
    
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))  # For local users
    role = Column(String(50), default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    is_ldap_user = Column(Boolean, default=False)
    ldap_dn = Column(String(500))  # LDAP Distinguished Name
    last_login = Column(DateTime(timezone=True))
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    print_jobs = relationship("PrintJob", back_populates="user")


class Agent(BaseModel):
    """Windows agent model for tracking client PCs."""
    
    __tablename__ = "agents"
    
    pc_name = Column(String(255), nullable=False, index=True)
    pc_ip = Column(String(45))  # IPv4/IPv6
    username = Column(String(100), nullable=False, index=True)
    agent_version = Column(String(50))
    os_version = Column(String(255))
    api_key = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="offline")  # online, offline, error
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_job_submitted = Column(DateTime(timezone=True))
    total_jobs_submitted = Column(Integer, default=0)
    pending_jobs = Column(Integer, default=0)
    config_version = Column(Integer, default=1)
    installed_printers = Column(Text)  # JSON array of printer names
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="agents")
    print_jobs = relationship("PrintJob", back_populates="agent")


class Printer(BaseModel):
    """Printer model for tracking printer information."""
    
    __tablename__ = "printers"
    
    name = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), index=True)
    location = Column(String(255))
    model = Column(String(255))
    is_color = Column(Boolean, default=False)
    is_duplex_capable = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    
    # Relationships
    site = relationship("Site")
    print_jobs = relationship("PrintJob", back_populates="printer")


class PrintJob(BaseModel):
    """Print job model - core data structure."""
    
    __tablename__ = "print_jobs"
    
    # User and location information
    username = Column(String(100), nullable=False, index=True)
    pc_name = Column(String(255), nullable=False, index=True)
    
    # Printer information
    printer_name = Column(String(255), nullable=False, index=True)
    printer_ip = Column(String(45))
    
    # Document information
    document_name = Column(String(500), nullable=False)
    pages = Column(Integer, nullable=False)
    copies = Column(Integer, default=1)
    total_pages = Column(Integer, nullable=False)  # pages * copies
    
    # Print settings
    is_duplex = Column(Boolean, default=False)
    is_color = Column(Boolean, default=False)
    
    # Timestamps
    print_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metadata
    agent_version = Column(String(50))
    job_size_bytes = Column(Integer)  # Document size in bytes
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    printer_id = Column(Integer, ForeignKey("printers.id"))
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="print_jobs")
    agent = relationship("Agent", back_populates="print_jobs")
    printer = relationship("Printer", back_populates="print_jobs")
    site = relationship("Site", back_populates="print_jobs")


class AuditLog(BaseModel):
    """Audit log for tracking system actions."""
    
    __tablename__ = "audit_logs"
    
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # user, agent, print_job, etc.
    entity_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    details = Column(Text)  # JSON with additional details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Relationships
    user = relationship("User")


class SystemConfig(BaseModel):
    """System configuration key-value store."""
    
    __tablename__ = "system_config"
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(500))
    is_public = Column(Boolean, default=False)  # Can be read by non-admin users
