# AlphaForge - Automated Investment Screening Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AlphaForge is a sophisticated investment screening application that implements Ted Weschler's quality filters for systematic stock analysis. It's designed as an "Automated Mini Deep Dive" tool that helps identify high-quality investment opportunities through comprehensive quantitative and qualitative screening.

## 🏗️ Architecture

### Core Components
- **GUI Interface** (`gui/main_window.py`) - PyQt6-based desktop application
- **Data Fetcher** (`data_ingestion/data_fetcher.py`) - Yahoo Finance API integration
- **Quality Filters** (`quality_filters/weschler_filters.py`) - Ted Weschler's investment criteria
- **SEC Filing Processor** (`sec_filings/edgar_processor.py`) - SEC EDGAR API integration
- **Database Layer** (`database/schema.py`) - SQLite database management
- **Configuration** (`config.py`) - Centralized configuration management

### Technology Stack
- **Python 3.9+** with PyQt6 for GUI
- **SQLite** for local data storage and caching
- **yfinance** for stock data retrieval
- **pandas/numpy** for data analysis
- **requests** for API calls
- **Beautiful Soup** for web scraping (SEC data)

## 🔧 Features

### Implemented Features
- ✅ CSV-Based Company Input - Process lists of companies from Excel/CSV files
- ✅ Comprehensive Data Fetching - Stock prices, market cap, financials, SEC filings
- ✅ Ted Weschler Quality Filters:
  - SEC filing compliance checks
  - Free cash flow consistency analysis
  - Operating income trends
  - Debt analysis (Net Debt/EBITDA ratios)
  - Balance sheet strength
  - Trading volume liquidity
  - Exchange listing requirements
  - News sentiment red flags
- ✅ Quality Scoring System - 100-point scale with configurable penalties
- ✅ GUI Features:
  - Company processing with progress tracking
  - Sortable results table with key metrics visible
  - Red flags display for manual review
  - Session-based filtering (only shows current CSV companies)

### Current Issues
- ⚠️ Corporate Action Detection System needs integration debugging
- ⚠️ Companies with stock splits/reverse splits (SITE, XXII) need proper flagging

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Git (for version control)

### Installation

#### Windows
```powershell
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### macOS
```bash
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Linux
```bash
# Clone the repository
git clone https://github.com/yourusername/AlphaForge.git
cd AlphaForge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For GUI support on Linux, you might need:
sudo apt-get install python3-pyqt6

# Run the application
python main.py
```

## 📁 Project Structure

```
AlphaForge/
├── ai_analysis/           # AI-powered analysis modules
├── data/                  # Data storage directory
│   ├── alphaforge.db     # SQLite database (auto-generated)
│   └── filings/          # SEC filings cache
├── data_ingestion/        # Data fetching modules
├── database/              # Database schema and management
├── exports/               # Export directory for results
├── gui/                   # PyQt6 GUI components
├── logs/                  # Application logs
├── quality_filters/       # Investment screening filters
├── sec_filings/          # SEC data processing
├── utils/                # Utility functions
├── config.py             # Configuration management
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## ⚙️ Configuration

The application uses `config.py` for centralized configuration management:

- **Scoring Penalties**: SEC filing (-20), FCF (-10), Corporate Action (-5)
- **Filter Thresholds**: Debt ratios, volume minimums, etc.
- **API Rate Limiting**: Configurable delays between requests
- **Database Paths**: SQLite database location

### Environment Variables
Create a `.env` file in the project root for sensitive configuration:
```env
# API Keys (if needed for premium data sources)
FINANCIAL_MODELING_PREP_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here

# Database Configuration
DATABASE_PATH=./data/alphaforge.db

# Logging Configuration
LOG_LEVEL=INFO
```

## 🖥️ Cross-Platform Development

### Mac Development Setup
1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.9+**:
   ```bash
   brew install python@3.9
   ```

3. **Install Git**:
   ```bash
   brew install git
   ```

4. **Clone and Setup**:
   ```bash
   git clone https://github.com/yourusername/AlphaForge.git
   cd AlphaForge
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### Platform-Specific Notes

#### Windows
- Uses PowerShell for terminal commands
- Virtual environment activation: `.venv\Scripts\activate`
- File paths use backslashes

#### macOS
- Uses Terminal/zsh for commands
- Virtual environment activation: `source .venv/bin/activate`
- File paths use forward slashes
- May require Xcode Command Line Tools for some dependencies

#### Linux
- Additional system packages may be required for PyQt6
- Virtual environment activation: `source .venv/bin/activate`
- File paths use forward slashes

## 🔍 Usage

1. **Prepare Input Data**: Create a CSV file with company tickers in the first column
2. **Launch Application**: Run `python main.py`
3. **Load Companies**: Use the GUI to import your CSV file
4. **Configure Filters**: Adjust quality filter thresholds in the settings
5. **Run Analysis**: Click "Process Companies" to begin screening
6. **Review Results**: Examine the results table and red flags
7. **Export Data**: Save results to Excel or CSV format

## 📊 Quality Scoring System

The application uses a 100-point scoring system with penalties for various risk factors:

- **SEC Filing Issues**: -20 points
- **Free Cash Flow Problems**: -10 points
- **Corporate Actions**: -5 points
- **Debt Concerns**: Variable based on severity
- **Liquidity Issues**: Variable based on trading volume

## 🛠️ Development

### Setting Up Development Environment

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/yourusername/AlphaForge.git
   cd AlphaForge
   ```

2. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Tests** (when available):
   ```bash
   pytest tests/
   ```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Known Issues

- Corporate action detection system needs integration debugging
- Some companies with stock splits (SITE, XXII) may not be properly flagged
- Rate limiting may need adjustment for high-volume processing

## 🔮 Future Enhancements

- [ ] Enhanced corporate action detection
- [ ] Real-time data streaming
- [ ] Advanced screening algorithms
- [ ] Portfolio optimization features
- [ ] API for programmatic access
- [ ] Web-based interface
- [ ] Machine learning integration

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

**Note**: This tool is for educational and research purposes only. It should not be used as the sole basis for investment decisions. Always consult with a qualified financial advisor before making investment decisions. 