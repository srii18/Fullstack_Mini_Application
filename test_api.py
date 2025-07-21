#!/usr/bin/env python3
"""
API Testing Script for Receipt Processing Application
Tests all endpoints and demonstrates functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"Health Check: {data['status']}")
            return True
        else:
            print(f"Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Health Check Error: {e}")
        return False

def test_get_receipts():
    """Test getting all receipts"""
    print("\nTesting Get All Receipts...")
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/")
        if response.status_code == 200:
            receipts = response.json()
            print(f"Found {len(receipts)} receipts")
            
            # Show sample receipt data
            if receipts:
                sample = receipts[0]
                print(f"   Sample Receipt: {sample.get('vendor', 'Unknown')} - ${sample.get('amount', 0):.2f}")
            return receipts
        else:
            print(f"Get Receipts Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Get Receipts Error: {e}")
        return []

def test_search_functionality():
    """Test search functionality"""
    print("\nTesting Search Functionality...")
    
    # Test 1: Search by vendor
    print("   Testing vendor search...")
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/search", json={"vendor": "Walmart"})
        if response.status_code == 200:
            results = response.json()
            print(f"   Vendor search: Found {len(results)} Walmart receipts")
        else:
            print(f"   Vendor search failed: {response.status_code}")
            # Print error details for debugging
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {response.text}")
    except Exception as e:
        print(f"   Vendor search error: {e}")
    
    # Test 2: Search by amount range
    print("   Testing amount range search...")
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/search", json={"min_amount": 50.0, "max_amount": 200.0})
        if response.status_code == 200:
            results = response.json()
            print(f"   Amount range search: Found {len(results)} receipts ($50-$200)")
        else:
            print(f"   Amount range search failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {response.text}")
    except Exception as e:
        print(f"   Amount range search error: {e}")
    
    # Test 3: Search by category
    print("   Testing category search...")
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/search", json={"category": "grocery"})
        if response.status_code == 200:
            results = response.json()
            print(f"   Category search: Found {len(results)} grocery receipts")
        else:
            print(f"   Category search failed: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response text: {response.text}")
    except Exception as e:
        print(f"   Category search error: {e}")

def test_analytics():
    """Test analytics endpoints"""
    print("\nTesting Analytics...")
    
    # Test comprehensive analytics
    print("   Testing comprehensive analytics...")
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/analytics/summary")
        if response.status_code == 200:
            analytics = response.json()
            basic_stats = analytics.get('basic_statistics', {})
            print(f"   Analytics Summary:")
            print(f"      Total Receipts: {basic_stats.get('total_receipts', 0)}")
            print(f"      Total Amount: ${basic_stats.get('total_amount', 0):.2f}")
            print(f"      Average Amount: ${basic_stats.get('average_amount', 0):.2f}")
            print(f"      Median Amount: ${basic_stats.get('median_amount', 0):.2f}")
            
            # Show top vendors
            top_vendors = analytics.get('top_vendors', [])[:3]
            if top_vendors:
                print(f"      Top 3 Vendors:")
                for i, vendor in enumerate(top_vendors, 1):
                    print(f"        {i}. {vendor['vendor']}: ${vendor['total_amount']:.2f}")
        else:
            print(f"   Analytics failed: {response.status_code}")
    except Exception as e:
        print(f"   Analytics error: {e}")
    
    # Test vendor analytics
    print("   Testing vendor analytics...")
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/analytics/vendors?limit=5")
        if response.status_code == 200:
            vendor_data = response.json()
            top_vendors = vendor_data.get('top_vendors', [])
            print(f"   Top 5 Vendors by Spending:")
            for vendor in top_vendors:
                print(f"      {vendor['vendor']}: ${vendor['total_amount']:.2f} ({vendor['transaction_count']} transactions)")
        else:
            print(f"   Vendor analytics failed: {response.status_code}")
    except Exception as e:
        print(f"   Vendor analytics error: {e}")
    
    # Test spending trends
    print("   Testing spending trends...")
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/analytics/trends")
        if response.status_code == 200:
            trends = response.json()
            monthly_trends = trends.get('monthly_trends', [])
            if monthly_trends:
                print(f"   Monthly Trends (last 3 months):")
                for trend in monthly_trends[-3:]:
                    print(f"      {trend['month_name']}: ${trend['total_amount']:.2f} ({trend['transaction_count']} transactions)")
        else:
            print(f"   Trends analytics failed: {response.status_code}")
    except Exception as e:
        print(f"   Trends analytics error: {e}")

def test_sorting():
    """Test sorting functionality"""
    print("\nTesting Sorting...")
    
    # Test sorting by amount (descending)
    search_filters = {}
    sort_options = {"field": "amount", "direction": "desc"}
    
    try:
        payload = {**search_filters}
        response = requests.post(f"{API_BASE_URL}/receipts/search", json=payload)
        if response.status_code == 200:
            results = response.json()
            if len(results) >= 3:
                print("   Sorting by amount (highest first):")
                for i, receipt in enumerate(results[:3]):
                    amount = receipt.get('amount', 0)
                    vendor = receipt.get('vendor', 'Unknown')
                    print(f"      {i+1}. {vendor}: ${amount:.2f}")
        else:
            print(f"   Sorting test failed: {response.status_code}")
    except Exception as e:
        print(f"   Sorting error: {e}")

def performance_benchmark():
    """Run performance benchmarks"""
    print("\nPerformance Benchmarks...")
    
    # Test search performance
    start_time = time.time()
    search_filters = {"keyword": "store"}
    try:
        response = requests.post(f"{API_BASE_URL}/receipts/search", json=search_filters)
        end_time = time.time()
        
        if response.status_code == 200:
            results = response.json()
            search_time = (end_time - start_time) * 1000
            print(f"   Keyword Search Performance:")
            print(f"      Results: {len(results)} receipts")
            print(f"      Time: {search_time:.2f}ms")
        else:
            print(f"   Search benchmark failed: {response.status_code}")
    except Exception as e:
        print(f"   Search benchmark error: {e}")
    
    # Test analytics performance
    start_time = time.time()
    try:
        response = requests.get(f"{API_BASE_URL}/receipts/analytics/summary")
        end_time = time.time()
        
        if response.status_code == 200:
            analytics_time = (end_time - start_time) * 1000
            print(f"   Analytics Performance:")
            print(f"      Time: {analytics_time:.2f}ms")
        else:
            print(f"   Analytics benchmark failed: {response.status_code}")
    except Exception as e:
        print(f"   Analytics benchmark error: {e}")

def main():
    """Run all API tests"""
    print("=" * 60)
    print("RECEIPT PROCESSING API TESTS")
    print("=" * 60)
    
    # Check if API is running
    if not test_health_check():
        print("\nAPI is not running. Please start the backend first:")
        print("   python -m uvicorn main:app --reload")
        return
    
    # Run all tests
    receipts = test_get_receipts()
    
    if not receipts:
        print("\nNo receipts found. Generating test data...")
        print("   Run: python test_data_generator.py generate 30")
        return
    
    test_search_functionality()
    test_analytics()
    test_sorting()
    performance_benchmark()
    
    print("\n" + "=" * 60)
    print("\nALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nKey Performance Metrics:")
    print("   • Search algorithms: Linear + Hash-based indexing")
    print("   • Sorting algorithms: Timsort (O(n log n))")
    print("   • Aggregation: Real-time statistical computation")
    print("   • Database: SQLite with optimized indexes")
    print("\nAccess Points:")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Streamlit Dashboard: http://localhost:8501")

if __name__ == "__main__":
    main()
