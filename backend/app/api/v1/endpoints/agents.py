"""
Agent management endpoints for monitoring and configuring Windows print agents.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.models import Agent, Site, Company

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRegistration(BaseModel):
    """Agent registration model."""
    pc_name: str
    pc_ip: str
    username: str
    site_id: str
    company_name: str
    agent_version: str
    os_version: str
    installed_printers: List[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Agent configuration model."""
    api_url: str
    api_key: str
    update_interval: int = Field(default=300, description="Update interval in seconds")
    log_level: str = Field(default="INFO")
    offline_cache_days: int = Field(default=7)
    max_log_size_mb: int = Field(default=100)
    site_id: str
    company_name: str


class AgentStatus(BaseModel):
    """Agent status model."""
    id: int
    pc_name: str
    pc_ip: str
    username: str
    site_id: str
    company_name: str
    agent_version: str
    os_version: str
    status: str  # online, offline, error
    last_seen: datetime
    last_job_submitted: Optional[datetime]
    total_jobs_submitted: int
    pending_jobs: int
    installed_printers: List[str]
    config_version: int
    created_at: datetime


class AgentUpdate(BaseModel):
    """Agent update information."""
    current_version: str
    latest_version: str
    update_available: bool
    update_url: Optional[str]
    release_notes: Optional[str]


@router.post("/register", response_model=dict)
async def register_agent(agent: AgentRegistration, db: Session = Depends(get_db)):
    """
    Register a new agent or update existing agent information.
    """
    try:
        logger.info(f"Agent registration: {agent.pc_name} from {agent.site_id}")
        
        # Find or create site
        site = db.query(Site).filter(Site.site_id == agent.site_id).first()
        if not site:
            # Create company if it doesn't exist
            company = db.query(Company).filter(Company.name == agent.company_name).first()
            if not company:
                company = Company(name=agent.company_name)
                db.add(company)
                db.flush()
            
            # Create site
            site = Site(
                site_id=agent.site_id,
                name=f"Site {agent.site_id}",
                company_id=company.id
            )
            db.add(site)
            db.flush()
        
        # Check if agent already exists
        existing_agent = db.query(Agent).filter(
            Agent.pc_name == agent.pc_name,
            Agent.site_id == site.id
        ).first()
        
        if existing_agent:
            # Update existing agent
            existing_agent.pc_ip = agent.pc_ip
            existing_agent.username = agent.username
            existing_agent.agent_version = agent.agent_version
            existing_agent.os_version = agent.os_version
            existing_agent.last_seen = datetime.utcnow()
            existing_agent.status = "online"
            agent_record = existing_agent
        else:
            # Create new agent
            import secrets
            api_key = secrets.token_urlsafe(32)
            
            agent_record = Agent(
                pc_name=agent.pc_name,
                pc_ip=agent.pc_ip,
                username=agent.username,
                site_id=site.id,
                agent_version=agent.agent_version,
                os_version=agent.os_version,
                api_key=api_key,
                status="online",
                last_seen=datetime.utcnow()
            )
            db.add(agent_record)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Agent registered successfully",
            "agent_id": agent_record.id,
            "api_key": agent_record.api_key
        }
        
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register agent"
        )


@router.get("/config/{agent_id}", response_model=AgentConfig)
async def get_agent_config(agent_id: int):
    """
    Get configuration for a specific agent.
    """
    try:
        # TODO: Implement config retrieval
        # - Verify agent exists
        # - Return current configuration
        # - Include any site-specific settings
        
        return AgentConfig(
            api_url="https://portal.company.com/api/v1",
            api_key="agent_api_key",
            site_id="site_001",
            company_name="Company Name"
        )
        
    except Exception as e:
        logger.error(f"Error getting agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


@router.put("/config/{agent_id}")
async def update_agent_config(agent_id: int, config: AgentConfig):
    """
    Update configuration for a specific agent.
    """
    try:
        # TODO: Implement config update
        # - Verify admin permissions
        # - Update agent configuration
        # - Increment config version
        # - Notify agent of update
        
        return {"message": "Agent configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating agent config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent configuration"
        )


@router.get("/", response_model=List[AgentStatus])
async def get_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    site_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by PC name or username")
):
    """
    Get list of all agents with filtering.
    """
    try:
        # TODO: Implement agent listing
        # - Apply filters
        # - Include pagination
        # - Calculate status based on last_seen
        
        return []
        
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch agents"
        )


@router.get("/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: int):
    """Get details for a specific agent."""
    try:
        # TODO: Implement single agent retrieval
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch agent"
        )


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: int, data: Dict[str, Any]):
    """
    Receive heartbeat from agent with status information.
    """
    try:
        # TODO: Implement heartbeat processing
        # - Update last_seen timestamp
        # - Update agent status
        # - Process any status information
        # - Return any pending commands
        
        return {
            "status": "received",
            "commands": [],  # Any pending commands for the agent
            "config_version": 1
        }
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process heartbeat"
        )


@router.get("/{agent_id}/update-check", response_model=AgentUpdate)
async def check_agent_update(agent_id: int, current_version: str):
    """
    Check if an agent update is available.
    """
    try:
        # TODO: Implement update checking
        # - Compare with latest version
        # - Return update information
        
        return AgentUpdate(
            current_version=current_version,
            latest_version="1.0.0",
            update_available=False
        )
        
    except Exception as e:
        logger.error(f"Error checking update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for updates"
        )


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int):
    """Delete an agent (admin only)."""
    try:
        # TODO: Implement agent deletion
        # - Check admin permissions
        # - Delete agent and related data
        # - Log the action
        
        return {"message": "Agent deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )
