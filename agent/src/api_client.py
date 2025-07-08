"""
API Client - Handles communication with the Print Tracking Portal API.
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging


class APIClient:
    """Handles API communication with the Print Tracking Portal."""
    
    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PrintTrackingAgent/1.0.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Register agent with the portal."""
        try:
            url = f"{self.base_url}/agents/register"
            
            self.logger.info(f"Registering agent with portal: {agent_data.get('pc_name')}")
            
            response = self.session.post(url, json=agent_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info("Agent registration successful")
            
            # Update API key if provided
            if 'api_key' in result:
                self.api_key = result['api_key']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.api_key}'
                })
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Agent registration failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during registration: {e}")
            return None
    
    def submit_print_job(self, job_data: Dict[str, Any]) -> bool:
        """Submit a single print job to the portal."""
        try:
            url = f"{self.base_url}/print-jobs/submit"
            
            response = self.session.post(url, json=job_data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            if result.get('status') == 'success':
                self.logger.debug(f"Print job submitted: {job_data.get('document_name')}")
                return True
            else:
                self.logger.error(f"Print job submission failed: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to submit print job: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error submitting print job: {e}")
            return False
    
    def submit_print_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Submit multiple print jobs in a batch."""
        try:
            url = f"{self.base_url}/print-jobs/submit-batch"
            
            self.logger.info(f"Submitting batch of {len(jobs_data)} print jobs")
            
            response = self.session.post(url, json=jobs_data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"Batch submission result: {result}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to submit print job batch: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error submitting batch: {e}")
            return None
    
    def send_heartbeat(self, agent_id: int, status_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send heartbeat to the portal."""
        try:
            url = f"{self.base_url}/agents/{agent_id}/heartbeat"
            
            response = self.session.post(url, json=status_data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug("Heartbeat sent successfully")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error sending heartbeat: {e}")
            return None
    
    def get_agent_config(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get agent configuration from the portal."""
        try:
            url = f"{self.base_url}/agents/config/{agent_id}"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug("Agent configuration retrieved")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get agent config: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting config: {e}")
            return None
    
    def check_agent_update(self, agent_id: int, current_version: str) -> Optional[Dict[str, Any]]:
        """Check if agent update is available."""
        try:
            url = f"{self.base_url}/agents/{agent_id}/update-check"
            params = {"current_version": current_version}
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('update_available'):
                self.logger.info(f"Agent update available: {result.get('latest_version')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error checking updates: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test connection to the portal API."""
        try:
            url = f"{self.base_url}/health"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            self.logger.info("API connection test successful")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error testing connection: {e}")
            return False
    
    def update_api_key(self, api_key: str):
        """Update the API key."""
        self.api_key = api_key
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })
        self.logger.info("API key updated")
    
    def get_portal_status(self) -> Optional[Dict[str, Any]]:
        """Get portal status information."""
        try:
            url = f"{self.base_url}/status"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Failed to get portal status: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting portal status: {e}")
            return None
