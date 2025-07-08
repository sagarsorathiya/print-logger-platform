# Copilot Instructions for Distributed Print Tracking Portal

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a distributed print tracking portal system with the following components:

### Architecture
- **Backend API Server**: FastAPI-based Python server with PostgreSQL database
- **Web Portal**: Modern web dashboard with authentication and reporting
- **Windows Agent**: Lightweight print monitoring service for Windows PCs
- **Multi-site Support**: MPLS-connected locations with offline resilience

### Key Requirements
- **Open Source Only**: No paid/licensed software dependencies
- **Self-hosted**: All components deployable on-premises
- **Multi-site**: 10+ locations with independent operation capability
- **Security**: HTTPS, API keys, LDAP/AD integration, SSO support
- **Scalability**: High-volume log handling with fast statistics

### Code Guidelines
- Follow Python PEP 8 standards
- Use type hints throughout
- Implement proper error handling and logging
- Design for scalability and maintainability
- Ensure security best practices
- Support both online and offline operations
- Use async/await patterns for performance

### Database Design
- PostgreSQL for production, SQLite for development/small installs
- Efficient indexing for fast queries
- Audit logging for all operations
- Support for bulk operations

### Authentication & Security
- LDAP/Active Directory integration
- JWT tokens for API authentication
- Role-based access control (admin/user)
- Encrypted data in transit
- Secure configuration management
