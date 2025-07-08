"""
Pydantic schemas for print jobs.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class PrintJobBase(BaseModel):
    """Base print job schema."""
    username: str = Field(..., min_length=1, max_length=100)
    pc_name: str = Field(..., min_length=1, max_length=255)
    printer_name: str = Field(..., min_length=1, max_length=255)
    printer_ip: Optional[str] = Field(None, max_length=45)
    document_name: str = Field(..., min_length=1, max_length=500)
    pages: int = Field(..., gt=0, le=10000)
    copies: int = Field(default=1, gt=0, le=1000)
    is_duplex: bool = Field(default=False)
    is_color: bool = Field(default=False)
    print_time: Optional[datetime] = None
    agent_version: Optional[str] = Field(None, max_length=50)
    job_size_bytes: Optional[int] = Field(None, ge=0)


class PrintJobCreate(PrintJobBase):
    """Schema for creating a print job."""
    site_id: str = Field(..., min_length=1, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=255)
    
    @validator('print_time', pre=True, always=True)
    def set_print_time(cls, v):
        return v or datetime.utcnow()


class PrintJobResponse(PrintJobBase):
    """Schema for print job responses."""
    id: int
    total_pages: int
    site_id: str  # Changed from int to str to match actual site_id values
    user_id: Optional[int]
    agent_id: Optional[int]
    printer_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PrintJobFilter(BaseModel):
    """Schema for filtering print jobs."""
    username: Optional[str] = None
    pc_name: Optional[str] = None
    printer_name: Optional[str] = None
    site_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_color: Optional[bool] = None
    is_duplex: Optional[bool] = None
    min_pages: Optional[int] = Field(None, ge=1)
    max_pages: Optional[int] = Field(None, ge=1)


class PrintJobBatch(BaseModel):
    """Schema for batch print job submission."""
    jobs: list[PrintJobCreate] = Field(..., min_items=1, max_items=1000)


class PrintJobStats(BaseModel):
    """Schema for print job statistics."""
    total_jobs: int
    total_pages: int
    color_pages: int
    bw_pages: int
    duplex_pages: int
    single_sided_pages: int
    unique_users: int
    unique_printers: int
    cost_estimate: Optional[float] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
