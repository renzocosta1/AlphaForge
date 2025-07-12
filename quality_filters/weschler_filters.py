"""
Weschler Quality Filters for AlphaForge.
Implements comprehensive quality screening based on Ted Weschler's investment criteria.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from config import config
from database.schema import DatabaseManager
from sec_filings.edgar_processor import EdgarProcessor

logger = logging.getLogger(__name__)

class WeschlerQualityFilters:
    """
    Implements Ted Weschler's quality filters for investment screening.
    
    This class applies systematic quantitative and qualitative filters
    to identify companies that meet high standards for further analysis.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize quality filters.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.edgar_processor = EdgarProcessor(db_manager)
        self.filter_config = config.get_filter_config()
        self.scoring_config = config.get_scoring_config()
        
        # Initialize filter thresholds
        self.max_debt_to_ebitda = self.filter_config['max_debt_to_ebitda']
        self.min_trading_volume = self.filter_config['min_trading_volume']
        self.fcf_negative_years_threshold = self.filter_config['fcf_negative_years_threshold']
        self.operating_income_negative_years_threshold = self.filter_config['operating_income_negative_years_threshold']
    
    def apply_all_filters(self, company_id: int) -> Dict[str, Any]:
        """
        Apply all quality filters to a company.
        
        Args:
            company_id: Company ID in database
            
        Returns:
            Dictionary with filter results, red flags, and quality score
        """
        logger.info(f"Applying quality filters to company ID {company_id}")
        
        # Get company data
        company_data = self._get_company_data(company_id)
        if not company_data:
            logger.error(f"Could not retrieve company data for ID {company_id}")
            return {}
        
        symbol = company_data['symbol']
        logger.info(f"Processing quality filters for {symbol}")
        
        # Initialize results
        filter_results = {
            'company_id': company_id,
            'symbol': symbol,
            'red_flags': [],
            'disqualified': False,
            'quality_score': 0,
            'filter_details': {}
        }
        
        # Apply each filter
        self._apply_sec_filing_filter(company_data, filter_results)
        self._apply_fcf_consistency_filter(company_data, filter_results)
        self._apply_operating_income_filter(company_data, filter_results)
        self._apply_debt_analysis_filter(company_data, filter_results)
        self._apply_balance_sheet_filter(company_data, filter_results)
        self._apply_liquidity_filter(company_data, filter_results)
        self._apply_exchange_filter(company_data, filter_results)
        self._apply_news_red_flag_filter(company_data, filter_results)
        self._apply_corporate_action_filter(company_data, filter_results)
        
        # Calculate quality score
        filter_results['quality_score'] = self._calculate_quality_score(filter_results)
        
        # Update database
        self._update_company_filtering_results(company_id, filter_results)
        
        logger.info(f"Quality filtering completed for {symbol}. Score: {filter_results['quality_score']}")
        return filter_results
    
    def _get_company_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive company data from database."""
        try:
            with self.db_manager:
                sql = """
                SELECT * FROM companies WHERE id = ?
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                row = self.db_manager.cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get company data: {e}")
            return None
    
    def _apply_sec_filing_filter(self, company_data: Dict[str, Any], 
                               filter_results: Dict[str, Any]):
        """
        Apply SEC filing standard filter (primary disqualification).
        
        Checks for recent 10-K, 10-Q, and 8-K filings within 12-18 months.
        This is the primary disqualification filter.
        """
        logger.info(f"Applying SEC filing filter for {company_data['symbol']}")
        
        company_id = company_data['id']
        filing_status = self.edgar_processor.check_recent_filings(company_id, company_data['symbol'])
        
        # Check if company has recent required filings
        required_filings = ['10-K', '10-Q', '8-K']
        missing_filings = []
        
        for filing_type in required_filings:
            if not filing_status.get(filing_type, False):
                missing_filings.append(filing_type)
        
        if missing_filings:
            red_flag = f"No Recent SEC Filings: {', '.join(missing_filings)}"
            filter_results['red_flags'].append(red_flag)
            filter_results['disqualified'] = True
            logger.warning(f"Company {company_data['symbol']} disqualified due to missing SEC filings")
        
        filter_results['filter_details']['sec_filing_status'] = filing_status
        filter_results['filter_details']['missing_filings'] = missing_filings
    
    def _apply_fcf_consistency_filter(self, company_data: Dict[str, Any],
                                    filter_results: Dict[str, Any]):
        """
        Apply free cash flow consistency filter.
        
        Flags companies with negative FCF for 4+ out of 5 years.
        """
        logger.info(f"Applying FCF consistency filter for {company_data['symbol']}")
        
        try:
            # Get historical FCF data
            fcf_data = self._get_historical_fcf_data(company_data['id'])
            
            if not fcf_data:
                logger.warning(f"No FCF data available for {company_data['symbol']}")
                return
            
            # Analyze FCF trend
            negative_years = 0
            total_years = len(fcf_data)
            
            for year_data in fcf_data:
                if year_data['fcf'] < 0:
                    negative_years += 1
            
            # Check if FCF is negative for threshold years
            if negative_years >= self.fcf_negative_years_threshold and total_years >= 5:
                red_flag = f"Persistent Negative FCF: {negative_years}/{total_years} years"
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"FCF red flag for {company_data['symbol']}: {red_flag}")
            
            # Check for accelerating negative trend
            if len(fcf_data) >= 3:
                recent_fcf = [year['fcf'] for year in fcf_data[-3:]]
                if all(fcf < 0 for fcf in recent_fcf) and recent_fcf[-1] < recent_fcf[0]:
                    red_flag = "Accelerating Negative FCF Trend"
                    filter_results['red_flags'].append(red_flag)
                    logger.warning(f"FCF trend red flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['fcf_analysis'] = {
                'negative_years': negative_years,
                'total_years': total_years,
                'recent_fcf': fcf_data[-5:] if len(fcf_data) >= 5 else fcf_data
            }
            
        except Exception as e:
            logger.error(f"Failed to apply FCF filter for {company_data['symbol']}: {e}")
    
    def _apply_operating_income_filter(self, company_data: Dict[str, Any],
                                     filter_results: Dict[str, Any]):
        """
        Apply operating income consistency filter.
        
        Flags companies with negative EBIT/EBITDA for 4+ out of 5 years.
        """
        logger.info(f"Applying operating income filter for {company_data['symbol']}")
        
        try:
            # Get historical operating income data
            operating_data = self._get_historical_operating_income_data(company_data['id'])
            
            if not operating_data:
                logger.warning(f"No operating income data available for {company_data['symbol']}")
                return
            
            # Analyze operating income trend
            negative_years = 0
            total_years = len(operating_data)
            
            for year_data in operating_data:
                if year_data['operating_income'] < 0:
                    negative_years += 1
            
            # Check if operating income is negative for threshold years
            if negative_years >= self.operating_income_negative_years_threshold and total_years >= 5:
                red_flag = f"Persistent Operating Losses: {negative_years}/{total_years} years"
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"Operating income red flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['operating_income_analysis'] = {
                'negative_years': negative_years,
                'total_years': total_years,
                'recent_data': operating_data[-5:] if len(operating_data) >= 5 else operating_data
            }
            
        except Exception as e:
            logger.error(f"Failed to apply operating income filter for {company_data['symbol']}: {e}")
    
    def _apply_debt_analysis_filter(self, company_data: Dict[str, Any],
                                  filter_results: Dict[str, Any]):
        """
        Apply debt analysis filter.
        
        Flags companies with high debt burden or rapidly growing debt.
        """
        logger.info(f"Applying debt analysis filter for {company_data['symbol']}")
        
        try:
            # Check Net Debt/EBITDA ratio
            net_debt_ebitda = company_data.get('net_debt_ebitda')
            if net_debt_ebitda and net_debt_ebitda > self.max_debt_to_ebitda:
                red_flag = f"High Debt Burden: Net Debt/EBITDA = {net_debt_ebitda:.2f}"
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"Debt ratio red flag for {company_data['symbol']}: {red_flag}")
            
            # Check debt growth trend
            debt_growth_data = self._get_debt_growth_data(company_data['id'])
            if debt_growth_data:
                recent_growth = debt_growth_data.get('yoy_growth', 0)
                revenue_growth = debt_growth_data.get('revenue_growth', 0)
                
                # Flag if debt grew >50% YoY without proportional revenue growth
                if recent_growth > 50 and (revenue_growth < recent_growth / 2):
                    red_flag = f"Rapid Debt Growth: {recent_growth:.1f}% vs Revenue {revenue_growth:.1f}%"
                    filter_results['red_flags'].append(red_flag)
                    logger.warning(f"Debt growth red flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['debt_analysis'] = {
                'net_debt_ebitda': net_debt_ebitda,
                'debt_growth_data': debt_growth_data
            }
            
        except Exception as e:
            logger.error(f"Failed to apply debt analysis filter for {company_data['symbol']}: {e}")
    
    def _apply_balance_sheet_filter(self, company_data: Dict[str, Any],
                                  filter_results: Dict[str, Any]):
        """
        Apply balance sheet health filter.
        
        Flags companies with negative shareholder equity.
        """
        logger.info(f"Applying balance sheet filter for {company_data['symbol']}")
        
        try:
            shareholder_equity = company_data.get('shareholder_equity', 0)
            
            if shareholder_equity < 0:
                red_flag = f"Negative Shareholder Equity: ${shareholder_equity:,.0f}"
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"Balance sheet red flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['balance_sheet_health'] = {
                'shareholder_equity': shareholder_equity
            }
            
        except Exception as e:
            logger.error(f"Failed to apply balance sheet filter for {company_data['symbol']}: {e}")
    
    def _apply_liquidity_filter(self, company_data: Dict[str, Any],
                              filter_results: Dict[str, Any]):
        """
        Apply liquidity filter.
        
        Flags companies with low trading volume.
        """
        logger.info(f"Applying liquidity filter for {company_data['symbol']}")
        
        try:
            avg_daily_volume = company_data.get('avg_daily_volume', 0)
            
            if avg_daily_volume < self.min_trading_volume:
                red_flag = f"Low Trading Volume: {avg_daily_volume:,} shares/day"
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"Liquidity red flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['liquidity_analysis'] = {
                'avg_daily_volume': avg_daily_volume,
                'min_threshold': self.min_trading_volume
            }
            
        except Exception as e:
            logger.error(f"Failed to apply liquidity filter for {company_data['symbol']}: {e}")
    
    def _apply_exchange_filter(self, company_data: Dict[str, Any],
                             filter_results: Dict[str, Any]):
        """
        Apply exchange type filter.
        
        Flags companies trading on OTC markets.
        """
        logger.info(f"Applying exchange filter for {company_data['symbol']}")
        
        try:
            exchange = company_data.get('exchange', '').upper()
            
            # OTC market indicators
            otc_indicators = ['PNK', 'OEM', 'OQX', 'OTC', 'OTCQB', 'OTCQX']
            
            if any(indicator in exchange for indicator in otc_indicators):
                red_flag = f"OTC Exchange: {exchange}"
                filter_results['red_flags'].append(red_flag)
                logger.info(f"Exchange info flag for {company_data['symbol']}: {red_flag}")
            
            filter_results['filter_details']['exchange_info'] = {
                'exchange': exchange,
                'is_otc': any(indicator in exchange for indicator in otc_indicators)
            }
            
        except Exception as e:
            logger.error(f"Failed to apply exchange filter for {company_data['symbol']}: {e}")
    
    def _apply_news_red_flag_filter(self, company_data: Dict[str, Any],
                                  filter_results: Dict[str, Any]):
        """
        Apply news red flag filter.
        
        Scans recent news for concerning keywords.
        """
        logger.info(f"Applying news red flag filter for {company_data['symbol']}")
        
        try:
            # Get recent news with red flag keywords
            news_red_flags = self._get_news_red_flags(company_data['id'])
            
            for news_flag in news_red_flags:
                red_flag = f"News Red Flag - {news_flag['keyword']}: {news_flag['headline'][:100]}..."
                filter_results['red_flags'].append(red_flag)
                logger.warning(f"News red flag for {company_data['symbol']}: {news_flag['keyword']}")
            
            filter_results['filter_details']['news_analysis'] = {
                'red_flag_count': len(news_red_flags),
                'red_flags': news_red_flags
            }
            
        except Exception as e:
            logger.error(f"Failed to apply news filter for {company_data['symbol']}: {e}")
    
    def _apply_corporate_action_filter(self, company_data: Dict[str, Any],
                                     filter_results: Dict[str, Any]):
        """
        Apply corporate action filter.
        
        Flags companies that have undergone stock splits or reverse splits in recent history,
        including those detected through backup analysis when yfinance data is missing.
        """
        logger.info(f"Applying corporate action filter for {company_data['symbol']}")
        
        try:
            # Check if company has recent splits (from data fetcher)
            has_recent_splits = company_data.get('has_recent_splits', False)
            split_count = company_data.get('split_count', 0)
            recent_splits = company_data.get('recent_splits', [])
            corporate_action_flags = company_data.get('corporate_action_flags', [])
            
            # Check for backup detection results
            potential_action_detected = company_data.get('potential_action_detected', False)
            
            # Apply scoring and flagging
            if has_recent_splits or potential_action_detected:
                # Calculate penalty based on type of detection
                if has_recent_splits and split_count > 0:
                    # Confirmed corporate actions get standard penalty
                    penalty = self.scoring_config['corporate_action_penalty']
                    filter_results['corporate_action_penalty'] = penalty
                    
                    # Add to red flags for confirmed actions
                    for flag in corporate_action_flags:
                        if flag not in filter_results['red_flags']:
                            filter_results['red_flags'].append(flag)
                    
                    logger.info(f"{company_data['symbol']}: Found {split_count} confirmed corporate action(s) - penalty: {penalty}")
                    
                elif potential_action_detected:
                    # Potential actions get lighter penalty but still flagged
                    penalty = self.scoring_config['corporate_action_penalty'] // 2  # Half penalty for potential actions
                    filter_results['corporate_action_penalty'] = penalty
                    
                    # Add to red flags for potential actions
                    for flag in corporate_action_flags:
                        if flag not in filter_results['red_flags']:
                            filter_results['red_flags'].append(flag)
                    
                    logger.warning(f"{company_data['symbol']}: Potential corporate action detected - penalty: {penalty} (requires manual review)")
                
                # Log split details for manual review
                if recent_splits:
                    for split in recent_splits:
                        split_type = split.get('type', 'Unknown')
                        split_date = split.get('date', 'Unknown')
                        split_ratio = split.get('ratio', 'Unknown')
                        confidence = split.get('confidence', 'HIGH')
                        
                        logger.info(f"{company_data['symbol']}: {split_type} on {split_date} "
                                  f"(ratio: {split_ratio}, confidence: {confidence})")
            else:
                # No corporate actions detected
                filter_results['corporate_action_penalty'] = 0
                logger.debug(f"{company_data['symbol']}: No corporate actions detected")
                
        except Exception as e:
            logger.error(f"Error applying corporate action filter for {company_data['symbol']}: {e}")
            filter_results['corporate_action_penalty'] = 0
    
    def _calculate_quality_score(self, filter_results: Dict[str, Any]) -> int:
        """
        Calculate Weschler Quality Score based on filter results.
        
        Args:
            filter_results: Dictionary containing filter results
            
        Returns:
            Quality score (higher is better)
        """
        base_score = 100  # Start with perfect score
        
        # Apply penalties for each red flag
        for red_flag in filter_results['red_flags']:
            if "No Recent SEC Filings" in red_flag:
                base_score += self.scoring_config['sec_filing_penalty']
            elif "Persistent Negative FCF" in red_flag:
                base_score += self.scoring_config['fcf_penalty']
            elif "Persistent Operating Losses" in red_flag:
                base_score += self.scoring_config['operating_loss_penalty']
            elif "High Debt Burden" in red_flag:
                base_score += self.scoring_config['high_debt_penalty']
            elif "Negative Shareholder Equity" in red_flag:
                base_score += self.scoring_config['negative_equity_penalty']
            elif "Low Trading Volume" in red_flag:
                base_score += self.scoring_config['low_volume_penalty']
            elif "OTC Exchange" in red_flag:
                base_score += self.scoring_config['otc_penalty']
            elif "News Red Flag" in red_flag:
                base_score += self.scoring_config['news_red_flag_penalty']
            elif "Corporate Action" in red_flag:
                base_score += self.scoring_config['corporate_action_penalty']
        
        # Ensure score doesn't go below 0
        return max(0, base_score)
    
    def _get_historical_fcf_data(self, company_id: int) -> List[Dict[str, Any]]:
        """Get historical free cash flow data."""
        try:
            with self.db_manager:
                sql = """
                SELECT fiscal_year, statement_data
                FROM financial_statements
                WHERE company_id = ? AND statement_type = 'cash_flow'
                ORDER BY fiscal_year DESC
                LIMIT 5
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                fcf_data = []
                for row in rows:
                    try:
                        statement_data = json.loads(row['statement_data'])
                        # Extract free cash flow from statement data
                        fcf = self._extract_fcf_from_statement(statement_data)
                        fcf_data.append({
                            'fiscal_year': row['fiscal_year'],
                            'fcf': fcf
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                return fcf_data
                
        except Exception as e:
            logger.error(f"Failed to get historical FCF data: {e}")
            return []
    
    def _get_historical_operating_income_data(self, company_id: int) -> List[Dict[str, Any]]:
        """Get historical operating income data."""
        try:
            with self.db_manager:
                sql = """
                SELECT fiscal_year, statement_data
                FROM financial_statements
                WHERE company_id = ? AND statement_type = 'income'
                ORDER BY fiscal_year DESC
                LIMIT 5
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                operating_data = []
                for row in rows:
                    try:
                        statement_data = json.loads(row['statement_data'])
                        # Extract operating income from statement data
                        operating_income = self._extract_operating_income_from_statement(statement_data)
                        operating_data.append({
                            'fiscal_year': row['fiscal_year'],
                            'operating_income': operating_income
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                return operating_data
                
        except Exception as e:
            logger.error(f"Failed to get historical operating income data: {e}")
            return []
    
    def _get_debt_growth_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get debt growth analysis data."""
        try:
            with self.db_manager:
                sql = """
                SELECT fiscal_year, statement_data
                FROM financial_statements
                WHERE company_id = ? AND statement_type = 'balance_sheet'
                ORDER BY fiscal_year DESC
                LIMIT 2
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                if len(rows) < 2:
                    return None
                
                # Calculate debt growth
                current_year = json.loads(rows[0]['statement_data'])
                previous_year = json.loads(rows[1]['statement_data'])
                
                current_debt = self._extract_total_debt_from_statement(current_year)
                previous_debt = self._extract_total_debt_from_statement(previous_year)
                
                if previous_debt > 0:
                    yoy_growth = ((current_debt - previous_debt) / previous_debt) * 100
                else:
                    yoy_growth = 0
                
                # Get revenue growth for comparison
                revenue_growth = self._get_revenue_growth(company_id)
                
                return {
                    'yoy_growth': yoy_growth,
                    'revenue_growth': revenue_growth,
                    'current_debt': current_debt,
                    'previous_debt': previous_debt
                }
                
        except Exception as e:
            logger.error(f"Failed to get debt growth data: {e}")
            return None
    
    def _get_news_red_flags(self, company_id: int) -> List[Dict[str, Any]]:
        """Get news articles with red flag keywords."""
        try:
            with self.db_manager:
                sql = """
                SELECT headline, red_flag_keywords
                FROM news
                WHERE company_id = ? AND red_flag_keywords != '[]'
                ORDER BY published_date DESC
                LIMIT 10
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                red_flags = []
                for row in rows:
                    try:
                        keywords = json.loads(row['red_flag_keywords'])
                        for keyword in keywords:
                            red_flags.append({
                                'keyword': keyword,
                                'headline': row['headline']
                            })
                    except json.JSONDecodeError:
                        continue
                
                return red_flags
                
        except Exception as e:
            logger.error(f"Failed to get news red flags: {e}")
            return []
    
    def _extract_fcf_from_statement(self, statement_data: Dict[str, Any]) -> float:
        """Extract free cash flow from cash flow statement."""
        # Try various FCF line items
        fcf_items = [
            'Free Cash Flow',
            'FreeCashFlow',
            'Operating Cash Flow',
            'OperatingCashFlow',
            'Net Cash from Operations'
        ]
        
        for item in fcf_items:
            if item in statement_data:
                return float(statement_data[item])
        
        return 0.0
    
    def _extract_operating_income_from_statement(self, statement_data: Dict[str, Any]) -> float:
        """Extract operating income from income statement."""
        # Try various operating income line items
        operating_items = [
            'Operating Income',
            'OperatingIncome',
            'EBIT',
            'Operating Profit',
            'Income from Operations'
        ]
        
        for item in operating_items:
            if item in statement_data:
                return float(statement_data[item])
        
        return 0.0
    
    def _extract_total_debt_from_statement(self, statement_data: Dict[str, Any]) -> float:
        """Extract total debt from balance sheet."""
        # Try various debt line items
        debt_items = [
            'Total Debt',
            'TotalDebt',
            'Long Term Debt',
            'Short Term Debt',
            'Total Liabilities'
        ]
        
        for item in debt_items:
            if item in statement_data:
                return float(statement_data[item])
        
        return 0.0
    
    def _get_revenue_growth(self, company_id: int) -> float:
        """Get revenue growth rate."""
        try:
            with self.db_manager:
                sql = """
                SELECT fiscal_year, statement_data
                FROM financial_statements
                WHERE company_id = ? AND statement_type = 'income'
                ORDER BY fiscal_year DESC
                LIMIT 2
                """
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                if len(rows) < 2:
                    return 0.0
                
                current_year = json.loads(rows[0]['statement_data'])
                previous_year = json.loads(rows[1]['statement_data'])
                
                current_revenue = self._extract_revenue_from_statement(current_year)
                previous_revenue = self._extract_revenue_from_statement(previous_year)
                
                if previous_revenue > 0:
                    return ((current_revenue - previous_revenue) / previous_revenue) * 100
                else:
                    return 0.0
                    
        except Exception as e:
            logger.error(f"Failed to get revenue growth: {e}")
            return 0.0
    
    def _extract_revenue_from_statement(self, statement_data: Dict[str, Any]) -> float:
        """Extract revenue from income statement."""
        revenue_items = [
            'Total Revenue',
            'TotalRevenue',
            'Revenue',
            'Net Sales',
            'Sales'
        ]
        
        for item in revenue_items:
            if item in statement_data:
                return float(statement_data[item])
        
        return 0.0
    
    def _update_company_filtering_results(self, company_id: int, 
                                        filter_results: Dict[str, Any]):
        """Update company record with filtering results."""
        try:
            with self.db_manager:
                sql = """
                UPDATE companies 
                SET red_flags_list = ?, disqualified_flag = ?, 
                    weschler_quality_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                
                red_flags_json = json.dumps(filter_results['red_flags'])
                disqualified = 1 if filter_results['disqualified'] else 0
                
                self.db_manager.cursor.execute(sql, (
                    red_flags_json,
                    disqualified,
                    filter_results['quality_score'],
                    company_id
                ))
                
                self.db_manager.connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to update company filtering results: {e}")
    
    def process_all_companies(self) -> Dict[str, Any]:
        """
        Process quality filters for all companies in the database.
        
        Returns:
            Summary of processing results
        """
        logger.info("Starting quality filter processing for all companies")
        
        try:
            # Get all companies
            with self.db_manager:
                sql = "SELECT id, symbol FROM companies"
                self.db_manager.cursor.execute(sql)
                companies = self.db_manager.cursor.fetchall()
            
            if not companies:
                logger.warning("No companies found in database")
                return {'processed': 0, 'errors': 0}
            
            processed_count = 0
            error_count = 0
            
            for company in companies:
                try:
                    company_id = company['id']
                    symbol = company['symbol']
                    
                    logger.info(f"Processing quality filters for {symbol}")
                    
                    # Apply all filters
                    filter_results = self.apply_all_filters(company_id)
                    
                    if filter_results:
                        processed_count += 1
                        logger.info(f"Successfully processed {symbol} - Score: {filter_results['quality_score']}")
                    else:
                        error_count += 1
                        logger.error(f"Failed to process {symbol}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing company {company.get('symbol', 'unknown')}: {e}")
            
            summary = {
                'processed': processed_count,
                'errors': error_count,
                'total': len(companies)
            }
            
            logger.info(f"Quality filter processing completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to process quality filters for all companies: {e}")
            return {'processed': 0, 'errors': 1} 