"""
Database Configuration and Connection Management

Supports both PostgreSQL and SQLite databases with async operations.
"""

import logging
from typing import Optional
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Database URL processing
DATABASE_URL = settings.DATABASE_URL

# Handle SQLite async compatibility
if DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Create database instance
database = Database(DATABASE_URL)

# Create SQLAlchemy engine (sync for table creation)
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import the base from models
from backend.app.models.base import Base

# Create metadata
metadata = Base.metadata


# Database dependency for FastAPI
async def get_database() -> Database:
    """Get database connection."""
    return database


# FastAPI database dependency
def get_db():
    """Get database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Session dependency for SQLAlchemy ORM
def get_db_session():
    """Get database session for ORM operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def connect_database():
    """Connect to the database."""
    try:
        await database.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def disconnect_database():
    """Disconnect from the database."""
    try:
        await database.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {e}")


def create_tables():
    """Create all database tables using sync engine."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
