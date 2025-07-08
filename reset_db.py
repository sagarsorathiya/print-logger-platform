"""
Reset database script - drops and recreates all tables
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from backend.app.core.database import engine, Base
from backend.app.models import models  # Import to register models
from backend.app.utils.seeder import seed_sample_data

def main():
    print("Dropping existing database tables...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped successfully!")
    
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    # Seed the database
    print("Seeding database with sample data...")
    seed_sample_data()
    print("Database reset and seeded successfully!")

if __name__ == "__main__":
    main()
