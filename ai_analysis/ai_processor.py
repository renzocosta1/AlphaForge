"""
AI Analysis Processor for AlphaForge.
Provides AI-assisted analysis of SEC filings and company data.
"""

import logging
import openai
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import time
import os

from config import config
from database.schema import DatabaseManager
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class AIProcessor:
    """
    AI processor for analyzing SEC filings and generating summaries.
    
    This class provides AI-assisted analysis using OpenAI's API to generate
    risk summaries and management analysis from SEC filings.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize AI processor.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.rate_limiter = RateLimiter()
        self.openai_api_key = config.OPENAI_API_KEY
        self.model = "gpt-3.5-turbo"  # Default model
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.ai_enabled = True
            logger.info("AI analysis enabled with OpenAI API")
        else:
            self.ai_enabled = False
            logger.warning("AI analysis disabled - no OpenAI API key provided")
    
    def is_enabled(self) -> bool:
        """Check if AI analysis is enabled."""
        return self.ai_enabled
    
    def analyze_risk_factors(self, company_id: int, filing_text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze risk factors from 10-K filing.
        
        Args:
            company_id: Company ID
            filing_text: Text from 10-K risk factors section
            
        Returns:
            Dictionary with risk analysis or None if failed
        """
        if not self.is_enabled():
            return None
        
        logger.info(f"Analyzing risk factors for company ID {company_id}")
        
        try:
            # Rate limiting for OpenAI API
            self.rate_limiter.wait_if_needed('openai')
            
            # Prepare prompt for risk analysis
            prompt = self._create_risk_analysis_prompt(filing_text)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in risk assessment for investment decisions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Extract and process response
            analysis_text = response.choices[0].message.content
            
            # Structure the analysis
            risk_analysis = {
                'summary': analysis_text,
                'key_risks': self._extract_key_risks(analysis_text),
                'risk_score': self._calculate_risk_score(analysis_text),
                'model_used': self.model,
                'confidence_score': 0.85,  # Default confidence
                'created_at': datetime.now().isoformat()
            }
            
            # Store in database
            self._store_ai_summary(company_id, 'risk_summary', risk_analysis)
            
            logger.info(f"Risk analysis completed for company ID {company_id}")
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze risk factors: {e}")
            return None
    
    def analyze_management_governance(self, company_id: int, filing_text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze management and governance from DEF 14A filing.
        
        Args:
            company_id: Company ID
            filing_text: Text from DEF 14A filing
            
        Returns:
            Dictionary with management analysis or None if failed
        """
        if not self.is_enabled():
            return None
        
        logger.info(f"Analyzing management governance for company ID {company_id}")
        
        try:
            # Rate limiting for OpenAI API
            self.rate_limiter.wait_if_needed('openai')
            
            # Prepare prompt for management analysis
            prompt = self._create_management_analysis_prompt(filing_text)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a corporate governance expert analyzing executive compensation and board structures."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            # Extract and process response
            analysis_text = response.choices[0].message.content
            
            # Structure the analysis
            management_analysis = {
                'summary': analysis_text,
                'governance_flags': self._extract_governance_flags(analysis_text),
                'compensation_concerns': self._extract_compensation_concerns(analysis_text),
                'model_used': self.model,
                'confidence_score': 0.80,  # Default confidence
                'created_at': datetime.now().isoformat()
            }
            
            # Store in database
            self._store_ai_summary(company_id, 'management_summary', management_analysis)
            
            logger.info(f"Management analysis completed for company ID {company_id}")
            return management_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze management governance: {e}")
            return None
    
    def _create_risk_analysis_prompt(self, filing_text: str) -> str:
        """Create prompt for risk factor analysis."""
        # Truncate text if too long
        max_length = 8000  # Leave room for prompt text
        if len(filing_text) > max_length:
            filing_text = filing_text[:max_length] + "... [truncated]"
        
        prompt = f"""
Analyze the following risk factors from a company's 10-K filing and provide a concise investment risk assessment.

Focus on:
1. The top 3-5 most critical operational and financial risks
2. Potential red flags that could indicate investment concerns
3. Overall risk level (Low, Medium, High)

Risk Factors Text:
{filing_text}

Please provide a structured analysis with:
- Executive Summary (2-3 sentences)
- Critical Risks (bullet points)
- Red Flags (if any)
- Overall Risk Assessment

Keep the response under 400 words and focus on actionable insights for investment decision-making.
"""
        return prompt
    
    def _create_management_analysis_prompt(self, filing_text: str) -> str:
        """Create prompt for management and governance analysis."""
        # Truncate text if too long
        max_length = 8000  # Leave room for prompt text
        if len(filing_text) > max_length:
            filing_text = filing_text[:max_length] + "... [truncated]"
        
        prompt = f"""
Analyze the following executive compensation and board structure information from a company's proxy statement (DEF 14A).

Focus on:
1. Executive compensation structure and alignment with performance
2. Board independence and composition
3. Potential governance red flags
4. Management accountability and oversight

Proxy Statement Text:
{filing_text}

Please provide a structured analysis with:
- Executive Summary (2-3 sentences)
- Compensation Analysis (alignment with performance)
- Board Structure Assessment
- Governance Concerns (if any)
- Overall Governance Rating

Keep the response under 400 words and focus on potential red flags for investors.
"""
        return prompt
    
    def _extract_key_risks(self, analysis_text: str) -> List[str]:
        """Extract key risks from AI analysis."""
        risks = []
        
        # Simple extraction based on common patterns
        lines = analysis_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                risk = line.lstrip('•-* ').strip()
                if risk and len(risk) > 10:  # Filter out short/empty items
                    risks.append(risk)
        
        return risks[:5]  # Return top 5 risks
    
    def _calculate_risk_score(self, analysis_text: str) -> str:
        """Calculate risk score from analysis text."""
        text_lower = analysis_text.lower()
        
        # Simple keyword-based scoring
        high_risk_keywords = ['critical', 'severe', 'significant', 'major', 'substantial', 'concerning']
        medium_risk_keywords = ['moderate', 'notable', 'important', 'relevant']
        low_risk_keywords = ['minor', 'limited', 'manageable', 'acceptable']
        
        high_count = sum(1 for keyword in high_risk_keywords if keyword in text_lower)
        medium_count = sum(1 for keyword in medium_risk_keywords if keyword in text_lower)
        low_count = sum(1 for keyword in low_risk_keywords if keyword in text_lower)
        
        if high_count >= 2:
            return "High"
        elif medium_count >= 2 or high_count >= 1:
            return "Medium"
        else:
            return "Low"
    
    def _extract_governance_flags(self, analysis_text: str) -> List[str]:
        """Extract governance flags from analysis."""
        flags = []
        text_lower = analysis_text.lower()
        
        # Common governance red flags
        flag_patterns = [
            ('excessive compensation', 'Excessive Executive Compensation'),
            ('lack of independence', 'Board Independence Issues'),
            ('related party', 'Related Party Transactions'),
            ('poor oversight', 'Inadequate Board Oversight'),
            ('conflicts of interest', 'Conflicts of Interest'),
            ('insider trading', 'Insider Trading Concerns')
        ]
        
        for pattern, flag_name in flag_patterns:
            if pattern in text_lower:
                flags.append(flag_name)
        
        return flags
    
    def _extract_compensation_concerns(self, analysis_text: str) -> List[str]:
        """Extract compensation concerns from analysis."""
        concerns = []
        text_lower = analysis_text.lower()
        
        # Common compensation concerns
        concern_patterns = [
            ('misaligned', 'Misaligned with Performance'),
            ('excessive', 'Excessive Pay Levels'),
            ('poor performance', 'Pay Despite Poor Performance'),
            ('lack of clawback', 'No Clawback Provisions'),
            ('guaranteed', 'Guaranteed Bonuses')
        ]
        
        for pattern, concern_name in concern_patterns:
            if pattern in text_lower:
                concerns.append(concern_name)
        
        return concerns
    
    def _store_ai_summary(self, company_id: int, summary_type: str, analysis: Dict[str, Any]):
        """Store AI summary in database."""
        try:
            with self.db_manager:
                sql = """
                INSERT INTO ai_summaries (
                    company_id, summary_type, summary_text, model_used, confidence_score
                ) VALUES (?, ?, ?, ?, ?)
                """
                
                summary_text = json.dumps(analysis)
                
                self.db_manager.cursor.execute(sql, (
                    company_id,
                    summary_type,
                    summary_text,
                    analysis.get('model_used', self.model),
                    analysis.get('confidence_score', 0.0)
                ))
                
                self.db_manager.connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to store AI summary: {e}")
    
    def get_company_ai_summaries(self, company_id: int) -> Dict[str, Any]:
        """Get all AI summaries for a company."""
        try:
            with self.db_manager:
                sql = """
                SELECT summary_type, summary_text, model_used, confidence_score, created_at
                FROM ai_summaries
                WHERE company_id = ?
                ORDER BY created_at DESC
                """
                
                self.db_manager.cursor.execute(sql, (company_id,))
                rows = self.db_manager.cursor.fetchall()
                
                summaries = {}
                for row in rows:
                    summary_type = row['summary_type']
                    try:
                        summary_data = json.loads(row['summary_text'])
                        summaries[summary_type] = summary_data
                    except json.JSONDecodeError:
                        # Fallback for simple text summaries
                        summaries[summary_type] = {
                            'summary': row['summary_text'],
                            'model_used': row['model_used'],
                            'confidence_score': row['confidence_score'],
                            'created_at': row['created_at']
                        }
                
                return summaries
                
        except Exception as e:
            logger.error(f"Failed to get AI summaries: {e}")
            return {}
    
    def process_company_filings(self, company_id: int, symbol: str) -> Dict[str, Any]:
        """
        Process all available SEC filings for a company with AI analysis.
        
        Args:
            company_id: Company ID
            symbol: Company symbol
            
        Returns:
            Dictionary with AI analysis results
        """
        if not self.is_enabled():
            return {'enabled': False, 'message': 'AI analysis disabled - no API key'}
        
        logger.info(f"Processing AI analysis for {symbol}")
        
        results = {
            'enabled': True,
            'company_id': company_id,
            'symbol': symbol,
            'analyses': {}
        }
        
        try:
            # Get available SEC filings
            with self.db_manager:
                sql = """
                SELECT filing_type, local_path, filing_date
                FROM sec_filings
                WHERE company_id = ? AND download_status = 'completed'
                ORDER BY filing_date DESC
                """
                
                self.db_manager.cursor.execute(sql, (company_id,))
                filings = self.db_manager.cursor.fetchall()
            
            # Process each filing type
            for filing in filings:
                filing_type = filing['filing_type']
                local_path = filing['local_path']
                
                if not local_path or not os.path.exists(local_path):
                    continue
                
                # Read filing content
                try:
                    with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                        filing_content = f.read()
                except Exception as e:
                    logger.error(f"Failed to read filing {local_path}: {e}")
                    continue
                
                # Process based on filing type
                if filing_type == '10-K' and 'risk_summary' not in results['analyses']:
                    # Extract risk factors section
                    risk_text = self._extract_risk_factors_section(filing_content)
                    if risk_text:
                        analysis = self.analyze_risk_factors(company_id, risk_text)
                        if analysis:
                            results['analyses']['risk_summary'] = analysis
                
                elif filing_type == 'DEF 14A' and 'management_summary' not in results['analyses']:
                    # Extract compensation and governance sections
                    mgmt_text = self._extract_management_sections(filing_content)
                    if mgmt_text:
                        analysis = self.analyze_management_governance(company_id, mgmt_text)
                        if analysis:
                            results['analyses']['management_summary'] = analysis
            
            logger.info(f"AI analysis completed for {symbol}: {len(results['analyses'])} analyses generated")
            
        except Exception as e:
            logger.error(f"Failed to process AI analysis for {symbol}: {e}")
            results['error'] = str(e)
        
        return results
    
    def _extract_risk_factors_section(self, filing_content: str) -> Optional[str]:
        """Extract risk factors section from 10-K filing."""
        # Simple regex pattern to find risk factors section
        import re
        
        pattern = r'(?i)item\s+1a\.?\s*risk\s+factors(.*?)(?=item\s+1b\.?|item\s+2\.?|$)'
        match = re.search(pattern, filing_content, re.DOTALL)
        
        if match:
            risk_text = match.group(1).strip()
            # Limit length for AI processing
            if len(risk_text) > 20000:
                risk_text = risk_text[:20000] + "... [truncated]"
            return risk_text
        
        return None
    
    def _extract_management_sections(self, filing_content: str) -> Optional[str]:
        """Extract management and governance sections from DEF 14A."""
        # Simple extraction of compensation and governance text
        import re
        
        patterns = [
            r'(?i)executive\s+compensation(.*?)(?=director\s+compensation|securities\s+ownership|$)',
            r'(?i)board\s+of\s+directors(.*?)(?=executive\s+compensation|$)',
            r'(?i)corporate\s+governance(.*?)(?=executive\s+compensation|$)'
        ]
        
        extracted_text = ""
        for pattern in patterns:
            match = re.search(pattern, filing_content, re.DOTALL)
            if match:
                extracted_text += match.group(1).strip() + "\n\n"
        
        if extracted_text.strip():
            # Limit length for AI processing
            if len(extracted_text) > 15000:
                extracted_text = extracted_text[:15000] + "... [truncated]"
            return extracted_text
        
        return None 