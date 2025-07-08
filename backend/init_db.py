"""
Initialize database and create tables.
"""

from backend.app.core.database import engine, Base
from backend.app.models import models  # Import to register models


def init_database():
    """Initialize database and create all tables."""
    print("Creating database tables...")
    
    # Import all models to ensure they're registered
    from backend.app.models.models import (
        Company, Site, User, Agent, Printer, PrintJob, AuditLog, SystemConfig
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # Print table information
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_database()
