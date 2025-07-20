from typing import List, Dict, Any, Optional
from models.database import Receipt
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics
import calendar

class AggregationAlgorithms:
    """
    Implementation of statistical aggregation functions for receipt data
    Includes sum, mean, median, mode, histograms, and time-series analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_basic_stats(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """
        Calculate basic statistical aggregates for receipt amounts
        Returns: sum, mean, median, mode, min, max, count
        """
        if not receipts:
            return self._empty_stats()
        
        # Extract amounts, filtering out None values
        amounts = [r.amount for r in receipts if r.amount is not None]
        
        if not amounts:
            return self._empty_stats()
        
        # Calculate statistics
        total_sum = sum(amounts)
        count = len(amounts)
        mean = total_sum / count
        
        # Sort for median calculation
        sorted_amounts = sorted(amounts)
        median = statistics.median(sorted_amounts)
        
        # Mode calculation
        mode_result = self._calculate_mode(amounts)
        
        return {
            'total_receipts': len(receipts),
            'receipts_with_amounts': count,
            'total_amount': round(total_sum, 2),
            'average_amount': round(mean, 2),
            'median_amount': round(median, 2),
            'mode_amount': mode_result,
            'min_amount': round(min(amounts), 2),
            'max_amount': round(max(amounts), 2),
            'amount_range': round(max(amounts) - min(amounts), 2),
            'standard_deviation': round(statistics.stdev(amounts) if count > 1 else 0, 2)
        }
    
    def _calculate_mode(self, amounts: List[float]) -> Dict[str, Any]:
        """Calculate mode with frequency information"""
        if not amounts:
            return {'value': None, 'frequency': 0}
        
        # Round amounts to 2 decimal places for mode calculation
        rounded_amounts = [round(amount, 2) for amount in amounts]
        counter = Counter(rounded_amounts)
        
        # Find the most common value(s)
        max_frequency = max(counter.values())
        modes = [amount for amount, freq in counter.items() if freq == max_frequency]
        
        return {
            'value': modes[0] if len(modes) == 1 else modes,
            'frequency': max_frequency,
            'is_multimodal': len(modes) > 1
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure"""
        return {
            'total_receipts': 0,
            'receipts_with_amounts': 0,
            'total_amount': 0.0,
            'average_amount': 0.0,
            'median_amount': 0.0,
            'mode_amount': {'value': None, 'frequency': 0},
            'min_amount': 0.0,
            'max_amount': 0.0,
            'amount_range': 0.0,
            'standard_deviation': 0.0
        }
    
    def vendor_frequency_distribution(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """
        Calculate frequency distribution of vendors (histogram)
        Returns sorted list of vendors with counts and percentages
        """
        if not receipts:
            return []
        
        # Count vendor occurrences
        vendor_counts = Counter()
        total_receipts = len(receipts)
        
        for receipt in receipts:
            vendor = receipt.vendor or 'Unknown'
            vendor_counts[vendor] += 1
        
        # Convert to list with percentages
        distribution = []
        for vendor, count in vendor_counts.most_common():
            percentage = (count / total_receipts) * 100
            distribution.append({
                'vendor': vendor,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return distribution
    
    def category_frequency_distribution(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """
        Calculate frequency distribution of categories
        Returns sorted list of categories with counts and percentages
        """
        if not receipts:
            return []
        
        # Count category occurrences
        category_counts = Counter()
        total_receipts = len(receipts)
        
        for receipt in receipts:
            category = receipt.category or 'Uncategorized'
            category_counts[category] += 1
        
        # Convert to list with percentages
        distribution = []
        for category, count in category_counts.most_common():
            percentage = (count / total_receipts) * 100
            distribution.append({
                'category': category,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return distribution
    
    def top_vendors_by_amount(self, receipts: List[Receipt], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top vendors by total spending amount
        Returns list of vendors with total amounts and transaction counts
        """
        if not receipts:
            return []
        
        # Aggregate by vendor
        vendor_totals = defaultdict(lambda: {'total': 0.0, 'count': 0})
        
        for receipt in receipts:
            vendor = receipt.vendor or 'Unknown'
            amount = receipt.amount or 0.0
            
            vendor_totals[vendor]['total'] += amount
            vendor_totals[vendor]['count'] += 1
        
        # Convert to sorted list
        top_vendors = []
        for vendor, data in vendor_totals.items():
            avg_amount = data['total'] / data['count'] if data['count'] > 0 else 0
            top_vendors.append({
                'vendor': vendor,
                'total_amount': round(data['total'], 2),
                'transaction_count': data['count'],
                'average_amount': round(avg_amount, 2)
            })
        
        # Sort by total amount (descending) and limit results
        top_vendors.sort(key=lambda x: x['total_amount'], reverse=True)
        return top_vendors[:limit]
    
    def monthly_spending_trends(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """
        Calculate monthly spending trends using time-series aggregation
        Returns list of monthly totals with moving averages
        """
        if not receipts:
            return []
        
        # Group receipts by month
        monthly_data = defaultdict(lambda: {'total': 0.0, 'count': 0})
        
        for receipt in receipts:
            if receipt.transaction_date and receipt.amount:
                # Use transaction_date, fallback to upload_date
                date = receipt.transaction_date
                month_key = f"{date.year}-{date.month:02d}"
                
                monthly_data[month_key]['total'] += receipt.amount
                monthly_data[month_key]['count'] += 1
        
        # Convert to sorted list
        trends = []
        for month_key, data in sorted(monthly_data.items()):
            year, month = map(int, month_key.split('-'))
            month_name = calendar.month_name[month]
            
            trends.append({
                'month': month_key,
                'month_name': f"{month_name} {year}",
                'total_amount': round(data['total'], 2),
                'transaction_count': data['count'],
                'average_amount': round(data['total'] / data['count'], 2)
            })
        
        # Add moving averages
        self._add_moving_averages(trends)
        
        return trends
    
    def _add_moving_averages(self, trends: List[Dict[str, Any]], window: int = 3):
        """Add moving averages to time series data"""
        if len(trends) < window:
            return
        
        for i in range(len(trends)):
            # Calculate moving average for current position
            start_idx = max(0, i - window + 1)
            end_idx = i + 1
            
            window_data = trends[start_idx:end_idx]
            if len(window_data) >= 2:  # Need at least 2 points for moving average
                avg_total = sum(item['total_amount'] for item in window_data) / len(window_data)
                avg_count = sum(item['transaction_count'] for item in window_data) / len(window_data)
                
                trends[i]['moving_avg_amount'] = round(avg_total, 2)
                trends[i]['moving_avg_count'] = round(avg_count, 1)
            else:
                trends[i]['moving_avg_amount'] = trends[i]['total_amount']
                trends[i]['moving_avg_count'] = trends[i]['transaction_count']
    
    def spending_by_day_of_week(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """
        Analyze spending patterns by day of the week
        Returns spending totals and averages for each day
        """
        if not receipts:
            return []
        
        # Group by day of week (0=Monday, 6=Sunday)
        daily_data = defaultdict(lambda: {'total': 0.0, 'count': 0})
        
        for receipt in receipts:
            if receipt.transaction_date and receipt.amount:
                day_of_week = receipt.transaction_date.weekday()
                daily_data[day_of_week]['total'] += receipt.amount
                daily_data[day_of_week]['count'] += 1
        
        # Convert to list with day names
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_spending = []
        
        for day_num in range(7):
            data = daily_data[day_num]
            avg_amount = data['total'] / data['count'] if data['count'] > 0 else 0
            
            daily_spending.append({
                'day_of_week': day_names[day_num],
                'day_number': day_num,
                'total_amount': round(data['total'], 2),
                'transaction_count': data['count'],
                'average_amount': round(avg_amount, 2)
            })
        
        return daily_spending
    
    def amount_distribution_histogram(self, receipts: List[Receipt], bins: int = 10) -> List[Dict[str, Any]]:
        """
        Create histogram of amount distribution
        Returns binned data showing spending patterns
        """
        if not receipts:
            return []
        
        amounts = [r.amount for r in receipts if r.amount is not None]
        if not amounts:
            return []
        
        # Calculate bin boundaries
        min_amount = min(amounts)
        max_amount = max(amounts)
        bin_width = (max_amount - min_amount) / bins
        
        # Create bins
        histogram = []
        for i in range(bins):
            bin_start = min_amount + (i * bin_width)
            bin_end = bin_start + bin_width
            
            # Count amounts in this bin
            count = sum(1 for amount in amounts if bin_start <= amount < bin_end)
            
            # Handle the last bin to include max_amount
            if i == bins - 1:
                count = sum(1 for amount in amounts if bin_start <= amount <= bin_end)
            
            percentage = (count / len(amounts)) * 100 if amounts else 0
            
            histogram.append({
                'bin_start': round(bin_start, 2),
                'bin_end': round(bin_end, 2),
                'bin_center': round(bin_start + bin_width/2, 2),
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return histogram
    
    def quarterly_analysis(self, receipts: List[Receipt]) -> List[Dict[str, Any]]:
        """
        Analyze spending by quarters
        Returns quarterly aggregations with year-over-year comparisons
        """
        if not receipts:
            return []
        
        # Group by quarter
        quarterly_data = defaultdict(lambda: {'total': 0.0, 'count': 0})
        
        for receipt in receipts:
            if receipt.transaction_date and receipt.amount:
                date = receipt.transaction_date
                quarter = (date.month - 1) // 3 + 1
                quarter_key = f"{date.year}-Q{quarter}"
                
                quarterly_data[quarter_key]['total'] += receipt.amount
                quarterly_data[quarter_key]['count'] += 1
        
        # Convert to sorted list
        quarterly_analysis = []
        for quarter_key, data in sorted(quarterly_data.items()):
            year, quarter = quarter_key.split('-')
            
            quarterly_analysis.append({
                'quarter': quarter_key,
                'year': int(year),
                'quarter_number': int(quarter[1]),
                'total_amount': round(data['total'], 2),
                'transaction_count': data['count'],
                'average_amount': round(data['total'] / data['count'], 2)
            })
        
        # Add year-over-year growth rates
        self._add_yoy_growth(quarterly_analysis)
        
        return quarterly_analysis
    
    def _add_yoy_growth(self, quarterly_data: List[Dict[str, Any]]):
        """Add year-over-year growth rates to quarterly data"""
        # Group by quarter number for YoY comparison
        by_quarter = defaultdict(list)
        for item in quarterly_data:
            by_quarter[item['quarter_number']].append(item)
        
        # Calculate YoY growth for each quarter
        for quarter_num, quarters in by_quarter.items():
            quarters.sort(key=lambda x: x['year'])
            
            for i in range(1, len(quarters)):
                current = quarters[i]
                previous = quarters[i-1]
                
                if previous['total_amount'] > 0:
                    growth_rate = ((current['total_amount'] - previous['total_amount']) / previous['total_amount']) * 100
                    current['yoy_growth_rate'] = round(growth_rate, 2)
                else:
                    current['yoy_growth_rate'] = None
    
    def comprehensive_analysis(self, receipts: List[Receipt]) -> Dict[str, Any]:
        """
        Generate comprehensive analysis combining all aggregation functions
        Returns complete statistical overview
        """
        return {
            'basic_statistics': self.calculate_basic_stats(receipts),
            'vendor_distribution': self.vendor_frequency_distribution(receipts),
            'category_distribution': self.category_frequency_distribution(receipts),
            'top_vendors': self.top_vendors_by_amount(receipts),
            'monthly_trends': self.monthly_spending_trends(receipts),
            'daily_patterns': self.spending_by_day_of_week(receipts),
            'amount_histogram': self.amount_distribution_histogram(receipts),
            'quarterly_analysis': self.quarterly_analysis(receipts)
        }
