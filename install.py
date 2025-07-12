#!/usr/bin/env python3
"""
AlphaForge Installation Script
Helps users set up the application quickly and correctly.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print the AlphaForge banner."""
    print("=" * 60)
    print("     AlphaForge - Investment Research Automation")
    print("        Installation and Setup Script")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ ERROR: Python 3.9 or higher is required.")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please upgrade Python and try again.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_platform():
    """Check if platform is supported."""
    print("Checking platform compatibility...")
    
    system = platform.system()
    print(f"✅ Platform: {system} {platform.release()}")
    
    if system == "Windows":
        print("   Primary development platform - full support")
    elif system in ["Darwin", "Linux"]:
        print("   Secondary platform - should work but not fully tested")
    else:
        print("   ⚠️  Unsupported platform - may experience issues")
    
    return True

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    
    try:
        # Upgrade pip first
        print("   Upgrading pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        print("   Installing requirements from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ ERROR: Failed to install dependencies")
        print(f"   Error: {e}")
        return False
    except FileNotFoundError:
        print("❌ ERROR: requirements.txt not found")
        return False

def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = [
        "data",
        "data/filings",
        "exports",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}/")
    
    print("✅ Directories created successfully")
    return True

def create_env_file():
    """Create .env file from template."""
    print("Setting up configuration...")
    
    env_content = """# AlphaForge Configuration
# Edit these values as needed

# SEC EDGAR API settings (REQUIRED)
SEC_EDGAR_USER_AGENT=AlphaForge/1.0 (your_email@example.com)

# Optional API Keys (leave empty if not using)
FMP_API_KEY=
ALPHA_VANTAGE_API_KEY=
OPENAI_API_KEY=

# Application settings
DEBUG=False
LOG_LEVEL=INFO

# Rate limiting settings (requests per minute)
YFINANCE_RATE_LIMIT=60
SEC_EDGAR_RATE_LIMIT=10
FMP_RATE_LIMIT=300
ALPHA_VANTAGE_RATE_LIMIT=5

# Database settings
DATABASE_PATH=./data/alphaforge.db

# File storage settings
FILINGS_DIR=./data/filings
EXPORT_DIR=./exports

# Quality filter thresholds
MAX_DEBT_TO_EBITDA=5.0
MIN_TRADING_VOLUME=50000
FCF_NEGATIVE_YEARS_THRESHOLD=4
OPERATING_INCOME_NEGATIVE_YEARS_THRESHOLD=4

# Scoring weights
SCORE_SEC_FILING_PENALTY=-20
SCORE_FCF_PENALTY=-10
SCORE_OPERATING_LOSS_PENALTY=-8
SCORE_HIGH_DEBT_PENALTY=-15
SCORE_NEGATIVE_EQUITY_PENALTY=-12
SCORE_LOW_VOLUME_PENALTY=-5
SCORE_OTC_PENALTY=-3
SCORE_NEWS_RED_FLAG_PENALTY=-7
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("   .env file already exists - skipping")
    else:
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("   ⚠️  IMPORTANT: Edit .env file with your email address for SEC EDGAR access")
    
    return True

def test_installation():
    """Test the installation by importing modules."""
    print("Testing installation...")
    
    try:
        # Test critical imports
        import PyQt5.QtWidgets
        print("   ✅ PyQt5 imported successfully")
        
        import pandas
        print("   ✅ pandas imported successfully")
        
        import yfinance
        print("   ✅ yfinance imported successfully")
        
        import requests
        print("   ✅ requests imported successfully")
        
        # Test our modules
        from config import config
        print("   ✅ Configuration module loaded")
        
        from database.schema import DatabaseManager
        print("   ✅ Database module loaded")
        
        print("✅ Installation test passed")
        return True
        
    except ImportError as e:
        print(f"❌ ERROR: Import failed - {e}")
        return False

def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "=" * 60)
    print("                  INSTALLATION COMPLETE")
    print("=" * 60)
    print()
    print("🎉 AlphaForge has been installed successfully!")
    print()
    print("NEXT STEPS:")
    print()
    print("1. CONFIGURE SEC EDGAR ACCESS:")
    print("   • Open the .env file in a text editor")
    print("   • Replace 'your_email@example.com' with your actual email")
    print("   • This is required for SEC EDGAR API access")
    print()
    print("2. PREPARE YOUR DATA:")
    print("   • Use the sample_companies.csv file as a template")
    print("   • Or create your own CSV with the required columns")
    print()
    print("3. RUN THE APPLICATION:")
    print("   • Execute: python main.py")
    print("   • Click 'Browse' to select your CSV file")
    print("   • Click 'Process Companies' to start analysis")
    print()
    print("4. OPTIONAL API KEYS:")
    print("   • Add Financial Modeling Prep API key for enhanced data")
    print("   • Add Alpha Vantage API key for additional metrics")
    print("   • Add OpenAI API key for AI-powered analysis")
    print()
    print("📚 Read the README.md file for detailed usage instructions")
    print("🐛 Check the logs/ directory if you encounter any issues")
    print()
    print("Happy investing! 📈")

def main():
    """Main installation function."""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_platform():
        return False
    
    # Install components
    if not install_dependencies():
        return False
    
    if not create_directories():
        return False
    
    if not create_env_file():
        return False
    
    if not test_installation():
        return False
    
    print_next_steps()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        sys.exit(1) 