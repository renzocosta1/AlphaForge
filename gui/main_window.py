"""
Main window for AlphaForge GUI application.
Provides the primary interface for investment research automation.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QTabWidget,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QSplitter,
    QHeaderView, QComboBox, QLineEdit, QGroupBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
import logging

from config import config
from database.schema import DatabaseManager, initialize_database
from data_ingestion.data_fetcher import DataFetcher
from quality_filters.weschler_filters import WeschlerQualityFilters
from sec_filings.edgar_processor import EdgarProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

class ProcessingThread(QThread):
    """Background thread for processing companies to keep GUI responsive."""
    
    progress_update = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    processing_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, csv_path: str, db_manager: DatabaseManager):
        super().__init__()
        self.csv_path = csv_path
        self.db_manager = db_manager
        self.is_cancelled = False
    
    def run(self):
        """Run the complete processing pipeline."""
        try:
            self.progress_update.emit("Initializing processing...")
            self.progress_value.emit(0)
            
            # Initialize components
            data_fetcher = DataFetcher(self.db_manager)
            quality_filters = WeschlerQualityFilters(self.db_manager)
            edgar_processor = EdgarProcessor(self.db_manager)
            
            # Step 1: Data Ingestion
            self.progress_update.emit("Processing CSV and fetching company data...")
            self.progress_value.emit(10)
            
            if self.is_cancelled:
                return
                
            company_ids = data_fetcher.process_csv_companies(self.csv_path)
            
            if not company_ids:
                self.error_occurred.emit("No companies were processed from CSV file.")
                return
            
            self.progress_update.emit(f"Processed {len(company_ids)} companies from CSV")
            self.progress_value.emit(30)
            
            # Step 2: SEC Filing Processing
            self.progress_update.emit("Processing SEC filings...")
            self.progress_value.emit(40)
            
            if self.is_cancelled:
                return
                
            for i, company_id in enumerate(company_ids):
                if self.is_cancelled:
                    return
                    
                # Get company symbol for logging
                with self.db_manager:
                    sql = "SELECT symbol FROM companies WHERE id = ?"
                    self.db_manager.cursor.execute(sql, (company_id,))
                    result = self.db_manager.cursor.fetchone()
                    symbol = result['symbol'] if result else f"ID_{company_id}"
                
                self.progress_update.emit(f"Processing SEC filings for {symbol}...")
                
                # Process SEC filings with error handling
                try:
                    filing_success = edgar_processor.process_company_filings(company_id, symbol)
                    if filing_success:
                        self.progress_update.emit(f"SEC filings processed successfully for {symbol}")
                    else:
                        self.progress_update.emit(f"No SEC filings found for {symbol}")
                except Exception as e:
                    self.progress_update.emit(f"SEC filing error for {symbol}: {str(e)}")
                    logger.error(f"SEC filing processing failed for {symbol}: {e}")
                
                # Update progress
                progress = 40 + (i + 1) * 30 // len(company_ids)
                self.progress_value.emit(progress)
            
            # Step 3: Quality Filtering
            self.progress_update.emit("Applying quality filters...")
            self.progress_value.emit(70)
            
            if self.is_cancelled:
                return
                
            filter_results = quality_filters.process_all_companies()
            
            self.progress_update.emit("Processing complete!")
            self.progress_value.emit(100)
            
            # Emit completion signal with results
            self.processing_complete.emit({
                'companies_processed': len(company_ids),
                'company_ids': company_ids,
                'filter_results': filter_results
            })
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self.error_occurred.emit(f"Processing failed: {str(e)}")
    
    def cancel(self):
        """Cancel the processing."""
        self.is_cancelled = True

class MainWindow(QMainWindow):
    """Main window for AlphaForge application."""
    
    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.processing_thread = None
        self.companies_data = []
        self.current_session_company_ids = []  # Track companies from current CSV session
        
        self.init_ui()
        self.init_database()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("AlphaForge - Investment Research Automation")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        self.create_header(main_layout)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar()
        
    def create_header(self, main_layout):
        """Create the header section with controls."""
        header_group = QGroupBox("CSV Processing & Analysis")
        header_layout = QHBoxLayout(header_group)
        
        # CSV Upload section
        csv_layout = QVBoxLayout()
        
        csv_label = QLabel("CSV File:")
        csv_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        csv_file_layout = QHBoxLayout()
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setPlaceholderText("Select CSV file containing company data...")
        self.csv_path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_csv_file)
        
        csv_file_layout.addWidget(self.csv_path_edit)
        csv_file_layout.addWidget(self.browse_button)
        
        csv_layout.addWidget(csv_label)
        csv_layout.addLayout(csv_file_layout)
        
        # Process button
        self.process_button = QPushButton("Process Companies")
        self.process_button.clicked.connect(self.process_companies)
        self.process_button.setEnabled(False)
        
        # Progress section
        progress_layout = QVBoxLayout()
        
        progress_label = QLabel("Processing Progress:")
        progress_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # Add to header layout
        header_layout.addLayout(csv_layout)
        header_layout.addWidget(self.process_button)
        header_layout.addLayout(progress_layout)
        header_layout.addStretch()
        
        main_layout.addWidget(header_group)
    
    def create_main_content(self, main_layout):
        """Create the main content area with results table and details."""
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left pane - Results table
        self.create_results_table(splitter)
        
        # Right pane - Company details
        self.create_details_pane(splitter)
        
        # Set splitter proportions
        splitter.setSizes([800, 600])
        
        main_layout.addWidget(splitter)
    
    def create_results_table(self, parent):
        """Create the results table widget."""
        # Create table group
        table_group = QGroupBox("Company Analysis Results")
        table_layout = QVBoxLayout(table_group)
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Filter controls
        filter_label = QLabel("Filter:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Companies", "Qualified Only", "Disqualified Only", "High Score (>60)", "Low Score (<30)"])
        self.filter_combo.currentTextChanged.connect(self.filter_companies)
        
        # Search box
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter symbol or company name...")
        self.search_edit.textChanged.connect(self.search_companies)
        
        # Export button
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        
        toolbar_layout.addWidget(filter_label)
        toolbar_layout.addWidget(self.filter_combo)
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.export_button)
        
        # Create table
        self.results_table = QTableWidget()
        self.setup_results_table()
        
        table_layout.addLayout(toolbar_layout)
        table_layout.addWidget(self.results_table)
        
        parent.addWidget(table_group)
    
    def setup_results_table(self):
        """Set up the results table columns and properties."""
        columns = [
            "Symbol", "Company Name", "Score", "SEC Filings", "Price", "Market Cap", 
            "P/E Ratio", "Free Cash Flow", "Debt/Equity", "52W % Change", "Avg Volume",
            "Net Debt/EBITDA", "Exchange", "Red Flags", "Status"
        ]
        
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        # Set table properties
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
        
        # Connect selection change
        self.results_table.selectionModel().selectionChanged.connect(self.on_company_selected)
    
    def create_details_pane(self, parent):
        """Create the company details pane."""
        # Create details group
        details_group = QGroupBox("Company Details")
        details_layout = QVBoxLayout(details_group)
        
        # Create tab widget for different detail sections
        self.details_tabs = QTabWidget()
        
        # Overview tab
        self.create_overview_tab()
        
        # Financial Data tab
        self.create_financial_tab()
        
        # SEC Filings tab
        self.create_filings_tab()
        
        # News & Analysis tab
        self.create_news_tab()
        
        # Notes tab
        self.create_notes_tab()
        
        details_layout.addWidget(self.details_tabs)
        
        parent.addWidget(details_group)
    
    def create_overview_tab(self):
        """Create the overview tab."""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Company info
        self.company_info_label = QLabel("Select a company to view details")
        self.company_info_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.company_info_label.setWordWrap(True)
        
        # Quality score display
        score_frame = QFrame()
        score_frame.setFrameStyle(QFrame.Box)
        score_layout = QVBoxLayout(score_frame)
        
        self.quality_score_label = QLabel("Quality Score: --")
        self.quality_score_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.quality_score_label.setAlignment(Qt.AlignCenter)
        
        score_layout.addWidget(self.quality_score_label)
        
        # Red flags display
        red_flags_label = QLabel("Red Flags:")
        red_flags_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.red_flags_list = QTextEdit()
        self.red_flags_list.setMaximumHeight(150)
        self.red_flags_list.setReadOnly(True)
        
        overview_layout.addWidget(self.company_info_label)
        overview_layout.addWidget(score_frame)
        overview_layout.addWidget(red_flags_label)
        overview_layout.addWidget(self.red_flags_list)
        overview_layout.addStretch()
        
        self.details_tabs.addTab(overview_widget, "Overview")
    
    def create_financial_tab(self):
        """Create the financial data tab."""
        financial_widget = QWidget()
        financial_layout = QVBoxLayout(financial_widget)
        
        self.financial_data_text = QTextEdit()
        self.financial_data_text.setReadOnly(True)
        self.financial_data_text.setFont(QFont("Courier", 9))
        
        financial_layout.addWidget(self.financial_data_text)
        
        self.details_tabs.addTab(financial_widget, "Financial Data")
    
    def create_filings_tab(self):
        """Create the SEC filings tab."""
        filings_widget = QWidget()
        filings_layout = QVBoxLayout(filings_widget)
        
        self.filings_table = QTableWidget()
        self.filings_table.setColumnCount(4)
        self.filings_table.setHorizontalHeaderLabels(["Filing Type", "Filing Date", "Period End", "Download"])
        
        filings_layout.addWidget(self.filings_table)
        
        self.details_tabs.addTab(filings_widget, "SEC Filings")
    
    def create_news_tab(self):
        """Create the news & analysis tab."""
        news_widget = QWidget()
        news_layout = QVBoxLayout(news_widget)
        
        # AI Summaries section
        ai_summaries_label = QLabel("AI-Generated Summaries:")
        ai_summaries_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.ai_summaries_text = QTextEdit()
        self.ai_summaries_text.setReadOnly(True)
        self.ai_summaries_text.setMaximumHeight(200)
        
        # News section
        news_label = QLabel("Recent News:")
        news_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.news_text = QTextEdit()
        self.news_text.setReadOnly(True)
        
        news_layout.addWidget(ai_summaries_label)
        news_layout.addWidget(self.ai_summaries_text)
        news_layout.addWidget(news_label)
        news_layout.addWidget(self.news_text)
        
        self.details_tabs.addTab(news_widget, "News & Analysis")
    
    def create_notes_tab(self):
        """Create the notes tab."""
        notes_widget = QWidget()
        notes_layout = QVBoxLayout(notes_widget)
        
        notes_label = QLabel("Research Notes:")
        notes_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Enter your qualitative analysis and thesis points here...")
        
        # Save notes button
        save_notes_button = QPushButton("Save Notes")
        save_notes_button.clicked.connect(self.save_notes)
        
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_text)
        notes_layout.addWidget(save_notes_button)
        
        self.details_tabs.addTab(notes_widget, "Notes")
    
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets to status bar
        self.companies_count_label = QLabel("Companies: 0")
        self.qualified_count_label = QLabel("Qualified: 0")
        self.disqualified_count_label = QLabel("Disqualified: 0")
        
        self.status_bar.addPermanentWidget(self.companies_count_label)
        self.status_bar.addPermanentWidget(self.qualified_count_label)
        self.status_bar.addPermanentWidget(self.disqualified_count_label)
    
    def init_database(self):
        """Initialize the database connection."""
        try:
            self.db_manager = initialize_database()
            self.status_bar.showMessage("Database initialized successfully")
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database: {str(e)}")
    
    def setup_connections(self):
        """Set up signal connections."""
        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def browse_csv_file(self):
        """Browse and select CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.csv_path_edit.setText(file_path)
            self.process_button.setEnabled(True)
            
            # Clear current session when new CSV is selected
            self.current_session_company_ids = []
            self.companies_data = []
            self.update_display()
    
    def process_companies(self):
        """Start processing companies from CSV."""
        csv_path = self.csv_path_edit.text()
        
        if not csv_path or not os.path.exists(csv_path):
            QMessageBox.warning(self, "File Error", "Please select a valid CSV file.")
            return
        
        # Disable controls during processing
        self.process_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        
        # Start processing thread
        self.processing_thread = ProcessingThread(csv_path, self.db_manager)
        self.processing_thread.progress_update.connect(self.update_progress_text)
        self.processing_thread.progress_value.connect(self.update_progress_value)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.error_occurred.connect(self.on_processing_error)
        
        self.processing_thread.start()
    
    def update_progress_text(self, text):
        """Update progress text."""
        self.progress_label.setText(text)
        self.status_bar.showMessage(text)
    
    def update_progress_value(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
    
    def on_processing_complete(self, results):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Re-enable controls
        self.process_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Show completion message
        companies_count = results.get('companies_processed', 0)
        self.current_session_company_ids = results.get('company_ids', []) # Store company IDs
        QMessageBox.information(
            self, "Processing Complete", 
            f"Successfully processed {companies_count} companies.\n\n"
            f"Results are now available in the table below."
        )
        
        # Refresh display
        self.load_companies_data()
        self.update_display()
        
        self.status_bar.showMessage("Processing completed successfully")
    
    def on_processing_error(self, error_message):
        """Handle processing error."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Re-enable controls
        self.process_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Processing Error", f"Processing failed:\n\n{error_message}")
        
        self.status_bar.showMessage("Processing failed")
    
    def load_companies_data(self):
        """Load companies data from database (only from current session)."""
        try:
            with self.db_manager:
                if self.current_session_company_ids:
                    # Only load companies from current CSV session
                    self.companies_data = self.db_manager.get_companies_by_ids(self.current_session_company_ids)
                    logger.info(f"Loaded {len(self.companies_data)} companies from current session")
                else:
                    # No current session, load all companies
                    self.companies_data = self.db_manager.get_all_companies()
                    logger.info(f"Loaded {len(self.companies_data)} companies from database")
        except Exception as e:
            logger.error(f"Failed to load companies data: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load data: {str(e)}")
    
    def update_display(self):
        """Update the display with current data."""
        try:
            if not self.companies_data:
                return
            
            # Update results table
            self.populate_results_table()
            
            # Update status bar counts
            total_companies = len(self.companies_data)
            qualified_count = sum(1 for company in self.companies_data if not company.get('disqualified_flag', False))
            disqualified_count = total_companies - qualified_count
            
            self.companies_count_label.setText(f"Companies: {total_companies}")
            self.qualified_count_label.setText(f"Qualified: {qualified_count}")
            self.disqualified_count_label.setText(f"Disqualified: {disqualified_count}")
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
            self.status_bar.showMessage(f"Display update error: {str(e)}")
    
    def get_sec_filings_status(self, company_id):
        """Check if company has SEC filings."""
        try:
            with self.db_manager:
                sql = "SELECT COUNT(*) as count FROM sec_filings WHERE company_id = ?"
                self.db_manager.cursor.execute(sql, (company_id,))
                result = self.db_manager.cursor.fetchone()
                return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error checking SEC filings: {e}")
            return 0

    def populate_results_table(self):
        """Populate the results table with company data."""
        filtered_data = self.get_filtered_companies()
        
        # Sort by highest score first
        filtered_data.sort(key=lambda x: x.get('weschler_quality_score', 0), reverse=True)
        
        self.results_table.setRowCount(len(filtered_data))
        
        for row, company in enumerate(filtered_data):
            # Check SEC filings status
            company_id = company.get('id')
            sec_filings_count = self.get_sec_filings_status(company_id) if company_id else 0
            sec_filings_status = "Yes" if sec_filings_count > 0 else "No"
            
            # Format and display data
            items = [
                company.get('symbol', ''),
                company.get('name', ''),
                str(company.get('weschler_quality_score', 0)),
                sec_filings_status,
                self.format_currency(company.get('price')),
                self.format_large_number(company.get('market_cap')),
                self.format_ratio(company.get('pe_ratio')),
                self.format_large_number(company.get('free_cash_flow')),
                self.format_percentage(company.get('debt_equity_ratio')),
                self.format_percentage(company.get('price_52w_change')),
                self.format_number(company.get('avg_daily_volume')),
                self.format_ratio(company.get('net_debt_ebitda')),
                company.get('exchange', ''),
                str(len(company.get('red_flags_list', []))),
                "Disqualified" if company.get('disqualified_flag', False) else "Qualified"
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                
                # Color coding based on status
                if col == 14:  # Status column
                    if item == "Disqualified":
                        table_item.setBackground(QColor(255, 200, 200))
                    else:
                        table_item.setBackground(QColor(200, 255, 200))
                
                # Color coding for quality score
                elif col == 2:  # Score column
                    score = company.get('weschler_quality_score', 0)
                    if score >= 60:
                        table_item.setBackground(QColor(144, 238, 144))  # Light green
                    elif score >= 30:
                        table_item.setBackground(QColor(255, 255, 144))  # Light yellow
                    else:
                        table_item.setBackground(QColor(255, 182, 193))  # Light pink
                
                # Color coding for SEC Filings
                elif col == 3: # SEC Filings column
                    if item == "Yes":
                        table_item.setBackground(QColor(200, 255, 200))  # Light green
                    else:
                        table_item.setBackground(QColor(255, 200, 200))  # Light red
                
                self.results_table.setItem(row, col, table_item)
    
    def get_filtered_companies(self):
        """Get filtered companies based on current filter settings."""
        filtered_data = self.companies_data.copy()
        
        # Apply combo box filter
        filter_type = self.filter_combo.currentText()
        if filter_type == "Qualified Only":
            filtered_data = [c for c in filtered_data if not c.get('disqualified_flag', False)]
        elif filter_type == "Disqualified Only":
            filtered_data = [c for c in filtered_data if c.get('disqualified_flag', False)]
        elif filter_type == "High Score (>60)":
            filtered_data = [c for c in filtered_data if c.get('weschler_quality_score', 0) > 60]
        elif filter_type == "Low Score (<30)":
            filtered_data = [c for c in filtered_data if c.get('weschler_quality_score', 0) < 30]
        
        # Apply search filter
        search_text = self.search_edit.text().lower()
        if search_text:
            filtered_data = [
                c for c in filtered_data 
                if search_text in c.get('symbol', '').lower() or 
                   search_text in c.get('name', '').lower()
            ]
        
        return filtered_data
    
    def filter_companies(self):
        """Handle filter combo box change."""
        self.update_display()
    
    def search_companies(self):
        """Handle search text change."""
        self.update_display()
    
    def on_company_selected(self):
        """Handle company selection in results table."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        
        # Get the symbol from the selected row directly to avoid filtering issues
        symbol_item = self.results_table.item(row, 0)  # First column is Symbol
        if not symbol_item:
            return
            
        symbol = symbol_item.text()
        
        # Find the company data by symbol
        company = None
        for comp in self.companies_data:
            if comp.get('symbol') == symbol:
                company = comp
                break
        
        if company:
            self.display_company_details(company)
        else:
            logger.warning(f"Company not found for symbol: {symbol}")
    
    def display_company_details(self, company):
        """Display detailed company information."""
        # Overview tab
        info_text = f"""
        <h2>{company.get('name', 'N/A')} ({company.get('symbol', 'N/A')})</h2>
        <p><b>Exchange:</b> {company.get('exchange', 'N/A')}</p>
        <p><b>Sector:</b> {company.get('sector', 'N/A')}</p>
        <p><b>Industry:</b> {company.get('industry', 'N/A')}</p>
        <p><b>Market Cap:</b> {self.format_large_number(company.get('market_cap'))}</p>
        <p><b>Current Price:</b> {self.format_currency(company.get('price'))}</p>
        """
        
        self.company_info_label.setText(info_text)
        
        # Quality score
        score = company.get('weschler_quality_score', 0)
        score_text = f"Quality Score: {score}"
        if score >= 60:
            score_color = "green"
        elif score >= 30:
            score_color = "orange"
        else:
            score_color = "red"
        
        self.quality_score_label.setText(score_text)
        self.quality_score_label.setStyleSheet(f"color: {score_color};")
        
        # Red flags
        red_flags = company.get('red_flags_list', [])
        if red_flags:
            flags_text = "\n".join([f"• {flag}" for flag in red_flags])
        else:
            flags_text = "No red flags identified."
        
        self.red_flags_list.setText(flags_text)
        
        # Financial data tab
        financial_text = self.format_financial_data(company)
        self.financial_data_text.setText(financial_text)
        
        # Load additional data (SEC filings, news, etc.)
        self.load_additional_company_data(company)
    
    def format_financial_data(self, company):
        """Format financial data for display."""
        data = f"""
FINANCIAL SUMMARY
================

Basic Metrics:
• Market Cap: {self.format_large_number(company.get('market_cap'))}
• Current Price: {self.format_currency(company.get('price'))}
• P/E Ratio: {self.format_ratio(company.get('pe_ratio'))}
• 52-Week Change: {self.format_percentage(company.get('price_52w_change'))}

Financial Health:
• Free Cash Flow: {self.format_large_number(company.get('free_cash_flow'))}
• Total Debt: {self.format_large_number(company.get('total_debt'))}
• Shareholder Equity: {self.format_large_number(company.get('shareholder_equity'))}
• Net Debt/EBITDA: {self.format_ratio(company.get('net_debt_ebitda'))}

Trading Information:
• Average Daily Volume: {self.format_number(company.get('avg_daily_volume'))}
• Exchange: {company.get('exchange', 'N/A')}
        """
        
        return data.strip()
    
    def load_additional_company_data(self, company):
        """Load additional company data (SEC filings, news, etc.)."""
        # This would load SEC filings, news, and AI summaries
        # For now, we'll show placeholder text
        
        # SEC Filings
        self.filings_table.setRowCount(0)
        # TODO: Load actual SEC filings from database
        
        # AI Summaries
        ai_text = "AI-generated risk and management summaries will appear here after processing."
        self.ai_summaries_text.setText(ai_text)
        
        # News
        news_text = "Recent news articles and red flag analysis will appear here."
        self.news_text.setText(news_text)
        
        # Notes
        notes = company.get('user_notes', '')
        self.notes_text.setText(notes)
    
    def save_notes(self):
        """Save user notes for the selected company."""
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a company first.")
            return
        
        row = selected_rows[0].row()
        filtered_data = self.get_filtered_companies()
        
        if row < len(filtered_data):
            company = filtered_data[row]
            notes = self.notes_text.toPlainText()
            
            try:
                with self.db_manager:
                    sql = "UPDATE companies SET user_notes = ? WHERE id = ?"
                    self.db_manager.cursor.execute(sql, (notes, company['id']))
                    self.db_manager.connection.commit()
                
                QMessageBox.information(self, "Notes Saved", "Notes have been saved successfully.")
                
            except Exception as e:
                logger.error(f"Failed to save notes: {e}")
                QMessageBox.critical(self, "Save Error", f"Failed to save notes: {str(e)}")
    
    def export_to_excel(self):
        """Export results to Excel file."""
        if not self.companies_data:
            QMessageBox.warning(self, "No Data", "No data available to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", f"alphaforge_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            try:
                # This would implement the Excel export functionality
                # For now, show a placeholder message
                QMessageBox.information(self, "Export", f"Export to {file_path} would be implemented here.")
                
            except Exception as e:
                logger.error(f"Failed to export to Excel: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    # Utility methods for formatting
    def format_currency(self, value):
        """Format currency values."""
        if value is None:
            return "N/A"
        try:
            return f"${float(value):.2f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def format_large_number(self, value):
        """Format large numbers with suffixes."""
        if value is None:
            return "N/A"
        try:
            value = float(value)
            if abs(value) >= 1e9:
                return f"${value/1e9:.2f}B"
            elif abs(value) >= 1e6:
                return f"${value/1e6:.2f}M"
            elif abs(value) >= 1e3:
                return f"${value/1e3:.2f}K"
            else:
                return f"${value:.2f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def format_percentage(self, value):
        """Format percentage values."""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2f}%"
        except (ValueError, TypeError):
            return "N/A"
    
    def format_ratio(self, value):
        """Format ratio values."""
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def format_number(self, value):
        """Format number values."""
        if value is None:
            return "N/A"
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return "N/A"
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "Processing in Progress",
                "Processing is currently running. Do you want to cancel and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.processing_thread.cancel()
                self.processing_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 