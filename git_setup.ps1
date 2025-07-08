#!/usr/bin/env pwsh
# Git Setup Script for Print Tracking Portal
# Usage: .\git_setup.ps1 -Username "yourusername" -RepoName "your-repo-name"

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$RepoName,
    
    [string]$Branch = "main",
    [switch]$CreateRepo
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-ColorText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Test-GitInstalled {
    try {
        $gitVersion = git --version
        Write-ColorText "✓ Git found: $gitVersion" $Green
        return $true
    }
    catch {
        Write-ColorText "✗ Git not found. Please install Git from https://git-scm.com/" $Red
        return $false
    }
}

function Test-InProjectDirectory {
    if (Test-Path "requirements.txt" -And Test-Path "backend" -And Test-Path "frontend") {
        Write-ColorText "✓ In correct project directory" $Green
        return $true
    }
    else {
        Write-ColorText "✗ Not in project directory. Please run from Print_Count_Portal folder." $Red
        return $false
    }
}

function Initialize-GitRepo {
    Write-ColorText "🔧 Initializing Git repository..." $Blue
    
    # Initialize git if not already done
    if (-not (Test-Path ".git")) {
        git init
        Write-ColorText "✓ Git repository initialized" $Green
    } else {
        Write-ColorText "✓ Git repository already exists" $Green
    }
    
    # Add all files
    Write-ColorText "📁 Adding files to Git..." $Blue
    git add .
    
    # Create commit
    $commitMessage = @"
Initial commit: Complete Distributed Print Tracking Portal

- Backend API with FastAPI and PostgreSQL
- Frontend web dashboard with authentication  
- Windows print monitoring agent
- One-click deployment scripts (Windows/Linux)
- Comprehensive documentation and deployment guide
- Production-ready with security, monitoring, and scaling
"@
    
    git commit -m $commitMessage
    Write-ColorText "✓ Initial commit created" $Green
}

function Add-RemoteOrigin {
    param([string]$Username, [string]$RepoName)
    
    $repoUrl = "https://github.com/$Username/$RepoName.git"
    
    Write-ColorText "🔗 Adding remote origin: $repoUrl" $Blue
    
    # Remove existing origin if it exists
    git remote remove origin 2>$null
    
    # Add new origin
    git remote add origin $repoUrl
    Write-ColorText "✓ Remote origin added" $Green
    
    return $repoUrl
}

function Push-ToGitHub {
    param([string]$Branch)
    
    Write-ColorText "🚀 Pushing to GitHub..." $Blue
    
    try {
        git branch -M $Branch
        git push -u origin $Branch
        Write-ColorText "✓ Successfully pushed to GitHub!" $Green
        return $true
    }
    catch {
        Write-ColorText "✗ Push failed. You may need to authenticate." $Red
        Write-ColorText "💡 Try using a Personal Access Token as your password" $Yellow
        return $false
    }
}

function Show-NextSteps {
    param([string]$Username, [string]$RepoName)
    
    $repoUrl = "https://github.com/$Username/$RepoName"
    
    Write-ColorText "`n🎉 Git setup completed!" $Green
    Write-ColorText "📍 Repository URL: $repoUrl" $Blue
    
    Write-Host "`nNext steps:" -ForegroundColor $Yellow
    Write-Host "1. Visit: $repoUrl"
    Write-Host "2. Verify all files are uploaded correctly"
    Write-Host "3. Update repository description and topics"
    Write-Host "4. Consider adding a license file"
    Write-Host "5. Share the repository with your team"
    
    Write-Host "`nTo make future updates:" -ForegroundColor $Yellow
    Write-Host "git add ."
    Write-Host "git commit -m `"Your commit message`""
    Write-Host "git push"
}

function Main {
    Write-ColorText "=== Git Setup for Print Tracking Portal ===" $Blue
    Write-ColorText "Username: $Username" $Blue
    Write-ColorText "Repository: $RepoName" $Blue
    Write-ColorText "Branch: $Branch" $Blue
    Write-Host ""
    
    # Check prerequisites
    if (-not (Test-GitInstalled)) { exit 1 }
    if (-not (Test-InProjectDirectory)) { exit 1 }
    
    # Initialize repository
    Initialize-GitRepo
    
    # Add remote origin
    $repoUrl = Add-RemoteOrigin -Username $Username -RepoName $RepoName
    
    # Show GitHub setup instructions if repository doesn't exist
    if ($CreateRepo) {
        Write-ColorText "`n📝 Create repository on GitHub:" $Yellow
        Write-Host "1. Go to: https://github.com/new"
        Write-Host "2. Repository name: $RepoName"
        Write-Host "3. Make it Public or Private (your choice)"
        Write-Host "4. DO NOT initialize with README, .gitignore, or license"
        Write-Host "5. Click 'Create Repository'"
        Write-Host "6. Press Enter when done..."
        Read-Host
    }
    
    # Push to GitHub
    $pushSuccess = Push-ToGitHub -Branch $Branch
    
    if ($pushSuccess) {
        Show-NextSteps -Username $Username -RepoName $RepoName
    } else {
        Write-ColorText "`n💡 Authentication Help:" $Yellow
        Write-Host "1. Go to: https://github.com/settings/tokens"
        Write-Host "2. Generate new token (classic)"
        Write-Host "3. Select 'repo' scope"
        Write-Host "4. Use token as password when prompted"
        Write-Host "5. Re-run: git push -u origin $Branch"
    }
}

# Run main function
Main
