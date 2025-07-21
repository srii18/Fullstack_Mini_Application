import re
from datetime import datetime
from typing import Optional, Dict, List
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

class TextParser:
    """Service for parsing structured data from extracted text"""
    
    def __init__(self):
        # Common vendor patterns and categories (multi-language)
        self.vendor_categories = {
            # Grocery stores (English)
            'walmart': 'grocery', 'target': 'grocery', 'kroger': 'grocery',
            'safeway': 'grocery', 'whole foods': 'grocery', 'costco': 'grocery',
            # Grocery stores (Spanish)
            'supermercado': 'grocery', 'mercado': 'grocery', 'tienda': 'grocery',
            # Grocery stores (French)
            'supermarché': 'grocery', 'marché': 'grocery', 'épicerie': 'grocery',
            
            # Utilities (English)
            'electric': 'utilities', 'electricity': 'utilities', 'power': 'utilities',
            'gas': 'utilities', 'water': 'utilities', 'internet': 'utilities',
            'cable': 'utilities', 'phone': 'utilities', 'telecom': 'utilities',
            # Utilities (Spanish)
            'electricidad': 'utilities', 'agua': 'utilities', 'teléfono': 'utilities',
            # Utilities (French)
            'électricité': 'utilities', 'eau': 'utilities', 'téléphone': 'utilities',
            
            # Restaurants (English)
            'restaurant': 'dining', 'cafe': 'dining', 'pizza': 'dining',
            'mcdonald': 'dining', 'starbucks': 'dining', 'subway': 'dining',
            # Restaurants (Spanish)
            'restaurante': 'dining', 'café': 'dining', 'comida': 'dining',
            # Restaurants (French)
            'café': 'dining', 'brasserie': 'dining', 'bistro': 'dining',
            
            # Retail (English)
            'amazon': 'retail', 'ebay': 'retail', 'store': 'retail',
            'shop': 'retail', 'mall': 'retail',
            # Retail (Spanish)
            'tienda': 'retail', 'almacén': 'retail', 'centro comercial': 'retail',
            # Retail (French)
            'magasin': 'retail', 'boutique': 'retail', 'centre commercial': 'retail',
            
            # Transportation (English)
            'gas station': 'transportation', 'fuel': 'transportation',
            'uber': 'transportation', 'lyft': 'transportation', 'taxi': 'transportation',
            # Transportation (Spanish)
            'gasolinera': 'transportation', 'combustible': 'transportation', 'taxi': 'transportation',
            # Transportation (French)
            'station-service': 'transportation', 'carburant': 'transportation', 'taxi': 'transportation',
            
            # Healthcare (English)
            'pharmacy': 'healthcare', 'hospital': 'healthcare',
            'clinic': 'healthcare', 'medical': 'healthcare',
            # Healthcare (Spanish)
            'farmacia': 'healthcare', 'hospital': 'healthcare', 'clínica': 'healthcare',
            # Healthcare (French)
            'pharmacie': 'healthcare', 'hôpital': 'healthcare', 'clinique': 'healthcare'
        }
        
        # Multi-currency patterns
        self.currency_patterns = {
            'USD': {
                'symbols': ['$', 'USD', 'US$'],
                'patterns': [
                    r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',
                    r'USD\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'US\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ]
            },
            'EUR': {
                'symbols': ['€', 'EUR'],
                'patterns': [
                    r'€\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                    r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*€',
                    r'EUR\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                ]
            },
            'GBP': {
                'symbols': ['£', 'GBP'],
                'patterns': [
                    r'£\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*£',
                    r'GBP\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                ]
            },
            'JPY': {
                'symbols': ['¥', 'JPY'],
                'patterns': [
                    r'¥\s*(\d{1,3}(?:,\d{3})*)',
                    r'(\d{1,3}(?:,\d{3})*)\s*¥',
                    r'JPY\s*(\d{1,3}(?:,\d{3})*)',
                ]
            }
        }
        
        # Legacy amount patterns for backward compatibility
        self.amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
            r'total[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Total: $123.45
            r'amount[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Amount: 123.45
            r'subtotal[:\s]*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Subtotal: $123.45
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Generic decimal amounts
        ]
        
        # Multi-language date patterns
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # MM/DD/YYYY, MM-DD-YY
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',    # YYYY/MM/DD
            r'\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',  # January 15, 2024
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',    # 15 January 2024
            # Spanish patterns
            r'\b(\d{1,2}\s+de\s+[A-Za-z]{3,9}\s+de\s+\d{4})\b',  # 15 de enero de 2024
            # French patterns
            r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',  # 15 janvier 2024
        ]
        
        # Multi-language month mappings
        self.month_mappings = {
            # English
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            # Spanish
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            # French
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
            'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
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
    
    def detect_currency(self, text: str) -> Dict[str, any]:
        """Detect currency and extract amount with currency info"""
        currency_info = {
            'currency_code': 'USD',  # Default
            'symbol': '$',
            'amount': None,
            'detected_currencies': []
        }
        
        amounts_by_currency = {}
        
        # Check each currency pattern
        for currency_code, currency_data in self.currency_patterns.items():
            for pattern in currency_data['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        # Clean the amount string (handle both comma and period separators)
                        clean_amount = match.replace(',', '').replace(' ', '')
                        # Handle European format (comma as decimal separator)
                        if currency_code == 'EUR' and ',' in match and '.' not in match:
                            clean_amount = clean_amount.replace(',', '.')
                        
                        amount = float(clean_amount)
                        
                        # Validate amount is reasonable
                        if 0.01 <= amount <= 1000000:
                            if currency_code not in amounts_by_currency:
                                amounts_by_currency[currency_code] = []
                            amounts_by_currency[currency_code].append(amount)
                            
                    except (ValueError, TypeError):
                        continue
        
        # Determine primary currency (one with most/largest amounts)
        if amounts_by_currency:
            primary_currency = max(amounts_by_currency.keys(), 
                                 key=lambda k: (len(amounts_by_currency[k]), max(amounts_by_currency[k])))
            
            currency_info['currency_code'] = primary_currency
            currency_info['symbol'] = self.currency_patterns[primary_currency]['symbols'][0]
            currency_info['amount'] = max(amounts_by_currency[primary_currency])
            currency_info['detected_currencies'] = list(amounts_by_currency.keys())
        
        return currency_info
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text (enhanced with currency detection)"""
        # First try currency detection
        currency_info = self.detect_currency(text)
        if currency_info['amount']:
            return currency_info['amount']
        
        # Fallback to legacy patterns
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean the amount string (remove commas)
                    clean_amount = match.replace(',', '')
                    amount = float(clean_amount)
                    
                    # Validate amount is reasonable (not too large or small)
                    if 0.01 <= amount <= 1000000:
                        amounts.append(amount)
                        
                except (ValueError, TypeError):
                    continue
        
        # Return the largest amount found (likely the total)
        return max(amounts) if amounts else None
    
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
