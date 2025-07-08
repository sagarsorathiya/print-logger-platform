"""
Print Jobs API endpoints for receiving, storing, and querying print job data.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
import logging

from backend.app.core.database import get_db
from backend.app.services.print_job_service import PrintJobService
from backend.app.schemas.print_jobs import (
    PrintJobCreate, PrintJobResponse, PrintJobFilter, PrintJobStats
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/submit", response_model=dict)
async def submit_print_job(print_job: PrintJobCreate, db: Session = Depends(get_db)):
    """
    Submit a new print job from an agent.
    This endpoint receives print job data from Windows agents.
    """
    try:
        logger.info(f"Received print job from {print_job.username} on {print_job.pc_name}")
        
        service = PrintJobService(db)
        created_job = await service.create_print_job(print_job)
        
        return {
            "status": "success",
            "message": "Print job recorded successfully",
            "job_id": created_job.id
        }
        
    except Exception as e:
        logger.error(f"Error submitting print job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record print job"
        )


@router.post("/submit-batch", response_model=dict)
async def submit_print_jobs_batch(print_jobs: List[PrintJobCreate], db: Session = Depends(get_db)):
    """
    Submit multiple print jobs in a batch.
    Used by agents when coming back online after being offline.
    """
    try:
        logger.info(f"Received batch of {len(print_jobs)} print jobs")
        
        service = PrintJobService(db)
        result = await service.create_print_jobs_batch(print_jobs)
        
        return {
            "status": "success",
            "message": f"Processed {result['processed']} print jobs",
            "processed": result['processed'],
            "failed": result['failed']
        }
        
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process print job batch"
        )


@router.get("/", response_model=List[PrintJobResponse])
async def get_print_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    username: Optional[str] = Query(None, description="Filter by username"),
    pc_name: Optional[str] = Query(None, description="Filter by PC name"),
    printer_name: Optional[str] = Query(None, description="Filter by printer name"),
    site_id: Optional[str] = Query(None, description="Filter by site ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    is_color: Optional[bool] = Query(None, description="Filter by color/BW"),
    is_duplex: Optional[bool] = Query(None, description="Filter by duplex"),
    db: Session = Depends(get_db)
):
    """
    Get print jobs with filtering and pagination.
    """
    try:
        # Create filter object
        filters = PrintJobFilter(
            username=username,
            pc_name=pc_name,
            printer_name=printer_name,
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            is_color=is_color,
            is_duplex=is_duplex
        )
        
        service = PrintJobService(db)
        jobs = service.get_print_jobs(skip=skip, limit=limit, filters=filters)
        
        # Convert to response format
        return [
            PrintJobResponse(
                id=job.id,
                username=job.username,
                pc_name=job.pc_name,
                printer_name=job.printer_name,
                printer_ip=job.printer_ip or "",
                document_name=job.document_name,
                pages=job.pages,
                copies=job.copies,
                total_pages=job.total_pages,
                is_duplex=job.is_duplex,
                is_color=job.is_color,
                site_id=job.site.site_id if job.site else "",
                user_id=job.user_id,
                agent_id=job.agent_id,
                printer_id=job.printer_id,
                print_time=job.print_time,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Error fetching print jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch print jobs"
        )


@router.get("/{job_id}", response_model=PrintJobResponse)
async def get_print_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get a specific print job by ID.
    """
    try:
        service = PrintJobService(db)
        job = service.get_print_job_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        return PrintJobResponse(
            id=job.id,
            username=job.username,
            pc_name=job.pc_name,
            printer_name=job.printer_name,
            printer_ip=job.printer_ip or "",
            document_name=job.document_name,
            pages=job.pages,
            copies=job.copies,
            total_pages=job.total_pages,
            is_duplex=job.is_duplex,
            is_color=job.is_color,
            site_id=job.site.site_id if job.site else "",
            user_id=job.user_id,
            agent_id=job.agent_id,
            printer_id=job.printer_id,
            print_time=job.print_time,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching print job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch print job"
        )


@router.delete("/{job_id}")
async def delete_print_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete a print job by ID.
    """
    try:
        service = PrintJobService(db)
        success = service.delete_print_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Print job not found"
            )
        
        return {"status": "success", "message": "Print job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting print job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete print job"
        )


@router.get("/stats/overview", response_model=PrintJobStats)
async def get_print_job_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    site_id: Optional[str] = Query(None, description="Filter by site ID"),
    db: Session = Depends(get_db)
):
    """
    Get print job statistics for a given period.
    """
    try:
        service = PrintJobService(db)
        stats = service.get_print_job_stats(
            start_date=start_date,
            end_date=end_date,
            site_id=site_id
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting print job stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get print job statistics"
        )
