"""
Logging utility for AlphaForge application.
Provides centralized logging configuration and setup.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO"):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = "./logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler with rotation
    log_filename = f"alphaforge_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    
    file_handler = RotatingFileHandler(
        log_filepath,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Create separate handler for errors
    error_log_filename = f"alphaforge_errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_log_filepath = os.path.join(logs_dir, error_log_filename)
    
    error_handler = RotatingFileHandler(
        error_log_filepath,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging setup completed with level: {log_level}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name) 