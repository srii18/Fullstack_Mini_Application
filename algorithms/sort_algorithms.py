from typing import List, Callable, Any
from models.database import Receipt
from datetime import datetime
import time

class SortAlgorithms:
    """
    Implementation of various sorting algorithms for receipt data
    Includes quicksort, mergesort, and Timsort with time complexity analysis
    """
    
    def __init__(self):
        self.comparison_count = 0
        self.swap_count = 0
    
    def reset_counters(self):
        """Reset performance counters"""
        self.comparison_count = 0
        self.swap_count = 0
    
    def quicksort(self, receipts: List[Receipt], key_func: Callable, reverse: bool = False) -> List[Receipt]:
        """
        Quicksort implementation - Average O(n log n), Worst O(n²)
        Good for general-purpose sorting with random data
        """
        self.reset_counters()
        start_time = time.time()
        
        result = self._quicksort_recursive(receipts.copy(), key_func, reverse, 0, len(receipts) - 1)
        
        end_time = time.time()
        self._log_performance("Quicksort", len(receipts), end_time - start_time)
        
        return result
    
    def _quicksort_recursive(self, arr: List[Receipt], key_func: Callable, reverse: bool, low: int, high: int) -> List[Receipt]:
        """Recursive quicksort implementation"""
        if low < high:
            # Partition the array
            pivot_index = self._partition(arr, key_func, reverse, low, high)
            
            # Recursively sort elements before and after partition
            self._quicksort_recursive(arr, key_func, reverse, low, pivot_index - 1)
            self._quicksort_recursive(arr, key_func, reverse, pivot_index + 1, high)
        
        return arr
    
    def _partition(self, arr: List[Receipt], key_func: Callable, reverse: bool, low: int, high: int) -> int:
        """Partition function for quicksort"""
        # Choose rightmost element as pivot
        pivot = key_func(arr[high])
        i = low - 1  # Index of smaller element
        
        for j in range(low, high):
            self.comparison_count += 1
            
            # Compare based on sort direction
            should_swap = (key_func(arr[j]) <= pivot) if not reverse else (key_func(arr[j]) >= pivot)
            
            if should_swap:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                self.swap_count += 1
        
        # Place pivot in correct position
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        self.swap_count += 1
        
        return i + 1
    
    def mergesort(self, receipts: List[Receipt], key_func: Callable, reverse: bool = False) -> List[Receipt]:
        """
        Mergesort implementation - Guaranteed O(n log n)
        Stable sort, good for large datasets and when stability is required
        """
        self.reset_counters()
        start_time = time.time()
        
        result = self._mergesort_recursive(receipts.copy(), key_func, reverse)
        
        end_time = time.time()
        self._log_performance("Mergesort", len(receipts), end_time - start_time)
        
        return result
    
    def _mergesort_recursive(self, arr: List[Receipt], key_func: Callable, reverse: bool) -> List[Receipt]:
        """Recursive mergesort implementation"""
        if len(arr) <= 1:
            return arr
        
        # Divide the array
        mid = len(arr) // 2
        left = self._mergesort_recursive(arr[:mid], key_func, reverse)
        right = self._mergesort_recursive(arr[mid:], key_func, reverse)
        
        # Merge the sorted halves
        return self._merge(left, right, key_func, reverse)
    
    def _merge(self, left: List[Receipt], right: List[Receipt], key_func: Callable, reverse: bool) -> List[Receipt]:
        """Merge function for mergesort"""
        result = []
        i = j = 0
        
        # Merge the two arrays
        while i < len(left) and j < len(right):
            self.comparison_count += 1
            
            left_val = key_func(left[i])
            right_val = key_func(right[j])
            
            should_take_left = (left_val <= right_val) if not reverse else (left_val >= right_val)
            
            if should_take_left:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        # Add remaining elements
        result.extend(left[i:])
        result.extend(right[j:])
        
        return result
    
    def timsort(self, receipts: List[Receipt], key_func: Callable, reverse: bool = False) -> List[Receipt]:
        """
        Python's built-in Timsort - Adaptive O(n) to O(n log n)
        Optimized for real-world data with existing order
        """
        self.reset_counters()
        start_time = time.time()
        
        # Use Python's built-in sorted() which implements Timsort
        result = sorted(receipts, key=key_func, reverse=reverse)
        
        end_time = time.time()
        self._log_performance("Timsort", len(receipts), end_time - start_time)
        
        return result
    
    def sort_by_amount(self, receipts: List[Receipt], reverse: bool = False, algorithm: str = "timsort") -> List[Receipt]:
        """Sort receipts by amount using specified algorithm"""
        key_func = lambda r: r.amount if r.amount is not None else 0
        
        if algorithm == "quicksort":
            return self.quicksort(receipts, key_func, reverse)
        elif algorithm == "mergesort":
            return self.mergesort(receipts, key_func, reverse)
        else:  # Default to timsort
            return self.timsort(receipts, key_func, reverse)
    
    def sort_by_date(self, receipts: List[Receipt], field: str = "transaction_date", reverse: bool = False, algorithm: str = "timsort") -> List[Receipt]:
        """Sort receipts by date field using specified algorithm"""
        def key_func(r):
            date_val = getattr(r, field)
            return date_val if date_val is not None else datetime.min
        
        if algorithm == "quicksort":
            return self.quicksort(receipts, key_func, reverse)
        elif algorithm == "mergesort":
            return self.mergesort(receipts, key_func, reverse)
        else:  # Default to timsort
            return self.timsort(receipts, key_func, reverse)
    
    def sort_by_vendor(self, receipts: List[Receipt], reverse: bool = False, algorithm: str = "timsort") -> List[Receipt]:
        """Sort receipts by vendor name using specified algorithm"""
        key_func = lambda r: (r.vendor or "").lower()
        
        if algorithm == "quicksort":
            return self.quicksort(receipts, key_func, reverse)
        elif algorithm == "mergesort":
            return self.mergesort(receipts, key_func, reverse)
        else:  # Default to timsort
            return self.timsort(receipts, key_func, reverse)
    
    def sort_by_category(self, receipts: List[Receipt], reverse: bool = False, algorithm: str = "timsort") -> List[Receipt]:
        """Sort receipts by category using specified algorithm"""
        key_func = lambda r: (r.category or "").lower()
        
        if algorithm == "quicksort":
            return self.quicksort(receipts, key_func, reverse)
        elif algorithm == "mergesort":
            return self.mergesort(receipts, key_func, reverse)
        else:  # Default to timsort
            return self.timsort(receipts, key_func, reverse)
    
    def multi_level_sort(self, receipts: List[Receipt], sort_criteria: List[dict]) -> List[Receipt]:
        """
        Multi-level sorting with multiple criteria
        sort_criteria: [{"field": "amount", "reverse": False}, {"field": "date", "reverse": True}]
        """
        result = receipts.copy()
        
        # Sort in reverse order of criteria (last criterion first)
        for criteria in reversed(sort_criteria):
            field = criteria["field"]
            reverse = criteria.get("reverse", False)
            
            if field == "amount":
                result = self.sort_by_amount(result, reverse)
            elif field in ["transaction_date", "upload_date"]:
                result = self.sort_by_date(result, field, reverse)
            elif field == "vendor":
                result = self.sort_by_vendor(result, reverse)
            elif field == "category":
                result = self.sort_by_category(result, reverse)
        
        return result
    
    def benchmark_algorithms(self, receipts: List[Receipt], key_func: Callable) -> dict:
        """
        Benchmark different sorting algorithms
        Returns performance metrics for comparison
        """
        if len(receipts) == 0:
            return {}
        
        results = {}
        
        # Test each algorithm
        algorithms = ["timsort", "quicksort", "mergesort"]
        
        for algo in algorithms:
            try:
                if algo == "timsort":
                    sorted_receipts = self.timsort(receipts, key_func)
                elif algo == "quicksort":
                    sorted_receipts = self.quicksort(receipts, key_func)
                elif algo == "mergesort":
                    sorted_receipts = self.mergesort(receipts, key_func)
                
                results[algo] = {
                    "comparisons": self.comparison_count,
                    "swaps": self.swap_count,
                    "success": True
                }
            except Exception as e:
                results[algo] = {
                    "error": str(e),
                    "success": False
                }
        
        return results
    
    def _log_performance(self, algorithm: str, size: int, time_taken: float):
        """Log performance metrics"""
        print(f"\n{algorithm} Performance:")
        print(f"  Dataset size: {size}")
        print(f"  Time taken: {time_taken:.4f} seconds")
        print(f"  Comparisons: {self.comparison_count}")
        print(f"  Swaps: {self.swap_count}")
        
        # Calculate theoretical complexity
        import math
        if size > 0:
            n_log_n = size * math.log2(size)
            print(f"  Theoretical O(n log n): {n_log_n:.0f}")
            print(f"  Actual/Theoretical ratio: {self.comparison_count/n_log_n:.2f}")
    
    def is_sorted(self, receipts: List[Receipt], key_func: Callable, reverse: bool = False) -> bool:
        """Check if receipts are already sorted"""
        if len(receipts) <= 1:
            return True
        
        for i in range(1, len(receipts)):
            val1 = key_func(receipts[i-1])
            val2 = key_func(receipts[i])
            
            if reverse:
                if val1 < val2:
                    return False
            else:
                if val1 > val2:
                    return False
        
        return True
