"""
AlphaForge - Investment Research Automation Tool
Main application entry point with PyQt5 GUI initialization.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

from config import config
from gui.main_window import MainWindow
from utils.logger import setup_logging

def main():
    """Main entry point for AlphaForge application."""
    
    # Set up logging
    setup_logging(config.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting AlphaForge application...")
    
    # Create QApplication instance
    app = QApplication(sys.argv)
    
    # Set application properties
    QCoreApplication.setApplicationName("AlphaForge")
    QCoreApplication.setApplicationVersion("1.0.0")
    QCoreApplication.setOrganizationName("AlphaForge")
    
    try:
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("AlphaForge application started successfully")
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start AlphaForge application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 