import requests
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service for currency detection and conversion"""
    
    def __init__(self):
        # Currency symbols and their codes
        self.currency_symbols = {
            '$': 'USD',
            '€': 'EUR', 
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR',
            '₩': 'KRW',
            'C$': 'CAD',
            'A$': 'AUD',
            'CHF': 'CHF',
            'SEK': 'SEK',
            'NOK': 'NOK',
            'DKK': 'DKK',
            'PLN': 'PLN',
            'CZK': 'CZK',
            'HUF': 'HUF',
            'RUB': 'RUB',
            'CNY': 'CNY',
            'BRL': 'BRL',
            'MXN': 'MXN'
        }
        
        # Default exchange rates (fallback if API fails)
        self.default_rates = {
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0,
            'INR': 74.0,
            'CAD': 1.25,
            'AUD': 1.35,
            'CHF': 0.92,
            'CNY': 6.45
        }
        
        # Cache for exchange rates
        self.rate_cache = {}
        self.cache_timestamp = None
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
    def get_currency_from_symbol(self, symbol: str) -> str:
        """Get currency code from symbol"""
        return self.currency_symbols.get(symbol, 'USD')
    
    def get_exchange_rates(self, base_currency: str = 'USD') -> Dict[str, float]:
        """
        Get current exchange rates from API or cache
        Returns rates relative to base currency
        """
        try:
            # Check cache first
            if (self.cache_timestamp and 
                datetime.now() - self.cache_timestamp < self.cache_duration and
                base_currency in self.rate_cache):
                logger.info(f"Using cached exchange rates for {base_currency}")
                return self.rate_cache[base_currency]
            
            # Try to fetch from free API (exchangerate-api.com)
            # Note: In production, you'd want to use a paid service for better reliability
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Cache the rates
                if base_currency not in self.rate_cache:
                    self.rate_cache[base_currency] = {}
                self.rate_cache[base_currency] = rates
                self.cache_timestamp = datetime.now()
                
                logger.info(f"Fetched fresh exchange rates for {base_currency}")
                return rates
            else:
                logger.warning(f"Exchange rate API returned status {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Failed to fetch exchange rates: {str(e)}")
        
        # Fallback to default rates
        logger.info(f"Using default exchange rates for {base_currency}")
        if base_currency == 'USD':
            return self.default_rates
        else:
            # Convert default USD rates to requested base currency
            usd_rate = self.default_rates.get(base_currency, 1.0)
            converted_rates = {}
            for currency, rate in self.default_rates.items():
                converted_rates[currency] = rate / usd_rate
            converted_rates['USD'] = 1.0 / usd_rate
            return converted_rates
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another
        """
        try:
            if from_currency == to_currency:
                return amount
            
            # Get exchange rates with from_currency as base
            rates = self.get_exchange_rates(from_currency)
            
            if to_currency in rates:
                converted_amount = amount * rates[to_currency]
                logger.info(f"Converted {amount} {from_currency} to {converted_amount:.2f} {to_currency}")
                return round(converted_amount, 2)
            else:
                logger.warning(f"Exchange rate not available for {to_currency}")
                return None
                
        except Exception as e:
            logger.error(f"Currency conversion failed: {str(e)}")
            return None
    
    def detect_and_convert_currency(self, text: str, target_currency: str = 'USD') -> Dict[str, any]:
        """
        Detect currency in text and convert to target currency
        Returns currency information with conversion
        """
        result = {
            'original_currency': None,
            'original_amount': None,
            'target_currency': target_currency,
            'converted_amount': None,
            'exchange_rate': None,
            'detection_confidence': 0.0
        }
        
        try:
            # Import the text parser to use its currency detection
            from services.text_parser import TextParser
            parser = TextParser()
            
            # Detect currency using the enhanced parser
            currency_info = parser.detect_currency(text)
            
            if currency_info['amount']:
                result['original_currency'] = currency_info['currency_code']
                result['original_amount'] = currency_info['amount']
                result['detection_confidence'] = 0.8  # High confidence from parser
                
                # Convert to target currency if different
                if currency_info['currency_code'] != target_currency:
                    converted = self.convert_currency(
                        currency_info['amount'],
                        currency_info['currency_code'],
                        target_currency
                    )
                    
                    if converted is not None:
                        result['converted_amount'] = converted
                        
                        # Calculate exchange rate
                        if currency_info['amount'] > 0:
                            result['exchange_rate'] = converted / currency_info['amount']
                else:
                    # Same currency, no conversion needed
                    result['converted_amount'] = currency_info['amount']
                    result['exchange_rate'] = 1.0
            
            return result
            
        except Exception as e:
            logger.error(f"Currency detection and conversion failed: {str(e)}")
            return result
    
    def get_supported_currencies(self) -> Dict[str, str]:
        """Get list of supported currencies with their names"""
        currency_names = {
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'JPY': 'Japanese Yen',
            'INR': 'Indian Rupee',
            'CAD': 'Canadian Dollar',
            'AUD': 'Australian Dollar',
            'CHF': 'Swiss Franc',
            'CNY': 'Chinese Yuan',
            'KRW': 'South Korean Won',
            'BRL': 'Brazilian Real',
            'MXN': 'Mexican Peso',
            'SEK': 'Swedish Krona',
            'NOK': 'Norwegian Krone',
            'DKK': 'Danish Krone',
            'PLN': 'Polish Zloty',
            'CZK': 'Czech Koruna',
            'HUF': 'Hungarian Forint',
            'RUB': 'Russian Ruble'
        }
        return currency_names
