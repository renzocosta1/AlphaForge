"""
AlphaForge Configuration Management
Handles all configuration settings, API keys, and application parameters.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

class Config:
    """Main configuration class for AlphaForge application."""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load all configuration settings from environment variables."""
        
        # API Keys
        self.FMP_API_KEY = os.getenv('FMP_API_KEY', '')
        self.ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        
        # SEC EDGAR settings
        self.SEC_EDGAR_USER_AGENT = os.getenv('SEC_EDGAR_USER_AGENT', 'AlphaForge/1.0')
        
        # Application settings
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Rate limiting (requests per minute)
        self.YFINANCE_RATE_LIMIT = int(os.getenv('YFINANCE_RATE_LIMIT', '60'))
        self.SEC_EDGAR_RATE_LIMIT = int(os.getenv('SEC_EDGAR_RATE_LIMIT', '10'))
        self.FMP_RATE_LIMIT = int(os.getenv('FMP_RATE_LIMIT', '300'))
        self.ALPHA_VANTAGE_RATE_LIMIT = int(os.getenv('ALPHA_VANTAGE_RATE_LIMIT', '5'))
        
        # Database settings
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', './data/alphaforge.db')
        
        # File storage settings
        self.FILINGS_DIR = os.getenv('FILINGS_DIR', './data/filings')
        self.EXPORT_DIR = os.getenv('EXPORT_DIR', './exports')
        
        # Quality filter thresholds
        self.MAX_DEBT_TO_EBITDA = float(os.getenv('MAX_DEBT_TO_EBITDA', '5.0'))
        self.MIN_TRADING_VOLUME = int(os.getenv('MIN_TRADING_VOLUME', '50000'))
        self.FCF_NEGATIVE_YEARS_THRESHOLD = int(os.getenv('FCF_NEGATIVE_YEARS_THRESHOLD', '4'))
        self.OPERATING_INCOME_NEGATIVE_YEARS_THRESHOLD = int(os.getenv('OPERATING_INCOME_NEGATIVE_YEARS_THRESHOLD', '4'))
        
        # Scoring weights
        self.SCORE_SEC_FILING_PENALTY = int(os.getenv('SCORE_SEC_FILING_PENALTY', '-20'))
        self.SCORE_FCF_PENALTY = int(os.getenv('SCORE_FCF_PENALTY', '-10'))
        self.SCORE_OPERATING_LOSS_PENALTY = int(os.getenv('SCORE_OPERATING_LOSS_PENALTY', '-8'))
        self.SCORE_HIGH_DEBT_PENALTY = int(os.getenv('SCORE_HIGH_DEBT_PENALTY', '-15'))
        self.SCORE_NEGATIVE_EQUITY_PENALTY = int(os.getenv('SCORE_NEGATIVE_EQUITY_PENALTY', '-12'))
        self.SCORE_LOW_VOLUME_PENALTY = int(os.getenv('SCORE_LOW_VOLUME_PENALTY', '-5'))
        self.SCORE_OTC_PENALTY = int(os.getenv('SCORE_OTC_PENALTY', '-3'))
        self.SCORE_NEWS_RED_FLAG_PENALTY = int(os.getenv('SCORE_NEWS_RED_FLAG_PENALTY', '-7'))
        self.SCORE_CORPORATE_ACTION_PENALTY = int(os.getenv('SCORE_CORPORATE_ACTION_PENALTY', '-5'))
        
        # Create necessary directories
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure all necessary directories exist."""
        directories = [
            os.path.dirname(self.DATABASE_PATH),
            self.FILINGS_DIR,
            self.EXPORT_DIR,
            './logs'
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration for external services."""
        return {
            'fmp_api_key': self.FMP_API_KEY,
            'alpha_vantage_api_key': self.ALPHA_VANTAGE_API_KEY,
            'openai_api_key': self.OPENAI_API_KEY,
            'sec_edgar_user_agent': self.SEC_EDGAR_USER_AGENT,
            'rate_limits': {
                'yfinance': self.YFINANCE_RATE_LIMIT,
                'sec_edgar': self.SEC_EDGAR_RATE_LIMIT,
                'fmp': self.FMP_RATE_LIMIT,
                'alpha_vantage': self.ALPHA_VANTAGE_RATE_LIMIT
            }
        }
    
    def get_filter_config(self) -> Dict[str, Any]:
        """Get quality filter configuration."""
        return {
            'max_debt_to_ebitda': self.MAX_DEBT_TO_EBITDA,
            'min_trading_volume': self.MIN_TRADING_VOLUME,
            'fcf_negative_years_threshold': self.FCF_NEGATIVE_YEARS_THRESHOLD,
            'operating_income_negative_years_threshold': self.OPERATING_INCOME_NEGATIVE_YEARS_THRESHOLD
        }
    
    def get_scoring_config(self) -> Dict[str, int]:
        """Get scoring configuration."""
        return {
            'sec_filing_penalty': self.SCORE_SEC_FILING_PENALTY,
            'fcf_penalty': self.SCORE_FCF_PENALTY,
            'operating_loss_penalty': self.SCORE_OPERATING_LOSS_PENALTY,
            'high_debt_penalty': self.SCORE_HIGH_DEBT_PENALTY,
            'negative_equity_penalty': self.SCORE_NEGATIVE_EQUITY_PENALTY,
            'low_volume_penalty': self.SCORE_LOW_VOLUME_PENALTY,
            'otc_penalty': self.SCORE_OTC_PENALTY,
            'news_red_flag_penalty': self.SCORE_NEWS_RED_FLAG_PENALTY,
            'corporate_action_penalty': self.SCORE_CORPORATE_ACTION_PENALTY
        }

# Global configuration instance
config = Config() 