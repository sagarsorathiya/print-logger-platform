# Git Setup and Push Guide

## 📋 Prerequisites

### 1. Install Git (if not already installed)
- **Windows**: Download from https://git-scm.com/download/win
- **Linux**: `sudo apt install git` or `sudo yum install git`
- **macOS**: `brew install git` or download from https://git-scm.com/

### 2. Configure Git (first time only)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🚀 Push to GitHub

### Option 1: Create New Repository on GitHub
1. Go to https://github.com
2. Click "New Repository" (green button)
3. Name it: `distributed-print-tracking-portal`
4. Make it **Public** or **Private** (your choice)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create Repository"

### Option 2: Push to Existing Repository
If you already have a repository, note its URL.

## 📤 Commands to Push Your Project

Copy and paste these commands in your terminal (from the project directory):

### Initialize Git and Add Files
```bash
# Navigate to project directory
cd "D:\Printer_Count_Portal"

# Initialize Git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Complete Distributed Print Tracking Portal

- Backend API with FastAPI and PostgreSQL
- Frontend web dashboard with authentication
- Windows print monitoring agent
- One-click deployment scripts (Windows/Linux)
- Comprehensive documentation and deployment guide
- Production-ready with security, monitoring, and scaling"
```

### Connect to Your GitHub Repository
```bash
# Replace YOUR_USERNAME and YOUR_REPO_NAME with your actual values
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 📋 Complete Command Sequence

**Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub details:**

```bash
cd "D:\Printer_Count_Portal"
git init
git add .
git commit -m "Initial commit: Complete Distributed Print Tracking Portal"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## 🔐 Authentication Options

### Option 1: Personal Access Token (Recommended)
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when prompted

### Option 2: GitHub CLI
```bash
# Install GitHub CLI first: https://cli.github.com/
gh auth login
gh repo create distributed-print-tracking-portal --public --source=. --remote=origin --push
```

### Option 3: SSH Keys
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Then use SSH URL instead of HTTPS
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
```

## 📊 Repository Structure

Your repository will include:
```
distributed-print-tracking-portal/
├── README.md                    # Project overview and quick start
├── DEPLOYMENT_SUMMARY.md       # Documentation summary
├── deploy.sh                   # Linux one-click deployment
├── deploy.bat                  # Windows one-click deployment
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── backend/                    # FastAPI backend
├── frontend/                   # Web dashboard
├── agent/                      # Windows print agent
├── docs/                       # Comprehensive documentation
├── scripts/                    # Production scripts
└── tests/                      # Test suites
```

## 🎯 After Pushing

Once pushed, your repository will be accessible at:
`https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`

You can then:
1. Share the repository URL with others
2. Clone it on other machines: `git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`
3. Set up GitHub Actions for CI/CD (optional)
4. Create releases for stable versions

## 🔄 Future Updates

To push future changes:
```bash
git add .
git commit -m "Description of your changes"
git push
```

## 🆘 Troubleshooting

**Git not found**: Install Git from https://git-scm.com/
**Authentication failed**: Use personal access token instead of password
**Repository exists**: Use `git remote set-url origin NEW_URL` to change remote URL
**Large files**: Use Git LFS for files >100MB (not needed for this project)

## 📞 Support

If you encounter issues:
1. Check that Git is installed: `git --version`
2. Verify you're in the right directory: `pwd` (Linux/macOS) or `cd` (Windows)
3. Check Git status: `git status`
4. Review GitHub's documentation: https://docs.github.com/
