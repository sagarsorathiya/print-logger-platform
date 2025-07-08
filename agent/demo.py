"""
Simple Print Agent Demo - Test version that doesn't require Windows services.
"""

import os
import sys
import time
import json
import socket
import getpass
import platform
import logging
from datetime import datetime
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager
from api_client import APIClient
from local_storage import LocalStorage


class PrintAgentDemo:
    """Demo version of the print agent."""
    
    def __init__(self):
        """Initialize the demo agent."""
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.config = ConfigManager()
        self.storage = LocalStorage()
        self.api_client = None
        self.agent_id = None
        
        self.logger.info("Print Agent Demo initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('agent_demo.log')
            ]
        )
    
    def register_with_portal(self) -> bool:
        """Register the agent with the portal."""
        try:
            # Get system information
            system_info = self.config.get_system_info()
            
            # Prepare registration data
            registration_data = {
                "pc_name": system_info["pc_name"],
                "pc_ip": self.get_local_ip(),
                "username": system_info["username"],
                "site_id": self.config.get("site_id"),
                "company_name": self.config.get("company_name"),
                "agent_version": system_info["agent_version"],
                "os_version": system_info["os_version"],
                "installed_printers": self.get_demo_printers()
            }
            
            self.logger.info(f"Registering agent: {registration_data['pc_name']}")
            
            # Initialize API client
            self.api_client = APIClient(self.config.get("api_url"))
            
            # Test connection first
            if not self.api_client.test_connection():
                self.logger.error("Cannot connect to portal API")
                return False
            
            # Register agent
            result = self.api_client.register_agent(registration_data)
            
            if result and result.get('status') == 'success':
                self.agent_id = result.get('agent_id')
                api_key = result.get('api_key')
                
                if api_key:
                    self.config.set('api_key', api_key)
                    self.config.save_config()
                    self.api_client.update_api_key(api_key)
                
                self.logger.info(f"Agent registered successfully with ID: {self.agent_id}")
                return True
            else:
                self.logger.error(f"Agent registration failed: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during registration: {e}")
            return False
    
    def get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def get_demo_printers(self) -> list:
        """Get demo printer list."""
        return [
            "Microsoft Print to PDF",
            "HP LaserJet Pro M404n",
            "Canon PIXMA TS3100"
        ]
    
    def generate_demo_print_job(self) -> Dict[str, Any]:
        """Generate a demo print job."""
        import random
        
        documents = [
            "test_document.pdf",
            "monthly_report.docx", 
            "presentation.pptx",
            "invoice_12345.pdf",
            "meeting_notes.txt"
        ]
        
        printers = self.get_demo_printers()
        
        system_info = self.config.get_system_info()
        
        job_data = {
            "username": system_info["username"],
            "pc_name": system_info["pc_name"],
            "printer_name": random.choice(printers),
            "printer_ip": f"192.168.1.{random.randint(100, 200)}",
            "document_name": random.choice(documents),
            "pages": random.randint(1, 20),
            "copies": random.randint(1, 3),
            "is_duplex": random.choice([True, False]),
            "is_color": random.choice([True, False]),
            "site_id": self.config.get("site_id"),
            "company_name": self.config.get("company_name"),
            "agent_version": system_info["agent_version"],
            "print_time": datetime.utcnow().isoformat()
        }
        
        return job_data
    
    def submit_demo_jobs(self, count: int = 5):
        """Submit demo print jobs."""
        if not self.api_client:
            self.logger.error("API client not initialized")
            return
        
        jobs_submitted = 0
        jobs_cached = 0
        
        for i in range(count):
            job_data = self.generate_demo_print_job()
            
            self.logger.info(f"Submitting job {i+1}/{count}: {job_data['document_name']}")
            
            # Try to submit to portal
            if self.api_client.submit_print_job(job_data):
                jobs_submitted += 1
                self.logger.info(f"Job submitted successfully: {job_data['document_name']}")
            else:
                # Cache locally if portal is unavailable
                job_id = self.storage.store_print_job(job_data)
                jobs_cached += 1
                self.logger.info(f"Job cached locally: {job_id}")
            
            # Small delay between jobs
            time.sleep(1)
        
        self.logger.info(f"Demo complete: {jobs_submitted} submitted, {jobs_cached} cached")
    
    def upload_cached_jobs(self):
        """Upload any cached jobs to the portal."""
        if not self.api_client:
            self.logger.error("API client not initialized")
            return
        
        pending_jobs = self.storage.get_pending_jobs()
        
        if not pending_jobs:
            self.logger.info("No cached jobs to upload")
            return
        
        self.logger.info(f"Uploading {len(pending_jobs)} cached jobs")
        
        for job in pending_jobs:
            job_id = job.pop('_local_id')
            job.pop('_upload_attempts', None)
            
            if self.api_client.submit_print_job(job):
                self.storage.mark_as_uploaded(job_id)
                self.logger.info(f"Cached job uploaded: {job['document_name']}")
            else:
                self.storage.mark_upload_failed(job_id)
                self.logger.error(f"Failed to upload cached job: {job['document_name']}")
    
    def send_heartbeat(self):
        """Send heartbeat to portal."""
        if not self.api_client or not self.agent_id:
            return
        
        stats = self.storage.get_statistics()
        
        status_data = {
            "status": "online",
            "pending_jobs": stats.get('pending', 0),
            "total_jobs_cached": stats.get('total', 0),
            "system_info": self.config.get_system_info()
        }
        
        result = self.api_client.send_heartbeat(self.agent_id, status_data)
        if result:
            self.logger.debug("Heartbeat sent successfully")
    
    def run_demo(self):
        """Run the demo sequence."""
        print("🖨️  Print Tracking Agent Demo")
        print("=" * 40)
        
        # Step 1: Register with portal
        print("\n1. Registering with portal...")
        if not self.register_with_portal():
            print("❌ Registration failed!")
            return
        print("✅ Registration successful!")
        
        # Step 2: Submit demo jobs
        print("\n2. Submitting demo print jobs...")
        self.submit_demo_jobs(5)
        print("✅ Demo jobs submitted!")
        
        # Step 3: Send heartbeat
        print("\n3. Sending heartbeat...")
        self.send_heartbeat()
        print("✅ Heartbeat sent!")
        
        # Step 4: Show storage stats
        print("\n4. Storage statistics:")
        stats = self.storage.get_statistics()
        for status, count in stats.items():
            print(f"   {status}: {count}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nYou can now check the web portal at http://localhost:8080")
        print("to see the submitted print jobs.")


if __name__ == "__main__":
    demo = PrintAgentDemo()
    demo.run_demo()
