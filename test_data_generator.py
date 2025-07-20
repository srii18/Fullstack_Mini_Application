"""
Test data generator for the Receipt Processing Application
Creates sample receipt data for testing and demonstration
"""

import os
import random
from datetime import datetime, timedelta
from models.database import SessionLocal, Receipt, create_tables

# Sample data for generating test receipts
SAMPLE_VENDORS = [
    "Walmart", "Target", "Kroger", "Safeway", "Whole Foods", "Costco",
    "McDonald's", "Starbucks", "Subway", "Pizza Hut", "KFC",
    "Amazon", "Best Buy", "Home Depot", "Lowe's", "CVS Pharmacy",
    "Shell Gas Station", "Exxon", "BP", "Chevron",
    "Electric Company", "Gas Utility", "Water Department", "Internet Provider",
    "Verizon", "AT&T", "T-Mobile", "Comcast"
]

SAMPLE_CATEGORIES = {
    "Walmart": "grocery", "Target": "retail", "Kroger": "grocery", 
    "Safeway": "grocery", "Whole Foods": "grocery", "Costco": "grocery",
    "McDonald's": "dining", "Starbucks": "dining", "Subway": "dining", 
    "Pizza Hut": "dining", "KFC": "dining",
    "Amazon": "retail", "Best Buy": "retail", "Home Depot": "retail", 
    "Lowe's": "retail", "CVS Pharmacy": "healthcare",
    "Shell Gas Station": "transportation", "Exxon": "transportation", 
    "BP": "transportation", "Chevron": "transportation",
    "Electric Company": "utilities", "Gas Utility": "utilities", 
    "Water Department": "utilities", "Internet Provider": "utilities",
    "Verizon": "utilities", "AT&T": "utilities", "T-Mobile": "utilities", 
    "Comcast": "utilities"
}

SAMPLE_RECEIPT_TEXTS = {
    "grocery": [
        "GROCERY RECEIPT\n{vendor}\n{date}\nMilk $3.99\nBread $2.49\nEggs $4.29\nBananas $1.99\nTotal: ${amount}",
        "{vendor} SUPERMARKET\nDate: {date}\nApples 2lb $3.98\nChicken $8.99\nRice $2.99\nYogurt $4.49\nSUBTOTAL ${amount}",
        "FRESH MARKET\n{vendor}\n{date}\nVegetables $12.99\nFruit $8.49\nMeat $15.99\nDairy $6.99\nTOTAL: ${amount}"
    ],
    "dining": [
        "{vendor}\n{date}\nBig Mac Meal $8.99\nChicken McNuggets $5.99\nCoke $1.99\nTotal: ${amount}",
        "RESTAURANT RECEIPT\n{vendor}\n{date}\nBurger $12.99\nFries $4.99\nDrink $2.99\nTip $3.00\nTotal ${amount}",
        "{vendor} CAFE\nDate: {date}\nCoffee $4.99\nSandwich $7.99\nPastry $3.99\nTOTAL ${amount}"
    ],
    "retail": [
        "{vendor} STORE\n{date}\nElectronics $199.99\nAccessories $49.99\nWarranty $29.99\nTax $20.00\nTotal: ${amount}",
        "RETAIL RECEIPT\n{vendor}\n{date}\nClothing $79.99\nShoes $89.99\nBag $39.99\nSUBTOTAL ${amount}",
        "{vendor}\nPurchase Date: {date}\nHome Items $45.99\nTools $89.99\nSupplies $23.99\nTOTAL ${amount}"
    ],
    "utilities": [
        "{vendor}\nBILL DATE: {date}\nElectricity Usage: 850 kWh\nBase Charge: $15.00\nUsage Charge: $85.00\nTaxes: $8.50\nTOTAL AMOUNT DUE: ${amount}",
        "UTILITY BILL\n{vendor}\n{date}\nService Period: Monthly\nPrevious Balance: $0.00\nCurrent Charges: ${amount}\nDUE DATE: Next Month",
        "{vendor} SERVICES\nStatement Date: {date}\nInternet Service $59.99\nEquipment Rental $10.00\nTaxes $5.99\nTOTAL: ${amount}"
    ],
    "transportation": [
        "{vendor}\n{date}\nRegular Unleaded\nGallons: 12.5\nPrice/Gal: $3.45\nTotal: ${amount}",
        "GAS STATION RECEIPT\n{vendor}\nDate: {date}\nFuel Purchase\nAmount: ${amount}\nPayment: Credit Card",
        "{vendor} FUEL\n{date}\nPremium Gas\n15.2 Gallons\n$3.89/gal\nTOTAL ${amount}"
    ]
}

def generate_random_date(days_back=365):
    """Generate a random date within the last N days"""
    start_date = datetime.now() - timedelta(days=days_back)
    random_days = random.randint(0, days_back)
    return start_date + timedelta(days=random_days)

def generate_random_amount(category):
    """Generate realistic amounts based on category"""
    amount_ranges = {
        "grocery": (15.0, 150.0),
        "dining": (8.0, 75.0),
        "retail": (25.0, 500.0),
        "utilities": (45.0, 250.0),
        "transportation": (25.0, 80.0),
        "healthcare": (20.0, 300.0)
    }
    
    min_amt, max_amt = amount_ranges.get(category, (10.0, 100.0))
    return round(random.uniform(min_amt, max_amt), 2)

def generate_receipt_text(vendor, category, amount, date):
    """Generate realistic receipt text"""
    templates = SAMPLE_RECEIPT_TEXTS.get(category, SAMPLE_RECEIPT_TEXTS["retail"])
    template = random.choice(templates)
    
    return template.format(
        vendor=vendor,
        date=date.strftime("%m/%d/%Y"),
        amount=f"{amount:.2f}"
    )

def create_test_receipts(count=50):
    """Create test receipt data"""
    print(f"Creating {count} test receipts...")
    
    # Create database tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        for i in range(count):
            # Select random vendor and category
            vendor = random.choice(SAMPLE_VENDORS)
            category = SAMPLE_CATEGORIES.get(vendor, "other")
            
            # Generate random data
            transaction_date = generate_random_date()
            amount = generate_random_amount(category)
            
            # Generate receipt text
            raw_text = generate_receipt_text(vendor, category, amount, transaction_date)
            
            # Create receipt record
            receipt = Receipt(
                filename=f"test_receipt_{i+1:03d}.txt",
                file_type="txt",
                vendor=vendor,
                transaction_date=transaction_date,
                amount=amount,
                category=category,
                raw_text=raw_text,
                confidence_score=1.0,  # Perfect confidence for generated data
                processing_status="processed"
            )
            
            db.add(receipt)
            
            if (i + 1) % 10 == 0:
                print(f"Created {i + 1} receipts...")
        
        # Commit all changes
        db.commit()
        print(f"Successfully created {count} test receipts!")
        
        # Print summary
        print("\nTest Data Summary:")
        print(f"Total Receipts: {count}")
        
        # Count by category
        category_counts = {}
        for vendor in SAMPLE_VENDORS:
            category = SAMPLE_CATEGORIES.get(vendor, "other")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            print(f"{category.title()}: ~{count * count // len(SAMPLE_VENDORS)} receipts")
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

def clear_test_data():
    """Clear all test data from database"""
    print("Clearing all test data...")
    
    db = SessionLocal()
    try:
        # Delete all receipts
        deleted_count = db.query(Receipt).delete()
        db.commit()
        print(f"Deleted {deleted_count} receipts")
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_test_data()
        elif sys.argv[1] == "generate":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            create_test_receipts(count)
        else:
            print("Usage: python test_data_generator.py [generate|clear] [count]")
    else:
        # Default: create 30 test receipts
        create_test_receipts(30)
