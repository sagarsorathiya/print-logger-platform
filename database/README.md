# Database Setup and Migration Scripts

This directory contains database initialization scripts and Alembic migrations for the Print Tracking Portal.

## Structure
- `init_scripts/` - Initial database setup scripts
- `migrations/` - Alembic migration files
- `schemas/` - Database schema definitions

## Setup Instructions

### For SQLite (Development)
```bash
# Initialize database
python -m alembic upgrade head
```

### For PostgreSQL (Production)
```bash
# 1. Create database
createdb printportal

# 2. Set DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@localhost:5432/printportal

# 3. Run migrations
python -m alembic upgrade head
```

## Migration Commands
```bash
# Create new migration
python -m alembic revision --autogenerate -m "Description"

# Apply migrations
python -m alembic upgrade head

# Rollback migration
python -m alembic downgrade -1
```
