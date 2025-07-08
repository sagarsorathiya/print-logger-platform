"""
Configuration Manager - Handles agent configuration and settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """Manages agent configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default config location
            self.config_path = Path.home() / "PrintAgent" / "config.json"
        
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "api_url": "http://localhost:8000/api/v1",
            "api_key": "",
            "site_id": "DEFAULT",
            "company_name": "Default Company",
            "agent_version": "1.0.0",
            "update_interval": 300,  # 5 minutes
            "log_level": "INFO",
            "offline_cache_days": 7,
            "max_log_size_mb": 100,
            "retry_attempts": 3,
            "retry_delay": 30,
            "heartbeat_interval": 60,  # 1 minute
            "auto_register": True,
            "pc_name": "",
            "username": ""
        }
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.info("No configuration file found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def update_from_server(self, server_config: Dict[str, Any]):
        """Update configuration from server response."""
        try:
            # List of keys that can be updated from server
            updatable_keys = [
                "update_interval",
                "log_level", 
                "offline_cache_days",
                "max_log_size_mb",
                "heartbeat_interval"
            ]
            
            updated = False
            for key in updatable_keys:
                if key in server_config and server_config[key] != self.config.get(key):
                    self.config[key] = server_config[key]
                    updated = True
                    self.logger.info(f"Updated {key} from server: {server_config[key]}")
            
            if updated:
                self.save_config()
                
        except Exception as e:
            self.logger.error(f"Error updating config from server: {e}")
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information for registration."""
        import platform
        import socket
        import getpass
        
        try:
            return {
                "pc_name": self.config.get("pc_name") or socket.gethostname(),
                "username": self.config.get("username") or getpass.getuser(),
                "os_version": f"{platform.system()} {platform.release()}",
                "python_version": platform.python_version(),
                "agent_version": self.config.get("agent_version", "1.0.0")
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {
                "pc_name": "Unknown",
                "username": "Unknown", 
                "os_version": "Unknown",
                "python_version": "Unknown",
                "agent_version": self.config.get("agent_version", "1.0.0")
            }
    
    def validate_config(self) -> bool:
        """Validate configuration."""
        required_fields = ["api_url", "site_id", "company_name"]
        
        for field in required_fields:
            if not self.config.get(field):
                self.logger.error(f"Missing required configuration: {field}")
                return False
        
        return True
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self._load_default_config()
        self.save_config()
        self.logger.info("Configuration reset to defaults")
    
    def get_log_level(self) -> str:
        """Get logging level."""
        return self.config.get("log_level", "INFO").upper()
    
    def get_data_directory(self) -> Path:
        """Get data directory path."""
        data_dir = Path.home() / "PrintAgent" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def get_logs_directory(self) -> Path:
        """Get logs directory path."""
        logs_dir = Path.home() / "PrintAgent" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
