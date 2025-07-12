# GitHub Setup Guide for AlphaForge

This guide will help you push your AlphaForge codebase to GitHub and set up the remote repository.

## Prerequisites

- Git installed and configured
- GitHub account
- Local AlphaForge repository (already created)

## Step 1: Create GitHub Repository

### Option A: Via GitHub Website
1. Go to https://github.com
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the repository details:
   - **Repository name**: `AlphaForge`
   - **Description**: `Automated investment screening application implementing Ted Weschler's quality filters`
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### Option B: Via GitHub CLI (if installed)
```bash
# Install GitHub CLI if not already installed
# On macOS: brew install gh
# On Windows: winget install --id GitHub.cli

# Authenticate with GitHub
gh auth login

# Create repository
gh repo create AlphaForge --public --description "Automated investment screening application implementing Ted Weschler's quality filters"
```

## Step 2: Connect Local Repository to GitHub

### Add Remote Origin
```bash
# Replace 'yourusername' with your GitHub username
git remote add origin https://github.com/yourusername/AlphaForge.git
```

### Verify Remote
```bash
git remote -v
```

You should see:
```
origin  https://github.com/yourusername/AlphaForge.git (fetch)
origin  https://github.com/yourusername/AlphaForge.git (push)
```

## Step 3: Push to GitHub

### Push to Main Branch
```bash
# Rename master to main (GitHub's default)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Verify Push
Go to your GitHub repository URL and verify that all files are present.

## Step 4: Set Up Branch Protection (Optional)

### Via GitHub Website
1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Branches" in the left sidebar
4. Click "Add rule"
5. Configure branch protection:
   - **Branch name pattern**: `main`
   - Check "Require pull request reviews before merging"
   - Check "Require status checks to pass before merging"
   - Check "Restrict pushes to matching branches"

## Step 5: GitHub Repository Settings

### Update Repository Description
1. Go to your repository's main page
2. Click the gear icon next to "About"
3. Add:
   - **Description**: `Automated investment screening application implementing Ted Weschler's quality filters`
   - **Website**: (if you have one)
   - **Topics**: `python`, `pyqt6`, `investment`, `finance`, `screening`, `stocks`, `sec-edgar`, `yahoo-finance`

### Add Repository Badges
Update your README.md to include the repository URL in badges:
```markdown
[![GitHub stars](https://img.shields.io/github/stars/yourusername/AlphaForge.svg)](https://github.com/yourusername/AlphaForge/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/AlphaForge.svg)](https://github.com/yourusername/AlphaForge/network)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/AlphaForge.svg)](https://github.com/yourusername/AlphaForge/issues)
```

## Step 6: Set Up GitHub Actions (Optional)

Create `.github/workflows/ci.yml` for continuous integration:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## Step 7: Development Workflow

### Daily Development
```bash
# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your meaningful commit message"

# Push feature branch
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Commit Message Convention
Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test additions or changes
- `chore:` - Maintenance tasks

## Step 8: Collaborating Across Platforms

### Cloning on Mac
```bash
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the application
python main.py
```

### Cloning on Windows
```powershell
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Set up development environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run the application
python main.py
```

### Cloning on Linux
```bash
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install system dependencies if needed
sudo apt-get install python3-pyqt6  # Ubuntu/Debian

# Run the application
python main.py
```

## Step 9: GitHub Issues and Project Management

### Create Issue Templates
Create `.github/ISSUE_TEMPLATE/bug_report.md`:
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. macOS 12.0, Windows 11]
- Python Version: [e.g. 3.9.7]
- AlphaForge Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

### Set Up GitHub Projects
1. Go to your repository
2. Click "Projects" tab
3. Click "New project"
4. Choose "Board" template
5. Create columns: "To Do", "In Progress", "Done"
6. Add issues to organize development

## Step 10: Release Management

### Create Releases
```bash
# Tag a release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### GitHub Release
1. Go to your repository
2. Click "Releases"
3. Click "Create a new release"
4. Fill in release information:
   - **Tag version**: v1.0.0
   - **Release title**: AlphaForge v1.0.0
   - **Description**: Include changelog and features
   - **Assets**: Upload any distribution files

## Troubleshooting

### Authentication Issues
```bash
# Use personal access token instead of password
# GitHub Settings > Developer settings > Personal access tokens
# Use token as password when prompted
```

### Large Files
```bash
# Install Git LFS for large files
git lfs install
git lfs track "*.db"
git lfs track "*.log"
git add .gitattributes
```

### Repository Size
```bash
# Check repository size
git count-objects -vH

# Remove large files from history (if needed)
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

## Security Considerations

### Secrets Management
- Never commit API keys, passwords, or sensitive data
- Use GitHub Secrets for CI/CD
- Review .gitignore regularly

### Code Scanning
- Enable GitHub's security features
- Use Dependabot for dependency updates
- Set up code scanning alerts

---

**Repository URL**: https://github.com/yourusername/AlphaForge  
**Last Updated**: 2025-01-12  
**Next Steps**: Set up continuous integration and deployment 