# Print Tracking Agent

## Overview
The Print Tracking Agent is a lightweight Windows service that monitors print jobs on Windows PCs and reports them to the central Print Tracking Portal.

## Features
- **Silent Operation**: Runs as a Windows service with minimal user impact
- **Print Job Monitoring**: Captures all print jobs regardless of printer type
- **Offline Resilience**: Caches print jobs locally when offline
- **Automatic Configuration**: Downloads configuration from central portal
- **Security**: Uses encrypted communication with API key authentication

## Architecture
- **Service Component**: Windows service for background operation
- **Print Monitor**: Hooks into Windows print spooler
- **Local Cache**: SQLite database for offline storage
- **HTTP Client**: Secure communication with portal API
- **Configuration Manager**: Handles settings and updates

## Installation
1. Download the installer from the portal
2. Run as administrator: `PrintAgentInstaller.msi`
3. Agent automatically registers with portal
4. Configuration is downloaded automatically

## Files
- `src/` - Agent source code
- `installer/` - MSI installer scripts
- `config/` - Configuration templates
- `build_agent.py` - Build script

## Build Instructions
```bash
cd agent
python build_agent.py
```

This will create:
- Compiled agent executable
- Windows service installer
- MSI package for deployment
