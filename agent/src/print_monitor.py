"""
Print Monitor - Captures Windows print jobs using WMI.
"""

import time
import json
import wmi
import threading
from datetime import datetime
from typing import Callable, Optional
import logging


class PrintMonitor:
    """Monitor Windows print jobs using WMI."""
    
    def __init__(self, on_print_job: Callable):
        """
        Initialize print monitor.
        
        Args:
            on_print_job: Callback function to handle print jobs
        """
        self.on_print_job = on_print_job
        self.logger = logging.getLogger(__name__)
        self.wmi_connection = None
        self.monitoring_thread = None
        self.stop_monitoring = False
        
    def start_monitoring(self):
        """Start monitoring print jobs."""
        try:
            self.wmi_connection = wmi.WMI()
            self.stop_monitoring = False
            
            self.monitoring_thread = threading.Thread(
                target=self._monitor_print_jobs,
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.logger.info("Print monitoring started")
            
        except Exception as e:
            self.logger.error(f"Failed to start print monitoring: {e}")
            raise
    
    def stop_monitoring_service(self):
        """Stop monitoring print jobs."""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Print monitoring stopped")
    
    def _monitor_print_jobs(self):
        """Monitor print jobs in a separate thread."""
        try:
            # Monitor Win32_PrintJob creation events
            job_watcher = self.wmi_connection.Win32_PrintJob.watch_for("creation")
            
            while not self.stop_monitoring:
                try:
                    # Wait for new print job (with timeout)
                    new_job = job_watcher(timeout_ms=1000)
                    if new_job and not self.stop_monitoring:
                        self._process_print_job(new_job)
                        
                except wmi.x_wmi_timed_out:
                    # Timeout is expected, continue monitoring
                    continue
                except Exception as e:
                    self.logger.error(f"Error monitoring print job: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Print monitoring error: {e}")
    
    def _process_print_job(self, wmi_job):
        """Process a WMI print job event."""
        try:
            # Extract job information
            job_data = {
                'job_id': getattr(wmi_job, 'JobId', None),
                'document_name': getattr(wmi_job, 'Document', 'Unknown Document'),
                'printer_name': getattr(wmi_job, 'Name', '').split(',')[0] if getattr(wmi_job, 'Name', '') else 'Unknown Printer',
                'username': getattr(wmi_job, 'Owner', 'Unknown User'),
                'pages': getattr(wmi_job, 'TotalPages', 0),
                'size_bytes': getattr(wmi_job, 'Size', 0),
                'status': getattr(wmi_job, 'Status', 'Unknown'),
                'print_time': datetime.utcnow().isoformat(),
                'submitted_time': getattr(wmi_job, 'TimeSubmitted', None)
            }
            
            # Get additional printer information
            printer_info = self._get_printer_info(job_data['printer_name'])
            job_data.update(printer_info)
            
            # Call the callback function
            self.on_print_job(job_data)
            
        except Exception as e:
            self.logger.error(f"Error processing print job: {e}")
    
    def _get_printer_info(self, printer_name: str) -> dict:
        """Get additional printer information."""
        try:
            # Query printer details
            printers = self.wmi_connection.Win32_Printer(Name=printer_name)
            
            if printers:
                printer = printers[0]
                return {
                    'printer_ip': getattr(printer, 'PortName', ''),
                    'printer_driver': getattr(printer, 'DriverName', ''),
                    'printer_location': getattr(printer, 'Location', ''),
                    'is_color': self._is_color_printer(printer),
                    'is_duplex': self._is_duplex_capable(printer)
                }
            
        except Exception as e:
            self.logger.error(f"Error getting printer info: {e}")
        
        return {
            'printer_ip': '',
            'printer_driver': '',
            'printer_location': '',
            'is_color': False,
            'is_duplex': False
        }
    
    def _is_color_printer(self, printer) -> bool:
        """Determine if printer supports color printing."""
        try:
            # Check printer capabilities
            capabilities = getattr(printer, 'Capabilities', [])
            if capabilities:
                # Look for color capability codes
                color_codes = [4, 5]  # Common color capability codes
                return any(cap in color_codes for cap in capabilities)
            
            # Fallback: check driver name for color keywords
            driver_name = getattr(printer, 'DriverName', '').lower()
            color_keywords = ['color', 'colour', 'clr']
            return any(keyword in driver_name for keyword in color_keywords)
            
        except Exception:
            return False
    
    def _is_duplex_capable(self, printer) -> bool:
        """Determine if printer supports duplex printing."""
        try:
            # Check printer capabilities
            capabilities = getattr(printer, 'Capabilities', [])
            if capabilities:
                # Look for duplex capability codes
                duplex_codes = [6, 7]  # Common duplex capability codes
                return any(cap in duplex_codes for cap in capabilities)
            
            # Fallback: check driver name for duplex keywords
            driver_name = getattr(printer, 'DriverName', '').lower()
            duplex_keywords = ['duplex', 'double', 'two-sided']
            return any(keyword in driver_name for keyword in duplex_keywords)
            
        except Exception:
            return False
    
    def get_installed_printers(self) -> list:
        """Get list of installed printers."""
        try:
            if not self.wmi_connection:
                self.wmi_connection = wmi.WMI()
            
            printers = []
            for printer in self.wmi_connection.Win32_Printer():
                printer_info = {
                    'name': getattr(printer, 'Name', ''),
                    'location': getattr(printer, 'Location', ''),
                    'port': getattr(printer, 'PortName', ''),
                    'driver': getattr(printer, 'DriverName', ''),
                    'status': getattr(printer, 'Status', ''),
                    'is_default': getattr(printer, 'Default', False),
                    'is_shared': getattr(printer, 'Shared', False),
                    'is_color': self._is_color_printer(printer),
                    'is_duplex': self._is_duplex_capable(printer)
                }
                printers.append(printer_info)
            
            return printers
            
        except Exception as e:
            self.logger.error(f"Error getting installed printers: {e}")
            return []
