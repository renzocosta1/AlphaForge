"""
Database schema definition and management for AlphaForge.
Defines all tables and provides database initialization functions.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for AlphaForge."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or config.DATABASE_PATH
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.connection.cursor()
            logger.info(f"Database connection established: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def _ensure_connected(self):
        """Ensure database connection is established."""
        if self.connection is None or self.cursor is None:
            raise sqlite3.Error("Database not connected. Use connect() first.")
    
    def create_tables(self):
        """Create all database tables."""
        self._ensure_connected()
        assert self.cursor is not None and self.connection is not None
        
        tables = {
            'companies': self._get_companies_table_sql(),
            'financial_statements': self._get_financial_statements_table_sql(),
            'sec_filings': self._get_sec_filings_table_sql(),
            'news': self._get_news_table_sql(),
            'insider_activity': self._get_insider_activity_table_sql(),
            'ai_summaries': self._get_ai_summaries_table_sql(),
            'processing_log': self._get_processing_log_table_sql()
        }
        
        for table_name, sql in tables.items():
            try:
                self.cursor.execute(sql)
                logger.info(f"Created table: {table_name}")
            except sqlite3.Error as e:
                logger.error(f"Failed to create table {table_name}: {e}")
                raise
        
        self.connection.commit()
        logger.info("All database tables created successfully")
    
    def _get_companies_table_sql(self) -> str:
        """Get SQL for companies table."""
        return """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            exchange TEXT,
            sector TEXT,
            industry TEXT,
            market_cap REAL,
            price REAL,
            pe_ratio REAL,
            debt_equity_ratio REAL,
            free_cash_flow REAL,
            price_52w_change REAL,
            avg_daily_volume INTEGER,
            net_debt_ebitda REAL,
            total_debt REAL,
            shareholder_equity REAL,
            disqualified_flag INTEGER DEFAULT 0,
            red_flags_list TEXT,  -- JSON array of red flags
            weschler_quality_score INTEGER DEFAULT 0,
            user_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    
    def _get_financial_statements_table_sql(self) -> str:
        """Get SQL for financial statements table."""
        return """
        CREATE TABLE IF NOT EXISTS financial_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            statement_type TEXT NOT NULL,  -- 'income', 'balance_sheet', 'cash_flow'
            fiscal_year INTEGER NOT NULL,
            fiscal_quarter INTEGER,  -- NULL for annual statements
            statement_data TEXT NOT NULL,  -- JSON data of the statement
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            UNIQUE(company_id, statement_type, fiscal_year, fiscal_quarter)
        );
        """
    
    def _get_sec_filings_table_sql(self) -> str:
        """Get SQL for SEC filings table."""
        return """
        CREATE TABLE IF NOT EXISTS sec_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            filing_type TEXT NOT NULL,  -- '10-K', '10-Q', '8-K', 'DEF 14A'
            filing_date DATE NOT NULL,
            period_end_date DATE,
            accession_number TEXT NOT NULL,
            html_url TEXT NOT NULL,
            text_url TEXT,
            local_path TEXT,  -- Path to downloaded filing
            file_size INTEGER,
            download_status TEXT DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            UNIQUE(company_id, accession_number)
        );
        """
    
    def _get_news_table_sql(self) -> str:
        """Get SQL for news table."""
        return """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            headline TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            source TEXT,
            published_date TIMESTAMP,
            sentiment TEXT,  -- 'positive', 'negative', 'neutral'
            red_flag_keywords TEXT,  -- JSON array of flagged keywords
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        """
    
    def _get_insider_activity_table_sql(self) -> str:
        """Get SQL for insider activity table."""
        return """
        CREATE TABLE IF NOT EXISTS insider_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            insider_name TEXT NOT NULL,
            position TEXT,
            transaction_type TEXT,  -- 'buy', 'sell', 'option_exercise', etc.
            shares INTEGER,
            price REAL,
            value REAL,
            transaction_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        """
    
    def _get_ai_summaries_table_sql(self) -> str:
        """Get SQL for AI summaries table."""
        return """
        CREATE TABLE IF NOT EXISTS ai_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            summary_type TEXT NOT NULL,  -- 'risk_summary', 'management_summary'
            summary_text TEXT NOT NULL,
            source_filing_id INTEGER,
            model_used TEXT,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (source_filing_id) REFERENCES sec_filings (id)
        );
        """
    
    def _get_processing_log_table_sql(self) -> str:
        """Get SQL for processing log table."""
        return """
        CREATE TABLE IF NOT EXISTS processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            process_type TEXT NOT NULL,  -- 'data_ingestion', 'filtering', 'ai_analysis', etc.
            status TEXT NOT NULL,  -- 'started', 'completed', 'failed'
            message TEXT,
            error_details TEXT,
            processing_time REAL,  -- seconds
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        """
    
    def insert_company(self, company_data: Dict[str, Any]) -> int:
        """
        Insert a new company record or update existing one.
        
        Args:
            company_data: Dictionary containing company information
            
        Returns:
            ID of the inserted/updated company
        """
        sql = """
        INSERT OR REPLACE INTO companies (
            symbol, name, exchange, sector, industry, market_cap, price, 
            pe_ratio, debt_equity_ratio, free_cash_flow, price_52w_change,
            avg_daily_volume, net_debt_ebitda, total_debt, shareholder_equity,
            red_flags_list
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        red_flags_json = json.dumps(company_data.get('red_flags_list', []))
        
        values = (
            company_data.get('symbol'),
            company_data.get('name'),
            company_data.get('exchange'),
            company_data.get('sector'),
            company_data.get('industry'),
            company_data.get('market_cap'),
            company_data.get('price'),
            company_data.get('pe_ratio'),
            company_data.get('debt_equity_ratio'),
            company_data.get('free_cash_flow'),
            company_data.get('price_52w_change'),
            company_data.get('avg_daily_volume'),
            company_data.get('net_debt_ebitda'),
            company_data.get('total_debt'),
            company_data.get('shareholder_equity'),
            red_flags_json
        )
        
        self.cursor.execute(sql, values)
        self.connection.commit()
        
        # Get the company ID (either newly inserted or existing)
        symbol = company_data.get('symbol')
        get_id_sql = "SELECT id FROM companies WHERE symbol = ?"
        self.cursor.execute(get_id_sql, (symbol,))
        result = self.cursor.fetchone()
        return result[0] if result else self.cursor.lastrowid
    
    def get_company_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company by symbol.
        
        Args:
            symbol: Company symbol
            
        Returns:
            Company data dictionary or None if not found
        """
        sql = "SELECT * FROM companies WHERE symbol = ?"
        self.cursor.execute(sql, (symbol,))
        row = self.cursor.fetchone()
        
        if row:
            company_data = dict(row)
            # Parse JSON fields
            company_data['red_flags_list'] = json.loads(company_data.get('red_flags_list', '[]'))
            return company_data
        return None
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get all companies.
        
        Returns:
            List of company data dictionaries
        """
        sql = "SELECT * FROM companies ORDER BY weschler_quality_score DESC"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        
        companies = []
        for row in rows:
            company_data = dict(row)
            # Parse JSON fields
            company_data['red_flags_list'] = json.loads(company_data.get('red_flags_list', '[]'))
            companies.append(company_data)
        
        return companies
    
    def get_companies_by_ids(self, company_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get companies by their IDs.
        
        Args:
            company_ids: List of company IDs
            
        Returns:
            List of company data dictionaries
        """
        if not company_ids:
            return []
        
        # Create placeholders for the IN clause
        placeholders = ','.join(['?' for _ in company_ids])
        sql = f"SELECT * FROM companies WHERE id IN ({placeholders}) ORDER BY weschler_quality_score DESC"
        self.cursor.execute(sql, company_ids)
        rows = self.cursor.fetchall()
        
        companies = []
        for row in rows:
            company_data = dict(row)
            # Parse JSON fields
            company_data['red_flags_list'] = json.loads(company_data.get('red_flags_list', '[]'))
            companies.append(company_data)
        
        return companies
    
    def update_company_flags(self, company_id: int, red_flags: List[str], 
                           disqualified: bool = False):
        """
        Update company red flags and disqualification status.
        
        Args:
            company_id: Company ID
            red_flags: List of red flag strings
            disqualified: Whether company is disqualified
        """
        sql = """
        UPDATE companies 
        SET red_flags_list = ?, disqualified_flag = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        
        red_flags_json = json.dumps(red_flags)
        self.cursor.execute(sql, (red_flags_json, int(disqualified), company_id))
        self.connection.commit()
    
    def update_company_score(self, company_id: int, score: int):
        """
        Update company Weschler Quality Score.
        
        Args:
            company_id: Company ID
            score: Quality score
        """
        sql = """
        UPDATE companies 
        SET weschler_quality_score = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        self.cursor.execute(sql, (score, company_id))
        self.connection.commit()
    
    def log_processing_event(self, company_id: Optional[int], process_type: str, 
                           status: str, message: str = None, error_details: str = None,
                           processing_time: float = None):
        """
        Log a processing event.
        
        Args:
            company_id: Company ID (optional)
            process_type: Type of process
            status: Process status
            message: Optional message
            error_details: Optional error details
            processing_time: Processing time in seconds
        """
        sql = """
        INSERT INTO processing_log (
            company_id, process_type, status, message, error_details, processing_time
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        self.cursor.execute(sql, (
            company_id, process_type, status, message, error_details, processing_time
        ))
        self.connection.commit()

def initialize_database(db_path: str = None) -> DatabaseManager:
    """
    Initialize the database with all tables.
    
    Args:
        db_path: Path to database file
        
    Returns:
        DatabaseManager instance
    """
    db_manager = DatabaseManager(db_path)
    
    with db_manager:
        db_manager.create_tables()
        logger.info("Database initialized successfully")
    
    return db_manager 