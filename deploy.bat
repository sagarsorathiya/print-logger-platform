@echo off
REM One-Click Deployment Script for Print Tracking Portal (Windows)
REM Usage: deploy.bat [development|production]

setlocal enabledelayedexpansion

REM Configuration
set "DEPLOY_MODE=%~1"
if "%DEPLOY_MODE%"=="" set "DEPLOY_MODE=development"
set "PROJECT_NAME=printportal"
set "DOMAIN=%DOMAIN%"
if "%DOMAIN%"=="" set "DOMAIN=localhost"

echo === Print Tracking Portal Deployment ===
echo Mode: %DEPLOY_MODE%
echo Domain: %DOMAIN%
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" rmdir /s /q venv
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo [INFO] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Generate environment configuration
echo [INFO] Creating environment configuration...

REM Generate secret key using PowerShell
for /f "delims=" %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(32, 8)"') do set "SECRET_KEY=%%i"

REM Create .env file
(
echo # Database Configuration
echo DATABASE_URL=sqlite:///./printportal.db
echo.
echo # Security Settings
echo SECRET_KEY=%SECRET_KEY%
echo DEBUG=true
echo JWT_ALGORITHM=HS256
echo ACCESS_TOKEN_EXPIRE_MINUTES=480
echo.
echo # CORS and Security
echo CORS_ORIGINS=["http://localhost:8080","http://%DOMAIN%:8080"]
echo ALLOWED_HOSTS=["localhost","%DOMAIN%"]
echo.
echo # Logging
echo LOG_LEVEL=INFO
echo.
echo # LDAP Configuration (disabled by default^)
echo LDAP_ENABLED=false
echo.
echo # Agent Settings
echo AGENT_UPDATE_INTERVAL=300
echo AGENT_OFFLINE_CACHE_DAYS=7
) > .env

echo [SUCCESS] Environment configuration created

REM Initialize database
echo [INFO] Initializing database...
python setup_db.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)

echo [SUCCESS] Database initialized

REM Test the installation
echo [INFO] Testing installation...
timeout /t 2 /nobreak >nul

REM Check if we can import the main module
python -c "from backend.main import app; print('Import test passed')"
if %errorlevel% neq 0 (
    echo [ERROR] Import test failed
    pause
    exit /b 1
)

echo [SUCCESS] Installation test passed

REM Create start scripts
echo [INFO] Creating start scripts...

REM Create start_api.bat
(
echo @echo off
echo echo Starting Print Portal API Server...
echo call venv\Scripts\activate.bat
echo python -m uvicorn backend.main:app --reload --port 8000
echo pause
) > start_api.bat

REM Create start_web.bat
(
echo @echo off
echo echo Starting Print Portal Web Server...
echo cd frontend
echo python -m http.server 8080
echo pause
) > start_web.bat

REM Create start_all.bat
(
echo @echo off
echo echo Starting Print Portal...
echo echo.
echo echo Starting API Server in new window...
echo start "Print Portal API" start_api.bat
echo.
echo echo Waiting 5 seconds for API to start...
echo timeout /t 5 /nobreak ^>nul
echo.
echo echo Starting Web Server in new window...
echo start "Print Portal Web" start_web.bat
echo.
echo echo Print Portal is starting...
echo echo API URL: http://localhost:8000/docs
echo echo Web URL: http://localhost:8080
echo echo.
echo echo Login credentials:
echo echo Email: admin@example.com
echo echo Password: admin123
echo echo.
echo echo Press any key to open web browser...
echo pause ^>nul
echo start http://localhost:8080
) > start_all.bat

echo [SUCCESS] Start scripts created

REM Create test script for agent
echo [INFO] Creating agent test script...
(
echo @echo off
echo echo Testing Print Portal Agent...
echo call venv\Scripts\activate.bat
echo cd agent
echo python demo.py
echo pause
) > test_agent.bat

REM Display completion information
echo.
echo === Deployment Completed Successfully! ===
echo.
echo Mode: %DEPLOY_MODE%
echo Domain: %DOMAIN%
echo Database: SQLite (printportal.db)
echo.
echo Available Scripts:
echo   start_all.bat     - Start both API and Web servers
echo   start_api.bat     - Start only API server
echo   start_web.bat     - Start only Web server
echo   test_agent.bat    - Test agent functionality
echo.
echo URLs:
echo   Web Portal: http://localhost:8080
echo   API Docs:   http://localhost:8000/docs
echo.
echo Default Admin Login:
echo   Email:    admin@example.com
echo   Password: admin123
echo.
echo Next Steps:
echo   1. Run 'start_all.bat' to start the portal
echo   2. Change default admin password
echo   3. Test agent with 'test_agent.bat'
echo   4. Configure LDAP/AD integration (if needed)
echo   5. Deploy agents to Windows machines
echo.
echo VS Code Tasks (if using VS Code):
echo   - Ctrl+Shift+P -> Tasks: Run Task
echo   - Select "Start API Server" or "Start Web Portal"
echo.

REM Ask if user wants to start the portal now
echo Do you want to start the Print Portal now? (Y/N)
set /p "START_NOW="
if /i "%START_NOW%"=="Y" (
    echo Starting Print Portal...
    start_all.bat
) else (
    echo Run 'start_all.bat' when ready to start the portal
)

echo.
echo Deployment completed! Press any key to exit.
pause >nul
