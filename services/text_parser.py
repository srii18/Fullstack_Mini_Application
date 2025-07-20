import re
from datetime import datetime
from typing import Optional, Dict, List
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

class TextParser:
    """Service for parsing structured data from extracted text"""
    
    def __init__(self):
        # Common vendor patterns and categories
        self.vendor_categories = {
            # Grocery stores
            'walmart': 'grocery', 'target': 'grocery', 'kroger': 'grocery',
            'safeway': 'grocery', 'whole foods': 'grocery', 'costco': 'grocery',
            
            # Utilities
            'electric': 'utilities', 'electricity': 'utilities', 'power': 'utilities',
            'gas': 'utilities', 'water': 'utilities', 'internet': 'utilities',
            'cable': 'utilities', 'phone': 'utilities', 'telecom': 'utilities',
            
            # Restaurants
            'restaurant': 'dining', 'cafe': 'dining', 'pizza': 'dining',
            'mcdonald': 'dining', 'starbucks': 'dining', 'subway': 'dining',
            
            # Retail
            'amazon': 'retail', 'ebay': 'retail', 'store': 'retail',
            'shop': 'retail', 'mall': 'retail',
            
            # Transportation
            'gas station': 'transportation', 'fuel': 'transportation',
            'uber': 'transportation', 'lyft': 'transportation', 'taxi': 'transportation',
            
            # Healthcare
            'pharmacy': 'healthcare', 'hospital': 'healthcare',
            'clinic': 'healthcare', 'medical': 'healthcare'
        }
        
        # Amount patterns (various currency formats)
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
            r'total[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Total: $123.45
            r'amount[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Amount: 123.45
            r'subtotal[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Subtotal: $123.45
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Generic decimal amounts
        ]
        
        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY, MM-DD-YY
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY/MM/DD
            r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',  # January 15, 2024
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',    # 15 January 2024
        ]
        
        # Vendor name patterns
        self.vendor_patterns = [
            r'(?:store|shop|market|company)[:\s]*([A-Za-z\s&\-\'\.]+)',
            r'([A-Z][A-Za-z\s&\-\'\.]{2,30})\s*(?:inc|llc|corp|ltd)?',
            r'bill\s+from[:\s]*([A-Za-z\s&\-\'\.]+)',
            r'merchant[:\s]*([A-Za-z\s&\-\'\.]+)',
        ]
    
    def parse_receipt_data(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse structured data from receipt text
        Returns: dict with vendor, date, amount, category
        """
        result = {
            'vendor': None,
            'transaction_date': None,
            'amount': None,
            'category': None
        }
        
        if not text or not text.strip():
            return result
        
        text_lower = text.lower()
        
        # Extract amount
        result['amount'] = self._extract_amount(text)
        
        # Extract date
        result['transaction_date'] = self._extract_date(text)
        
        # Extract vendor
        result['vendor'] = self._extract_vendor(text)
        
        # Determine category
        result['category'] = self._determine_category(text_lower, result['vendor'])
        
        logger.info(f"Parsed data: {result}")
        return result
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    amount_str = match.replace(',', '')
                    amount = float(amount_str)
                    if 0.01 <= amount <= 999999:  # Reasonable amount range
                        amounts.append(amount)
                except ValueError:
                    continue
        
        if amounts:
            # Return the largest amount found (likely the total)
            return max(amounts)
        
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract transaction date from text"""
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Use dateutil parser for flexible date parsing
                    parsed_date = date_parser.parse(match, fuzzy=True)
                    
                    # Validate date is reasonable (not too far in future/past)
                    current_year = datetime.now().year
                    if 2000 <= parsed_date.year <= current_year + 1:
                        return parsed_date
                        
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor/merchant name from text"""
        # Try specific vendor patterns first
        for pattern in self.vendor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                vendor = match.strip()
                if len(vendor) >= 3 and vendor.replace(' ', '').isalpha():
                    return self._clean_vendor_name(vendor)
        
        # Fallback: look for capitalized words at the beginning
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) >= 3:
                # Check if line contains mostly letters and spaces
                if re.match(r'^[A-Za-z\s&\-\'\.]{3,50}$', line):
                    return self._clean_vendor_name(line)
        
        return None
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """Clean and normalize vendor name"""
        # Remove common suffixes
        suffixes = ['inc', 'llc', 'corp', 'ltd', 'co', 'company']
        vendor_lower = vendor.lower()
        
        for suffix in suffixes:
            if vendor_lower.endswith(f' {suffix}'):
                vendor = vendor[:-len(suffix)-1]
                break
        
        # Capitalize properly
        return ' '.join(word.capitalize() for word in vendor.split())
    
    def _determine_category(self, text_lower: str, vendor: str) -> Optional[str]:
        """Determine category based on text content and vendor"""
        # Check vendor name first
        if vendor:
            vendor_lower = vendor.lower()
            for keyword, category in self.vendor_categories.items():
                if keyword in vendor_lower:
                    return category
        
        # Check full text for category keywords
        for keyword, category in self.vendor_categories.items():
            if keyword in text_lower:
                return category
        
        # Default categories based on common patterns
        if any(word in text_lower for word in ['bill', 'utility', 'electric', 'gas', 'water']):
            return 'utilities'
        elif any(word in text_lower for word in ['grocery', 'food', 'market', 'supermarket']):
            return 'grocery'
        elif any(word in text_lower for word in ['restaurant', 'cafe', 'dining', 'food']):
            return 'dining'
        elif any(word in text_lower for word in ['store', 'retail', 'shop', 'purchase']):
            return 'retail'
        
        return 'other'
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords for search indexing"""
        if not text:
            return []
        
        # Remove special characters and split into words
        words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
            'did', 'she', 'use', 'way', 'will', 'with'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) >= 3]
        
        # Return unique keywords
        return list(set(keywords))
