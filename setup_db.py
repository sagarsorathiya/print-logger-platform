"""
Database initialization script with proper path setup
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the database initialization
from backend.app.core.database import engine, Base
from backend.app.models import models  # Import to register models
from backend.app.utils.seeder import seed_sample_data

def main():
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    # Seed the database
    print("Seeding database with sample data...")
    seed_sample_data()
    print("Database seeded successfully!")

if __name__ == "__main__":
    main()
