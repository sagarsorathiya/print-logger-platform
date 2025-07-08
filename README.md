# Distributed Print Tracking Portal

A comprehensive, open-source solution for tracking print jobs across multiple sites with Windows agents, centralized logging, and web-based reporting.

## 🏗️ Architecture

### Components
- **API Server**: FastAPI-based backend with PostgreSQL
- **Web Portal**: Modern dashboard with authentication and reporting  
- **Windows Agent**: Lightweight print monitoring service
- **Database**: PostgreSQL with SQLite fallback for small deployments

### Key Features
- ✅ Multi-site support (10+ locations)
- ✅ Offline resilience with local caching
- ✅ LDAP/Active Directory integration
- ✅ Real-time print job tracking
- ✅ Comprehensive reporting and analytics
- ✅ Secure API with token authentication
- ✅ Self-hosted deployment
- ✅ Open-source components only

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ (or SQLite for development)
- Windows PCs for agent deployment

### Development Setup

1. **Clone and setup virtual environment**:
   ```bash
   git clone <repository-url>
   cd Printer_Count_Portal
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Setup database**:
   ```bash
   # Initialize database and create admin user
   python setup_db.py
   
   # Or run migrations manually
   cd backend
   python -m alembic upgrade head
   python init_db.py  # Seeds admin user
   ```

4. **Start the system**:
   ```bash
   # Option 1: Use VS Code tasks
   # - Run "Start API Server" task (Ctrl+Shift+P -> Tasks: Run Task)
   # - Run "Start Web Portal" task
   
   # Option 2: Manual startup
   # API Server
   python -m uvicorn backend.main:app --reload --port 8000
   
   # Web Portal (in new terminal)
   cd frontend
   python -m http.server 8080
   ```

5. **Access the portal**:
   ```
   Web Portal: http://localhost:8080
   API Docs: http://localhost:8000/docs
   Default admin: admin@example.com / admin123
   ```

### Agent Testing

You can test the agent functionality without installing it:

```bash
cd agent
# Install agent dependencies
pip install -r requirements.txt

# Run demo to test print job logging
python demo.py
```

This creates sample print jobs that you can view in the web portal.

## 📁 Project Structure

```
Printer_Count_Portal/
├── backend/                 # API Server (FastAPI)
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration and security
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   └── main.py             # Application entry point
├── frontend/               # Web Portal
│   ├── static/             # CSS, JS, images
│   ├── templates/          # HTML templates
│   └── index.html          # Main page
├── agent/                  # Windows Print Agent
│   ├── src/                # Agent source code
│   ├── installer/          # MSI installer scripts
│   └── config/             # Configuration templates
├── database/               # Database schemas and scripts
│   ├── migrations/         # Alembic migrations
│   └── init_scripts/       # Initial setup scripts
├── docs/                   # Documentation
├── scripts/                # Deployment and utility scripts
└── tests/                  # Test suites
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Database (use SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///./printportal.db
# DATABASE_URL=postgresql://user:pass@localhost/printportal

# Security
SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Development settings
DEBUG=true
LOG_LEVEL=INFO

# LDAP (optional - for Active Directory integration)
LDAP_ENABLED=false
LDAP_SERVER=ldap://your-domain-controller
LDAP_BIND_DN=CN=admin,DC=company,DC=com
LDAP_BIND_PASSWORD=password
LDAP_SEARCH_BASE=DC=company,DC=com

# Agent Configuration
AGENT_UPDATE_INTERVAL=300
AGENT_OFFLINE_CACHE_DAYS=7
```

### Available VS Code Tasks

The project includes several VS Code tasks for development:

- **Start API Server**: Launches the FastAPI backend
- **Start Web Portal**: Serves the frontend on port 8080
- **Run Tests**: Executes the test suite
- **Format Code**: Runs Black formatter on Python code
- **Lint Code**: Runs Flake8 linting
- **Database Migration**: Applies database migrations
- **Build Agent**: Compiles the Windows agent

## 📊 Features

### Print Job Tracking
- Username and computer identification
- Printer details (name, IP, location)
- Document metadata (name, pages, copies)
- Print settings (duplex, color/BW)
- Timestamp and site information

### Web Portal
- Real-time dashboard with filtering
- Export capabilities (CSV, Excel)
- User and printer management
- Agent status monitoring
- Statistical reports and analytics

### Security & Authentication
- LDAP/AD integration with SSO
- Role-based access control
- API key management
- Audit logging
- Encrypted communications

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

### API Testing
The API documentation is available at `http://localhost:8000/docs` when the server is running. You can test all endpoints interactively using the Swagger UI.

### Manual Testing
```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "admin123"}'

# Test print jobs endpoint
curl -X GET "http://localhost:8000/api/v1/print-jobs/" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🚀 Deployment

For production deployment, see the comprehensive [Deployment Guide](docs/deployment.md).

### Quick Production Setup
1. Set up PostgreSQL database
2. Configure environment variables for production
3. Use systemd service for the API server
4. Set up nginx reverse proxy
5. Deploy agents via Group Policy or manual installation

## 🔍 Monitoring

### Application Logs
- Backend logs: `backend/logs/app.log` and `backend/logs/error.log`
- Agent logs: Stored locally on each machine and synced to server

### Health Checks
- API Health: `GET /health`
- Database Status: `GET /api/v1/health/db`
- Agent Status: Monitored via last-seen timestamps

## 🛠️ Development

### Code Quality Tools
- **Black**: Code formatting (`python -m black backend/ agent/`)
- **Flake8**: Linting (`python -m flake8 backend/ agent/`)
- **Pytest**: Testing framework
- **Alembic**: Database migrations

### Project Structure
```
backend/app/
├── api/v1/endpoints/    # API route handlers
├── core/               # Configuration, database, logging
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── services/           # Business logic
└── utils/              # Utilities and seeders
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

Open source - see LICENSE file for details.

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: Create GitHub issues for bugs
- Discussions: Use GitHub discussions for questions
