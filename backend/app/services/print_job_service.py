"""
Database service layer for print jobs management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import and_, or_, func, desc, Integer
from sqlalchemy.orm import Session, joinedload

from backend.app.models.models import (
    PrintJob, User, Agent, Printer, Site, Company
)
from backend.app.schemas.print_jobs import (
    PrintJobCreate, PrintJobResponse, PrintJobFilter, PrintJobStats
)


class PrintJobService:
    """Service class for print job operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_print_job(self, job_data: PrintJobCreate) -> PrintJob:
        """Create a new print job."""
        # Find or create site
        site = self.get_or_create_site(job_data.site_id, job_data.company_name)
        
        # Find or create user
        user = self.get_or_create_user(job_data.username, site.company_id)
        
        # Find or create printer
        printer = self.get_or_create_printer(
            job_data.printer_name, 
            job_data.printer_ip, 
            site.id
        )
        
        # Calculate total pages
        total_pages = job_data.pages * job_data.copies
        
        # Create print job
        print_job = PrintJob(
            username=job_data.username,
            pc_name=job_data.pc_name,
            printer_name=job_data.printer_name,
            printer_ip=job_data.printer_ip,
            document_name=job_data.document_name,
            pages=job_data.pages,
            copies=job_data.copies,
            total_pages=total_pages,
            is_duplex=job_data.is_duplex,
            is_color=job_data.is_color,
            print_time=job_data.print_time or datetime.utcnow(),
            agent_version=job_data.agent_version,
            job_size_bytes=getattr(job_data, 'job_size_bytes', None),
            user_id=user.id,
            printer_id=printer.id,
            site_id=site.id
        )
        
        self.db.add(print_job)
        self.db.commit()
        self.db.refresh(print_job)
        
        return print_job
    
    async def create_print_jobs_batch(self, jobs_data: List[PrintJobCreate]) -> Dict[str, Any]:
        """Create multiple print jobs in a batch."""
        created_jobs = []
        failed_jobs = []
        
        for job_data in jobs_data:
            try:
                job = await self.create_print_job(job_data)
                created_jobs.append(job)
            except Exception as e:
                failed_jobs.append({
                    "job_data": job_data.dict(),
                    "error": str(e)
                })
        
        return {
            "processed": len(created_jobs),
            "failed": len(failed_jobs),
            "created_jobs": created_jobs,
            "failed_jobs": failed_jobs
        }
    
    def get_print_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[PrintJobFilter] = None
    ) -> List[PrintJob]:
        """Get print jobs with filtering and pagination."""
        query = self.db.query(PrintJob).options(
            joinedload(PrintJob.user),
            joinedload(PrintJob.printer),
            joinedload(PrintJob.site)
        )
        
        # Apply filters
        if filters:
            if filters.username:
                query = query.filter(PrintJob.username.ilike(f"%{filters.username}%"))
            
            if filters.pc_name:
                query = query.filter(PrintJob.pc_name.ilike(f"%{filters.pc_name}%"))
            
            if filters.printer_name:
                query = query.filter(PrintJob.printer_name.ilike(f"%{filters.printer_name}%"))
            
            if filters.site_id:
                query = query.join(Site).filter(Site.site_id == filters.site_id)
            
            if filters.start_date:
                query = query.filter(PrintJob.print_time >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(PrintJob.print_time <= filters.end_date)
            
            if filters.is_color is not None:
                query = query.filter(PrintJob.is_color == filters.is_color)
            
            if filters.is_duplex is not None:
                query = query.filter(PrintJob.is_duplex == filters.is_duplex)
            
            if filters.min_pages:
                query = query.filter(PrintJob.pages >= filters.min_pages)
            
            if filters.max_pages:
                query = query.filter(PrintJob.pages <= filters.max_pages)
        
        # Order by most recent first
        query = query.order_by(desc(PrintJob.print_time))
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def get_print_job_by_id(self, job_id: int) -> Optional[PrintJob]:
        """Get a print job by ID."""
        return self.db.query(PrintJob).options(
            joinedload(PrintJob.user),
            joinedload(PrintJob.printer),
            joinedload(PrintJob.site)
        ).filter(PrintJob.id == job_id).first()
    
    def delete_print_job(self, job_id: int) -> bool:
        """Delete a print job."""
        job = self.db.query(PrintJob).filter(PrintJob.id == job_id).first()
        if job:
            self.db.delete(job)
            self.db.commit()
            return True
        return False
    
    def get_print_job_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        site_id: Optional[str] = None
    ) -> PrintJobStats:
        """Get print job statistics."""
        query = self.db.query(PrintJob)
        
        # Apply date filters
        if start_date:
            query = query.filter(PrintJob.print_time >= start_date)
        if end_date:
            query = query.filter(PrintJob.print_time <= end_date)
        
        # Apply site filter
        if site_id:
            query = query.join(Site).filter(Site.site_id == site_id)
        
        # Calculate statistics using simpler approach
        stats = query.with_entities(
            func.count(PrintJob.id).label('total_jobs'),
            func.coalesce(func.sum(PrintJob.total_pages), 0).label('total_pages'),
            func.coalesce(func.sum(
                PrintJob.total_pages * PrintJob.is_color.cast(Integer)
            ), 0).label('color_pages'),
            func.coalesce(func.sum(
                PrintJob.total_pages * (1 - PrintJob.is_color.cast(Integer))
            ), 0).label('bw_pages'),
            func.coalesce(func.sum(
                PrintJob.total_pages * PrintJob.is_duplex.cast(Integer)
            ), 0).label('duplex_pages'),
            func.coalesce(func.sum(
                PrintJob.total_pages * (1 - PrintJob.is_duplex.cast(Integer))
            ), 0).label('single_sided_pages'),
            func.count(func.distinct(PrintJob.username)).label('unique_users'),
            func.count(func.distinct(PrintJob.printer_name)).label('unique_printers')
        ).first()
        
        return PrintJobStats(
            total_jobs=stats.total_jobs or 0,
            total_pages=stats.total_pages or 0,
            color_pages=stats.color_pages or 0,
            bw_pages=stats.bw_pages or 0,
            duplex_pages=stats.duplex_pages or 0,
            single_sided_pages=stats.single_sided_pages or 0,
            unique_users=stats.unique_users or 0,
            unique_printers=stats.unique_printers or 0,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_or_create_site(self, site_id: str, company_name: str) -> Site:
        """Get or create a site."""
        # First, get or create company
        company = self.db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(
                name=company_name,
                domain=company_name.lower().replace(" ", "")
            )
            self.db.add(company)
            self.db.flush()
        
        # Then, get or create site
        site = self.db.query(Site).filter(
            and_(Site.site_id == site_id, Site.company_id == company.id)
        ).first()
        
        if not site:
            site = Site(
                site_id=site_id,
                name=f"Site {site_id}",
                company_id=company.id
            )
            self.db.add(site)
            self.db.flush()
        
        return site
    
    def get_or_create_user(self, username: str, company_id: int) -> User:
        """Get or create a user."""
        user = self.db.query(User).filter(
            and_(User.username == username, User.company_id == company_id)
        ).first()
        
        if not user:
            user = User(
                username=username,
                email=f"{username}@company.local",
                full_name=username.title(),
                company_id=company_id,
                is_ldap_user=False
            )
            self.db.add(user)
            self.db.flush()
        
        return user
    
    def get_or_create_printer(self, printer_name: str, printer_ip: Optional[str], site_id: int) -> Printer:
        """Get or create a printer."""
        printer = self.db.query(Printer).filter(
            and_(Printer.name == printer_name, Printer.site_id == site_id)
        ).first()
        
        if not printer:
            printer = Printer(
                name=printer_name,
                ip_address=printer_ip,
                site_id=site_id,
                is_active=True
            )
            self.db.add(printer)
            self.db.flush()
        
        return printer
