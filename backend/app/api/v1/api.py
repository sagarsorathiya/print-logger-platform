"""
API v1 Router

Main router that includes all API endpoints.
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, print_jobs, agents, reports, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(print_jobs.router, prefix="/print-jobs", tags=["Print Jobs"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
