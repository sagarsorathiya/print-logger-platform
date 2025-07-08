#!/usr/bin/env python3
"""
Setup Validation Script

Validates that the print tracking portal is correctly configured and running.
"""

import sys
import asyncio
import httpx
from pathlib import Path
import sqlite3
from backend.app.core.config import settings
from backend.app.core.database import database


async def validate_configuration():
    """Validate configuration settings."""
    print("🔧 Validating Configuration...")
    
    # Check secret key
    if len(settings.SECRET_KEY) < 32:
        print("❌ SECRET_KEY is too short (must be at least 32 characters)")
        return False
    else:
        print("✅ SECRET_KEY is properly configured")
    
    # Check database URL
    print(f"✅ Database URL: {settings.DATABASE_URL}")
    
    # Check required directories
    required_dirs = ["logs", "static", "uploads", "agent_cache"]
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
            return False
    
    return True


async def validate_database():
    """Validate database connectivity and structure."""
    print("\n🗄️ Validating Database...")
    
    try:
        # Test database connection
        await database.connect()
        print("✅ Database connection successful")
        
        # Check if tables exist
        if "sqlite" in settings.DATABASE_URL:
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if Path(db_path).exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for required tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["users", "print_jobs", "printers", "sites"]
                for table in required_tables:
                    if table in tables:
                        print(f"✅ Table exists: {table}")
                    else:
                        print(f"❌ Missing table: {table}")
                        return False
                
                conn.close()
            else:
                print(f"❌ Database file not found: {db_path}")
                return False
        
        await database.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        return False


async def validate_api():
    """Validate API endpoints."""
    print("\n🌐 Validating API...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://127.0.0.1:8000/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health endpoint working: {data['status']}")
                print(f"   Version: {data['version']}")
                print(f"   Service: {data['service']}")
                return True
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ API validation failed: {e}")
        print("   Make sure the server is running: python -m uvicorn backend.main:app --reload")
        return False


async def main():
    """Main validation function."""
    print("🚀 Print Tracking Portal - Setup Validation")
    print("=" * 50)
    
    validation_results = []
    
    # Run validations
    validation_results.append(await validate_configuration())
    validation_results.append(await validate_database())
    validation_results.append(await validate_api())
    
    # Summary
    print("\n📊 Validation Summary")
    print("=" * 50)
    
    if all(validation_results):
        print("🎉 All validations passed! Your setup is ready.")
        print("\n🚀 Next steps:")
        print("   1. Start the API server: python -m uvicorn backend.main:app --reload")
        print("   2. Open the web portal: http://localhost:8080")
        print("   3. View API docs: http://localhost:8000/docs")
        print("   4. Deploy the Windows agent to client machines")
        sys.exit(0)
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
