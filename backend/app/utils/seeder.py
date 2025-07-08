"""
Database seeder for development and testing.
"""

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.app.core.database import get_db_session
from backend.app.models.models import (
    Company, Site, User, Agent, Printer, PrintJob
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_sample_data():
    """Seed the database with sample data for testing."""
    db = next(get_db_session())
    
    try:
        # Check if data already exists
        existing_jobs = db.query(PrintJob).count()
        if existing_jobs > 0:
            print(f"Database already has {existing_jobs} print jobs. Skipping seeding.")
            return
        
        print("Seeding database with sample data...")
        
        # Create sample company
        company = Company(
            name="Acme Corporation",
            domain="acme.com"
        )
        db.add(company)
        db.flush()
        
        # Create sample sites
        sites = []
        for site_data in [
            ("HQ", "Headquarters", "123 Main St"),
            ("BR1", "Branch Office 1", "456 Oak Ave"),
            ("BR2", "Branch Office 2", "789 Pine Rd"),
            ("WH", "Warehouse", "321 Industrial Blvd")
        ]:
            site = Site(
                site_id=site_data[0],
                name=site_data[1],
                address=site_data[2],
                company_id=company.id
            )
            sites.append(site)
            db.add(site)
        
        db.flush()
        
        # Create sample users
        users = []
        usernames = [
            ("admin", "Administrator", True),  # Admin user
            ("jsmith", "John Smith", False),
            ("ajohanson", "Alice Johnson", False), 
            ("mwilson", "Mike Wilson", False),
            ("rbrown", "Rachel Brown", False),
            ("ldavis", "Linda Davis", False), 
            ("swilliams", "Steve Williams", False),
            ("dmiller", "Dave Miller", False),
            ("kmoore", "Karen Moore", False),
            ("ttaylor", "Tom Taylor", False),
            ("janderson", "Jane Anderson", False)
        ]
        
        for username, full_name, is_admin in usernames:
            # Default password for all test users
            default_password = "admin123" if is_admin else "password123"
            hashed_password = pwd_context.hash(default_password)
            
            user = User(
                username=username,
                email=f"{username}@acme.com",
                full_name=full_name,
                hashed_password=hashed_password,
                company_id=company.id,
                is_active=True,
                is_ldap_user=False,
                role="admin" if is_admin else "user"
            )
            users.append(user)
            db.add(user)
        
        db.flush()
        
        # Create sample printers
        printers = []
        printer_data = [
            ("HP-LaserJet-P1606dn", "192.168.1.101", False, True),
            ("Canon-ColorImageCLASS", "192.168.1.102", True, True),
            ("Brother-HL-L2340DW", "192.168.1.103", False, True),
            ("Xerox-WorkCentre-6515", "192.168.1.104", True, True),
            ("Epson-WorkForce-Pro", "192.168.1.105", True, False),
            ("HP-OfficeJet-Pro-8720", "192.168.1.106", True, True),
        ]
        
        for i, (name, ip, is_color, is_duplex) in enumerate(printer_data):
            site = sites[i % len(sites)]  # Distribute printers across sites
            printer = Printer(
                name=name,
                ip_address=ip,
                model=name.replace("-", " "),
                is_color=is_color,
                is_duplex_capable=is_duplex,
                is_active=True,
                site_id=site.id,
                location=f"Floor {(i % 3) + 1}"
            )
            printers.append(printer)
            db.add(printer)
        
        db.flush()
        
        # Create sample agents
        agents = []
        for i, site in enumerate(sites):
            for j in range(2):  # 2 agents per site
                agent = Agent(
                    pc_name=f"PC-{site.site_id}-{j+1:02d}",
                    pc_ip=f"192.168.{i+1}.{j+10}",
                    username=random.choice(users).username,
                    agent_version="1.0.0",
                    os_version="Windows 10 Pro",
                    api_key=f"agent_key_{site.site_id}_{j+1}",
                    status="online",
                    site_id=site.id,
                    last_seen=datetime.utcnow(),
                    total_jobs_submitted=0,
                    pending_jobs=0,
                    config_version=1,
                    installed_printers="[]"
                )
                agents.append(agent)
                db.add(agent)
        
        db.flush()
        
        # Generate sample print jobs
        print("Generating sample print jobs...")
        
        documents = [
            "Monthly Report.pdf", "Invoice_12345.pdf", "Meeting Notes.docx",
            "Project Proposal.pptx", "Expense Report.xlsx", "Contract.pdf",
            "User Manual.pdf", "Presentation.pptx", "Budget Analysis.xlsx",
            "Technical Specification.docx", "Marketing Flyer.pdf", "Policy Document.pdf"
        ]
        
        # Generate jobs for the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            
            # Generate 20-100 jobs per day (weekdays more than weekends)
            if current_date.weekday() < 5:  # Weekday
                jobs_count = random.randint(50, 100)
            else:  # Weekend
                jobs_count = random.randint(5, 20)
            
            for _ in range(jobs_count):
                user = random.choice(users)
                printer = random.choice(printers)
                agent = random.choice([a for a in agents if a.site_id == printer.site_id])
                document = random.choice(documents)
                
                # Random job time during business hours
                job_time = current_date.replace(
                    hour=random.randint(8, 17),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                pages = random.randint(1, 50)
                copies = random.choices([1, 2, 3, 4, 5], weights=[70, 15, 8, 4, 3])[0]
                is_color = random.choices([True, False], weights=[30, 70])[0] and printer.is_color
                is_duplex = random.choices([True, False], weights=[60, 40])[0] and printer.is_duplex_capable
                
                print_job = PrintJob(
                    username=user.username,
                    pc_name=agent.pc_name,
                    printer_name=printer.name,
                    printer_ip=printer.ip_address,
                    document_name=document,
                    pages=pages,
                    copies=copies,
                    total_pages=pages * copies,
                    is_duplex=is_duplex,
                    is_color=is_color,
                    print_time=job_time,
                    agent_version=agent.agent_version,
                    job_size_bytes=random.randint(50000, 5000000),
                    user_id=user.id,
                    agent_id=agent.id,
                    printer_id=printer.id,
                    site_id=printer.site_id
                )
                db.add(print_job)
        
        # Commit all data
        db.commit()
        
        # Print summary
        total_jobs = db.query(PrintJob).count()
        total_users = db.query(User).count()
        total_printers = db.query(Printer).count()
        total_sites = db.query(Site).count()
        
        print(f"✅ Successfully seeded database with:")
        print(f"   - {total_sites} sites")
        print(f"   - {total_users} users")
        print(f"   - {total_printers} printers")
        print(f"   - {len(agents)} agents")
        print(f"   - {total_jobs} print jobs")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_sample_data()
