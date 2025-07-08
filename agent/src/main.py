"""
Print Tracking Agent - Main Entry Point

Windows service for monitoring print jobs and reporting to central portal.
"""

import sys
import time
import logging
import json
from pathlib import Path
from typing import Optional
import win32serviceutil
import win32service
import win32event
import servicemanager

from print_monitor import PrintMonitor
from config_manager import ConfigManager
from api_client import APIClient
from local_storage import LocalStorage


class PrintTrackingService(win32serviceutil.ServiceFramework):
    """Windows service for print tracking."""
    
    _svc_name_ = "PrintTrackingAgent"
    _svc_display_name_ = "Print Tracking Agent"
    _svc_description_ = "Monitors print jobs and reports to Print Tracking Portal"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.local_storage = LocalStorage()
        self.api_client = APIClient(self.config_manager)
        self.print_monitor = PrintMonitor(self.on_print_job)
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Configure logging for the service."""
        log_dir = Path.home() / "AppData" / "Local" / "PrintTrackingAgent" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "agent.log"),
                logging.StreamHandler()
            ]
        )
        
    def SvcStop(self):
        """Stop the service."""
        self.logger.info("Print Tracking Agent stopping...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        
    def SvcDoRun(self):
        """Run the service."""
        self.logger.info("Print Tracking Agent starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.main_loop()
        except Exception as e:
            self.logger.error(f"Service error: {e}", exc_info=True)
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_ERROR_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, str(e))
            )
            
    def main_loop(self):
        """Main service loop."""
        # Initialize and register with portal
        self.initialize_agent()
        
        # Start print monitoring
        self.print_monitor.start()
        
        # Main loop with periodic tasks
        last_heartbeat = time.time()
        last_config_check = time.time()
        heartbeat_interval = 300  # 5 minutes
        config_check_interval = 3600  # 1 hour
        
        while self.is_running:
            current_time = time.time()
            
            try:
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # Check for configuration updates
                if current_time - last_config_check >= config_check_interval:
                    self.check_config_updates()
                    last_config_check = current_time
                
                # Upload pending print jobs
                self.upload_pending_jobs()
                
                # Wait for stop event or timeout
                if win32event.WaitForSingleObject(self.hWaitStop, 30000) == win32event.WAIT_OBJECT_0:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying
                
        # Cleanup
        self.print_monitor.stop()
        self.logger.info("Print Tracking Agent stopped")
        
    def initialize_agent(self):
        """Initialize agent and register with portal."""
        try:
            # Load or create configuration
            config = self.config_manager.load_config()
            
            if not config.get('agent_id') or not config.get('api_key'):
                self.logger.info("Agent not registered, attempting registration...")
                self.register_agent()
            else:
                self.logger.info(f"Agent initialized with ID: {config.get('agent_id')}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            raise
            
    def register_agent(self):
        """Register agent with the portal."""
        try:
            import platform
            import socket
            
            registration_data = {
                'pc_name': socket.gethostname(),
                'pc_ip': socket.gethostbyname(socket.gethostname()),
                'username': os.environ.get('USERNAME', 'Unknown'),
                'site_id': self.config_manager.get_site_id(),
                'company_name': self.config_manager.get_company_name(),
                'agent_version': '1.0.0',
                'os_version': f"{platform.system()} {platform.release()}",
                'installed_printers': self.get_installed_printers()
            }
            
            response = self.api_client.register_agent(registration_data)
            
            if response and response.get('status') == 'success':
                # Update configuration with registration info
                config = self.config_manager.load_config()
                config['agent_id'] = response.get('agent_id')
                config['api_key'] = response.get('api_key')
                self.config_manager.save_config(config)
                
                self.logger.info("Agent registered successfully")
            else:
                raise Exception("Agent registration failed")
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            raise
            
    def get_installed_printers(self):
        """Get list of installed printers."""
        try:
            import win32print
            printers = []
            
            # Enumerate local printers
            printer_info = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            
            for printer in printer_info:
                printers.append(printer[2])  # Printer name
                
            return printers
            
        except Exception as e:
            self.logger.error(f"Error getting printers: {e}")
            return []
            
    def on_print_job(self, job_data):
        """Handle new print job detected."""
        try:
            self.logger.info(f"Print job detected: {job_data.get('document_name')}")
            
            # Store locally first
            self.local_storage.store_print_job(job_data)
            
            # Try to upload immediately if online
            if self.api_client.is_online():
                self.upload_print_job(job_data)
                
        except Exception as e:
            self.logger.error(f"Error handling print job: {e}")
            
    def upload_print_job(self, job_data):
        """Upload a single print job to the portal."""
        try:
            response = self.api_client.submit_print_job(job_data)
            
            if response and response.get('status') == 'success':
                # Mark as uploaded in local storage
                self.local_storage.mark_as_uploaded(job_data['id'])
                self.logger.debug(f"Print job uploaded: {job_data['id']}")
            else:
                self.logger.warning(f"Failed to upload print job: {job_data['id']}")
                
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            
    def upload_pending_jobs(self):
        """Upload all pending print jobs."""
        try:
            pending_jobs = self.local_storage.get_pending_jobs()
            
            if pending_jobs:
                self.logger.info(f"Uploading {len(pending_jobs)} pending jobs")
                
                # Upload in batches
                batch_size = 50
                for i in range(0, len(pending_jobs), batch_size):
                    batch = pending_jobs[i:i + batch_size]
                    
                    response = self.api_client.submit_print_jobs_batch(batch)
                    
                    if response and response.get('status') == 'success':
                        # Mark batch as uploaded
                        for job in batch:
                            self.local_storage.mark_as_uploaded(job['id'])
                            
        except Exception as e:
            self.logger.error(f"Error uploading pending jobs: {e}")
            
    def send_heartbeat(self):
        """Send heartbeat to portal."""
        try:
            heartbeat_data = {
                'status': 'online',
                'pending_jobs': self.local_storage.get_pending_count(),
                'last_job_time': self.local_storage.get_last_job_time(),
                'agent_version': '1.0.0'
            }
            
            response = self.api_client.send_heartbeat(heartbeat_data)
            
            if response:
                # Process any commands from portal
                commands = response.get('commands', [])
                for command in commands:
                    self.process_command(command)
                    
        except Exception as e:
            self.logger.error(f"Heartbeat error: {e}")
            
    def check_config_updates(self):
        """Check for configuration updates from portal."""
        try:
            new_config = self.api_client.get_agent_config()
            
            if new_config:
                current_config = self.config_manager.load_config()
                
                if new_config.get('config_version', 0) > current_config.get('config_version', 0):
                    self.logger.info("Updating agent configuration")
                    self.config_manager.update_config(new_config)
                    
        except Exception as e:
            self.logger.error(f"Config update error: {e}")
            
    def process_command(self, command):
        """Process command from portal."""
        try:
            command_type = command.get('type')
            
            if command_type == 'restart':
                self.logger.info("Restart command received")
                # Implement restart logic
            elif command_type == 'update_config':
                self.logger.info("Config update command received")
                self.check_config_updates()
            elif command_type == 'sync_jobs':
                self.logger.info("Sync jobs command received")
                self.upload_pending_jobs()
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PrintTrackingService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle service installation/removal
        win32serviceutil.HandleCommandLine(PrintTrackingService)


if __name__ == '__main__':
    main()
