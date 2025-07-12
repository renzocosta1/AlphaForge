# AlphaForge Mac Development Setup

This guide will help you set up AlphaForge for development on macOS.

## Prerequisites

### 1. Install Xcode Command Line Tools
```bash
xcode-select --install
```

### 2. Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. Install Python 3.9+
```bash
# Install Python 3.9 (or latest)
brew install python@3.9

# Verify installation
python3 --version
```

### 4. Install Git (if not already installed)
```bash
brew install git
```

## Project Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Configuration
```bash
# Create a .env file for environment variables
cp .env.example .env  # If example exists
# Or create manually:
touch .env
```

Add the following to your `.env` file:
```env
# Database Configuration
DATABASE_PATH=./data/alphaforge.db

# Logging Configuration
LOG_LEVEL=INFO

# API Keys (optional)
# FINANCIAL_MODELING_PREP_API_KEY=your_key_here
# ALPHA_VANTAGE_API_KEY=your_key_here
```

## Running the Application

### 1. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 2. Run AlphaForge
```bash
python main.py
```

## Development Tools

### Recommended IDE Setup
1. **Visual Studio Code**
   ```bash
   brew install --cask visual-studio-code
   ```

2. **PyCharm Community Edition**
   ```bash
   brew install --cask pycharm-ce
   ```

### Python Development Extensions (VS Code)
- Python
- Python Docstring Generator
- autopep8
- Black Formatter
- isort

## Troubleshooting

### Common Issues

#### Issue: PyQt6 Installation Problems
```bash
# Try installing with brew first
brew install pyqt6

# Or install via pip with specific flags
pip install PyQt6 --config-settings --confirm-license= --verbose
```

#### Issue: Permission Denied for Database
```bash
# Ensure data directory exists and has proper permissions
mkdir -p data
chmod 755 data
```

#### Issue: SSL Certificate Errors
```bash
# Update certificates
brew upgrade ca-certificates
```

#### Issue: Python Path Issues
```bash
# Check Python path
which python3

# Verify virtual environment is active
echo $VIRTUAL_ENV
```

### Environment Variables
Create a `.env` file in the project root:
```env
# Database
DATABASE_PATH=./data/alphaforge.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/alphaforge.log

# API Configuration
API_TIMEOUT=30
RATE_LIMIT_DELAY=1

# GUI Configuration
GUI_THEME=default
```

## Platform-Specific Considerations

### macOS Differences from Windows
1. **File Paths**: Use forward slashes (`/`) instead of backslashes (`\`)
2. **Virtual Environment**: Use `source .venv/bin/activate` instead of `.venv\Scripts\activate`
3. **Python Command**: Use `python3` instead of `python`
4. **Package Management**: May need to use `pip3` instead of `pip`

### Directory Structure
```
AlphaForge/
├── .venv/                 # Virtual environment (ignored by git)
├── data/                  # Database and cache files
│   ├── alphaforge.db     # SQLite database
│   └── filings/          # SEC filing cache
├── logs/                  # Application logs
└── [other project files]
```

## Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Manual Testing Checklist
- [ ] Application launches without errors
- [ ] CSV import functionality works
- [ ] Database operations succeed
- [ ] GUI is responsive
- [ ] All filters execute properly

## Development Workflow

### 1. Daily Development
```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 2. Before Committing
```bash
# Format code
black .

# Sort imports
isort .

# Run tests
pytest tests/

# Check for issues
flake8 .
```

### 3. Commit Changes
```bash
git add .
git commit -m "feat: your meaningful commit message"
git push origin your-branch
```

## Performance Optimization

### macOS-Specific Optimizations
1. **Use System Python**: Consider using system Python for better performance
2. **Enable Metal**: PyQt6 should use Metal for better graphics performance
3. **Memory Management**: Monitor memory usage with Activity Monitor

### Database Optimization
```bash
# Optimize SQLite database
sqlite3 data/alphaforge.db "VACUUM; ANALYZE;"
```

## Security Considerations

### API Key Management
```bash
# Never commit API keys to git
echo "*.env" >> .gitignore
echo "secrets.txt" >> .gitignore
```

### File Permissions
```bash
# Secure sensitive files
chmod 600 .env
chmod 700 data/
```

## Deployment

### Creating a Distribution
```bash
# Install build tools
pip install pyinstaller

# Create executable
pyinstaller --onedir --windowed main.py

# The app will be in dist/main/
```

### App Bundle (macOS)
```bash
# Create macOS app bundle
pyinstaller --onedir --windowed --name AlphaForge main.py

# Sign the app (requires Apple Developer account)
# codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/AlphaForge.app
```

## Maintenance

### Regular Tasks
1. **Update Dependencies**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

2. **Clean Cache**
   ```bash
   find . -name "__pycache__" -type d -exec rm -rf {} +
   find . -name "*.pyc" -delete
   ```

3. **Database Maintenance**
   ```bash
   # Backup database
   cp data/alphaforge.db data/alphaforge.db.backup
   
   # Optimize database
   sqlite3 data/alphaforge.db "VACUUM; REINDEX;"
   ```

## Support

### Getting Help
1. Check the main README.md
2. Review DEVELOPMENT_STATUS.md for known issues
3. Open an issue on GitHub
4. Check the troubleshooting section above

### System Requirements
- macOS 10.14 or later
- Python 3.9 or later
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space
- Internet connection for data fetching

---

**Last Updated**: 2025-01-12  
**Platform**: macOS  
**Python Version**: 3.9+ 