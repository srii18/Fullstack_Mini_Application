from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models.database import Receipt
from datetime import datetime
import re

class SearchAlgorithms:
    """
    Implementation of various search algorithms for receipt data
    Includes linear search, hash-based indexing, and pattern matching
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._build_search_indexes()
    
    def _build_search_indexes(self):
        """Build hash-based indexes for optimized search performance"""
        # Vendor hash index
        self.vendor_index = {}
        # Category hash index  
        self.category_index = {}
        # Keyword hash index
        self.keyword_index = {}
        
        # Build indexes from existing data
        receipts = self.db.query(Receipt).all()
        for receipt in receipts:
            # Vendor index
            if receipt.vendor:
                vendor_key = receipt.vendor.lower()
                if vendor_key not in self.vendor_index:
                    self.vendor_index[vendor_key] = []
                self.vendor_index[vendor_key].append(receipt.id)
            
            # Category index
            if receipt.category:
                category_key = receipt.category.lower()
                if category_key not in self.category_index:
                    self.category_index[category_key] = []
                self.category_index[category_key].append(receipt.id)
            
            # Keyword index from raw text
            if receipt.raw_text:
                keywords = self._extract_keywords(receipt.raw_text)
                for keyword in keywords:
                    if keyword not in self.keyword_index:
                        self.keyword_index[keyword] = []
                    self.keyword_index[keyword].append(receipt.id)
    
    def linear_search(self, field: str, value: Any) -> List[Receipt]:
        """
        Linear search implementation - O(n) time complexity
        Useful for exact matches and when dataset is small
        """
        receipts = self.db.query(Receipt).all()
        results = []
        
        for receipt in receipts:
            if hasattr(receipt, field):
                receipt_value = getattr(receipt, field)
                if receipt_value and str(receipt_value).lower() == str(value).lower():
                    results.append(receipt)
        
        return results
    
    def hash_search(self, field: str, value: str) -> List[Receipt]:
        """
        Hash-based search using pre-built indexes - O(1) average time complexity
        Optimized for frequent searches on indexed fields
        """
        value_key = value.lower()
        receipt_ids = []
        
        if field == 'vendor' and value_key in self.vendor_index:
            receipt_ids = self.vendor_index[value_key]
        elif field == 'category' and value_key in self.category_index:
            receipt_ids = self.category_index[value_key]
        elif field == 'keyword' and value_key in self.keyword_index:
            receipt_ids = self.keyword_index[value_key]
        
        if receipt_ids:
            return self.db.query(Receipt).filter(Receipt.id.in_(receipt_ids)).all()
        
        return []
    
    def keyword_search(self, keyword: str) -> List[Receipt]:
        """
        Keyword search in vendor names and raw text
        Uses both hash index and SQL LIKE for comprehensive results
        """
        keyword_lower = keyword.lower()
        
        # First try hash index for exact keyword matches
        hash_results = self.hash_search('keyword', keyword_lower)
        
        # Then use SQL LIKE for partial matches
        sql_results = self.db.query(Receipt).filter(
            or_(
                Receipt.vendor.ilike(f'%{keyword}%'),
                Receipt.raw_text.ilike(f'%{keyword}%'),
                Receipt.category.ilike(f'%{keyword}%')
            )
        ).all()
        
        # Combine and deduplicate results
        all_results = hash_results + sql_results
        unique_results = list({receipt.id: receipt for receipt in all_results}.values())
        
        return unique_results
    
    def range_search(self, field: str, min_value: Any, max_value: Any) -> List[Receipt]:
        """
        Range-based search for numerical and date fields
        Optimized using database indexes
        """
        query = self.db.query(Receipt)
        
        if field == 'amount':
            query = query.filter(
                and_(Receipt.amount >= min_value, Receipt.amount <= max_value)
            )
        elif field == 'transaction_date':
            query = query.filter(
                and_(Receipt.transaction_date >= min_value, Receipt.transaction_date <= max_value)
            )
        elif field == 'upload_date':
            query = query.filter(
                and_(Receipt.upload_date >= min_value, Receipt.upload_date <= max_value)
            )
        
        return query.all()
    
    def pattern_search(self, field: str, pattern: str) -> List[Receipt]:
        """
        Pattern-based search using regular expressions
        Useful for complex text matching requirements
        """
        receipts = self.db.query(Receipt).all()
        results = []
        
        try:
            regex_pattern = re.compile(pattern, re.IGNORECASE)
            
            for receipt in receipts:
                if hasattr(receipt, field):
                    field_value = getattr(receipt, field)
                    if field_value and regex_pattern.search(str(field_value)):
                        results.append(receipt)
        
        except re.error:
            # Invalid regex pattern, fall back to simple string matching
            return self.keyword_search(pattern)
        
        return results
    
    def multi_criteria_search(self, filters: Dict[str, Any]) -> List[Receipt]:
        """
        Advanced search with multiple criteria
        Combines different search algorithms for optimal performance
        """
        query = self.db.query(Receipt)
        conditions = []
        
        # Vendor filter
        if filters.get('vendor'):
            conditions.append(Receipt.vendor.ilike(f"%{filters['vendor']}%"))
        
        # Category filter
        if filters.get('category'):
            conditions.append(Receipt.category.ilike(f"%{filters['category']}%"))
        
        # Amount range filter
        if filters.get('min_amount') is not None:
            conditions.append(Receipt.amount >= filters['min_amount'])
        if filters.get('max_amount') is not None:
            conditions.append(Receipt.amount <= filters['max_amount'])
        
        # Date range filter
        if filters.get('start_date'):
            conditions.append(Receipt.transaction_date >= filters['start_date'])
        if filters.get('end_date'):
            conditions.append(Receipt.transaction_date <= filters['end_date'])
        
        # Keyword search in text
        if filters.get('keyword'):
            keyword_condition = or_(
                Receipt.vendor.ilike(f"%{filters['keyword']}%"),
                Receipt.raw_text.ilike(f"%{filters['keyword']}%"),
                Receipt.category.ilike(f"%{filters['keyword']}%")
            )
            conditions.append(keyword_condition)
        
        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query.all()
    
    def fuzzy_search(self, field: str, value: str, threshold: float = 0.8) -> List[Receipt]:
        """
        Fuzzy string matching for approximate searches
        Uses Levenshtein distance for similarity scoring
        """
        receipts = self.db.query(Receipt).all()
        results = []
        
        for receipt in receipts:
            if hasattr(receipt, field):
                field_value = getattr(receipt, field)
                if field_value:
                    similarity = self._calculate_similarity(str(field_value).lower(), value.lower())
                    if similarity >= threshold:
                        results.append((receipt, similarity))
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return [receipt for receipt, _ in results]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using Levenshtein distance
        Returns similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple implementation of Levenshtein distance
        len1, len2 = len(str1), len(str2)
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
        
        # Create distance matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill the matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity score
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = 1.0 - (distance / max_len)
        
        return similarity
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for indexing"""
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
        return list(set(keywords))
    
    def refresh_indexes(self):
        """Refresh hash indexes when new data is added"""
        self._build_search_indexes()
