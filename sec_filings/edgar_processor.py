"""
SEC EDGAR filing processor for AlphaForge.
Handles retrieval, downloading, and processing of SEC filings.
"""

import os
import re
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path
import time
import csv

from config import config
from database.schema import DatabaseManager
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class EdgarProcessor:
    """Processes SEC EDGAR filings for companies."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize EDGAR processor.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.rate_limiter = RateLimiter()
        self.base_url = "https://www.sec.gov"
        self.api_base = "https://data.sec.gov"
        self.user_agent = config.SEC_EDGAR_USER_AGENT
        self.session = self._create_session()
        
        # Ensure filings directory exists
        self.filings_dir = Path(config.FILINGS_DIR)
        self.filings_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_session(self) -> requests.Session:
        """Create requests session with proper headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/html, application/xhtml+xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def get_company_cik(self, symbol: str) -> Optional[str]:
        """
        Get company CIK from ticker symbol using local CSV mapping.
        
        Args:
            symbol: Company ticker symbol
            
        Returns:
            CIK string or None if not found
        """
        try:
            logger.info(f"Looking up CIK for symbol: {symbol}")
            
            # Path to the local CIK mapping file
            mapping_file = Path("sec_cik_mapping.csv")
            
            if not mapping_file.exists():
                logger.error(f"CIK mapping file not found: {mapping_file}")
                return None
            
            # Read the CSV file and search for the symbol
            with open(mapping_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if row.get('symbol', '').upper() == symbol.upper():
                        cik = row.get('cik', '')
                        # Ensure CIK is properly formatted (10 digits with leading zeros)
                        padded_cik = cik.zfill(10)
                        logger.info(f"Found CIK for {symbol}: {padded_cik}")
                        return padded_cik
            
            logger.warning(f"CIK not found for symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get CIK for {symbol}: {e}")
            return None
    
    def get_company_filings(self, cik: str, symbol: str, 
                          filing_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get recent filings for a company.
        
        Args:
            cik: Company CIK
            symbol: Company symbol
            filing_types: List of filing types to retrieve
            
        Returns:
            List of filing information dictionaries
        """
        if filing_types is None:
            filing_types = ['10-K', '10-Q', '8-K', 'DEF 14A']
        
        logger.info(f"Fetching filings for {symbol} (CIK: {cik})")
        
        try:
            self.rate_limiter.wait_if_needed('sec_edgar')
            
            # Get company submissions
            url = f"{self.api_base}/submissions/CIK{cik}.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            submissions_data = response.json()
            
            # Extract recent filings
            filings = []
            recent_filings = submissions_data.get('filings', {}).get('recent', {})
            
            if not recent_filings:
                logger.warning(f"No recent filings found for {symbol}")
                return filings
            
            # Process each filing
            for i in range(len(recent_filings.get('form', []))):
                form_type = recent_filings['form'][i]
                
                # Filter by requested filing types
                if form_type not in filing_types:
                    continue
                
                filing_date = recent_filings['filingDate'][i]
                accession_number = recent_filings['accessionNumber'][i]
                
                # Skip if filing is too old (more than 5 years)
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
                if filing_date_obj < datetime.now() - timedelta(days=5*365):
                    continue
                
                # Construct URLs
                accession_no_dashes = accession_number.replace('-', '')
                html_url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_no_dashes}/{accession_number}.txt"
                
                filing_info = {
                    'filing_type': form_type,
                    'filing_date': filing_date,
                    'accession_number': accession_number,
                    'html_url': html_url,
                    'period_end_date': recent_filings.get('reportDate', [None])[i],
                    'file_size': recent_filings.get('size', [0])[i],
                    'company_name': submissions_data.get('name', ''),
                    'cik': cik
                }
                
                filings.append(filing_info)
            
            logger.info(f"Found {len(filings)} relevant filings for {symbol}")
            return filings
            
        except Exception as e:
            logger.error(f"Failed to get filings for {symbol}: {e}")
            return []
    
    def download_filing(self, filing_info: Dict[str, Any], symbol: str) -> Optional[str]:
        """
        Download a specific filing.
        
        Args:
            filing_info: Filing information dictionary
            symbol: Company symbol
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            self.rate_limiter.wait_if_needed('sec_edgar')
            
            # Create company-specific directory
            company_dir = self.filings_dir / symbol
            company_dir.mkdir(exist_ok=True)
            
            # Generate filename
            filing_date = filing_info['filing_date']
            filing_type = filing_info['filing_type']
            accession_number = filing_info['accession_number']
            filename = f"{filing_type}_{filing_date}_{accession_number}.txt"
            file_path = company_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                logger.info(f"Filing already exists: {file_path}")
                return str(file_path)
            
            # Download the filing
            url = filing_info['html_url']
            logger.info(f"Downloading filing from: {url}")
            
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Successfully downloaded filing: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to download filing {filing_info.get('accession_number', 'unknown')}: {e}")
            return None
    
    def extract_filing_text(self, file_path: str, filing_type: str) -> Dict[str, str]:
        """
        Extract relevant text sections from a filing.
        
        Args:
            file_path: Path to the filing file
            filing_type: Type of filing (10-K, 10-Q, etc.)
            
        Returns:
            Dictionary with extracted text sections
        """
        extracted_text = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract based on filing type
            if filing_type == '10-K':
                extracted_text = self._extract_10k_sections(content)
            elif filing_type == '10-Q':
                extracted_text = self._extract_10q_sections(content)
            elif filing_type == 'DEF 14A':
                extracted_text = self._extract_def14a_sections(content)
            elif filing_type == '8-K':
                extracted_text = self._extract_8k_sections(content)
            
            logger.info(f"Extracted {len(extracted_text)} sections from {filing_type}")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return {}
    
    def _extract_10k_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections from 10-K filing."""
        sections = {}
        
        # Risk factors (Item 1A)
        risk_pattern = r'(?i)item\s+1a\.?\s*risk\s+factors(.*?)(?=item\s+1b\.?|item\s+2\.?|$)'
        risk_match = re.search(risk_pattern, content, re.DOTALL)
        if risk_match:
            sections['risk_factors'] = self._clean_text(risk_match.group(1))
        
        # Business overview (Item 1)
        business_pattern = r'(?i)item\s+1\.?\s*business(.*?)(?=item\s+1a\.?|item\s+2\.?|$)'
        business_match = re.search(business_pattern, content, re.DOTALL)
        if business_match:
            sections['business_overview'] = self._clean_text(business_match.group(1))
        
        # MD&A (Item 7)
        mda_pattern = r'(?i)item\s+7\.?\s*management.s\s+discussion\s+and\s+analysis(.*?)(?=item\s+7a\.?|item\s+8\.?|$)'
        mda_match = re.search(mda_pattern, content, re.DOTALL)
        if mda_match:
            sections['mda'] = self._clean_text(mda_match.group(1))
        
        # Financial statements (Item 8)
        financials_pattern = r'(?i)item\s+8\.?\s*financial\s+statements(.*?)(?=item\s+9\.?|$)'
        financials_match = re.search(financials_pattern, content, re.DOTALL)
        if financials_match:
            sections['financial_statements'] = self._clean_text(financials_match.group(1))
        
        return sections
    
    def _extract_10q_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections from 10-Q filing."""
        sections = {}
        
        # Financial statements (Part I, Item 1)
        financials_pattern = r'(?i)part\s+i.*?item\s+1\.?\s*financial\s+statements(.*?)(?=item\s+2\.?|part\s+ii|$)'
        financials_match = re.search(financials_pattern, content, re.DOTALL)
        if financials_match:
            sections['financial_statements'] = self._clean_text(financials_match.group(1))
        
        # MD&A (Part I, Item 2)
        mda_pattern = r'(?i)part\s+i.*?item\s+2\.?\s*management.s\s+discussion\s+and\s+analysis(.*?)(?=item\s+3\.?|part\s+ii|$)'
        mda_match = re.search(mda_pattern, content, re.DOTALL)
        if mda_match:
            sections['mda'] = self._clean_text(mda_match.group(1))
        
        return sections
    
    def _extract_def14a_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections from DEF 14A (Proxy Statement)."""
        sections = {}
        
        # Executive compensation
        comp_pattern = r'(?i)executive\s+compensation(.*?)(?=director\s+compensation|securities\s+ownership|$)'
        comp_match = re.search(comp_pattern, content, re.DOTALL)
        if comp_match:
            sections['executive_compensation'] = self._clean_text(comp_match.group(1))
        
        # Board of directors
        board_pattern = r'(?i)(?:board\s+of\s+directors|directors\s+and\s+executive\s+officers)(.*?)(?=executive\s+compensation|$)'
        board_match = re.search(board_pattern, content, re.DOTALL)
        if board_match:
            sections['board_of_directors'] = self._clean_text(board_match.group(1))
        
        # Security ownership
        ownership_pattern = r'(?i)security\s+ownership(.*?)(?=executive\s+compensation|$)'
        ownership_match = re.search(ownership_pattern, content, re.DOTALL)
        if ownership_match:
            sections['security_ownership'] = self._clean_text(ownership_match.group(1))
        
        return sections
    
    def _extract_8k_sections(self, content: str) -> Dict[str, str]:
        """Extract key sections from 8-K filing."""
        sections = {}
        
        # Current events (Item 1-9)
        items_pattern = r'(?i)item\s+(\d+\.?\d*)\s*(.*?)(?=item\s+\d+\.?\d*|signature|$)'
        items_matches = re.finditer(items_pattern, content, re.DOTALL)
        
        for match in items_matches:
            item_number = match.group(1)
            item_text = self._clean_text(match.group(2))
            sections[f'item_{item_number}'] = item_text
        
        return sections
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page breaks and form feeds
        text = re.sub(r'[\f\r]+', '\n', text)
        
        # Limit length to prevent extremely long texts
        if len(text) > 50000:  # Limit to ~50KB
            text = text[:50000] + "... [truncated]"
        
        return text.strip()
    
    def process_company_filings(self, company_id: int, symbol: str) -> bool:
        """
        Process all filings for a company.
        
        Args:
            company_id: Company ID in database
            symbol: Company symbol
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing SEC filings for {symbol}")
        
        try:
            # Get company CIK
            cik = self.get_company_cik(symbol)
            if not cik:
                logger.warning(f"Could not find CIK for {symbol} - this may not be a US-listed company")
                return False
            
            logger.info(f"Found CIK {cik} for {symbol}")
            
            # Get filings
            filings = self.get_company_filings(cik, symbol)
            if not filings:
                logger.warning(f"No filings found for {symbol} (CIK: {cik})")
                return False
            
            logger.info(f"Found {len(filings)} filings for {symbol}")
            
            # Process each filing
            processed_count = 0
            for filing_info in filings:
                try:
                    # Store filing information in database (without downloading the full text for now)
                    self._store_filing_info(company_id, filing_info, None)
                    
                    processed_count += 1
                    logger.info(f"Successfully processed {filing_info['filing_type']} for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Failed to process filing {filing_info.get('accession_number', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Completed processing {processed_count} filings for {symbol}")
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Failed to process filings for {symbol}: {e}")
            return False
    
    def _store_filing_info(self, company_id: int, filing_info: Dict[str, Any], 
                          local_path: Optional[str]):
        """Store filing information in database."""
        try:
            with self.db_manager:
                sql = """
                INSERT OR REPLACE INTO sec_filings (
                    company_id, filing_type, filing_date, period_end_date,
                    accession_number, html_url, local_path, file_size,
                    download_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db_manager.cursor.execute(sql, (
                    company_id,
                    filing_info['filing_type'],
                    filing_info['filing_date'],
                    filing_info.get('period_end_date'),
                    filing_info['accession_number'],
                    filing_info['html_url'],
                    local_path,
                    filing_info.get('file_size', 0),
                    'completed'
                ))
                
                self.db_manager.connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to store filing info: {e}")
    
    def check_recent_filings(self, company_id: int, symbol: str) -> Dict[str, bool]:
        """
        Check if company has recent required filings.
        
        Args:
            company_id: Company ID
            symbol: Company symbol
            
        Returns:
            Dictionary indicating presence of recent filings
        """
        logger.info(f"Checking recent filings for {symbol}")
        
        filing_status = {
            '10-K': False,
            '10-Q': False,
            '8-K': False,
            'DEF 14A': False
        }
        
        try:
            with self.db_manager:
                sql = """
                SELECT filing_type, MAX(filing_date) as latest_date
                FROM sec_filings
                WHERE company_id = ? AND download_status = 'completed'
                GROUP BY filing_type
                """
                
                self.db_manager.cursor.execute(sql, (company_id,))
                results = self.db_manager.cursor.fetchall()
                
                cutoff_date = datetime.now() - timedelta(days=18*30)  # 18 months ago
                
                for row in results:
                    filing_type = row['filing_type']
                    latest_date = datetime.strptime(row['latest_date'], '%Y-%m-%d')
                    
                    if filing_type in filing_status:
                        filing_status[filing_type] = latest_date >= cutoff_date
                
                logger.info(f"Filing status for {symbol}: {filing_status}")
                return filing_status
                
        except Exception as e:
            logger.error(f"Failed to check filings for {symbol}: {e}")
            return filing_status 