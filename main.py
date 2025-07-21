from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
import logging
import json
import csv
import io

# Import our modules
from models.database import get_db, create_tables, Receipt
from schemas.receipt_schemas import (
    ReceiptResponse, ReceiptCreate, ReceiptUpdate, 
    SearchFilters, SortOptions, AggregationResponse,
    ManualCorrectionRequest, ExportRequest, CurrencyInfo
)
from services.ocr_service import OCRService
from services.text_parser import TextParser
from services.currency_service import CurrencyService
from algorithms.search_algorithms import SearchAlgorithms
from algorithms.sort_algorithms import SortAlgorithms
from algorithms.aggregation_algorithms import AggregationAlgorithms

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and services on startup"""
    create_tables()
    logger.info("Application started successfully")
    yield
    logger.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="Receipt Processing API",
    description="A full-stack application for processing receipts and bills with OCR and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize services
ocr_service = OCRService()
text_parser = TextParser()
currency_service = CurrencyService()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Receipt Processing API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/receipts/upload",
            "list": "/receipts/",
            "search": "/receipts/search",
            "analytics": "/receipts/analytics"
        }
    }

@app.post("/receipts/upload", response_model=ReceiptResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a receipt file
    Supports .jpg, .png, .pdf, .txt formats
    """
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower()
        supported_types = ['jpg', 'jpeg', 'png', 'pdf', 'txt']
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(supported_types)}"
            )
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {file.filename}")
        
        # Extract text using OCR service
        raw_text, confidence_score = ocr_service.extract_text(file_path, file_extension)
        
        # Parse structured data
        parsed_data = text_parser.parse_receipt_data(raw_text)
        
        # Create receipt record
        receipt_data = ReceiptCreate(
            filename=file.filename,
            file_type=file_extension,
            raw_text=raw_text,
            confidence_score=confidence_score,
            vendor=parsed_data.get('vendor'),
            transaction_date=parsed_data.get('transaction_date'),
            amount=parsed_data.get('amount'),
            category=parsed_data.get('category')
        )
        
        # Save to database
        db_receipt = Receipt(
            filename=receipt_data.filename,
            file_type=receipt_data.file_type,
            raw_text=receipt_data.raw_text,
            confidence_score=receipt_data.confidence_score,
            vendor=receipt_data.vendor,
            transaction_date=receipt_data.transaction_date,
            amount=receipt_data.amount,
            category=receipt_data.category,
            processing_status="processed"
        )
        
        db.add(db_receipt)
        db.commit()
        db.refresh(db_receipt)
        
        logger.info(f"Receipt processed successfully: ID {db_receipt.id}")
        
        return db_receipt
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        
        # Save failed record
        try:
            failed_receipt = Receipt(
                filename=file.filename,
                file_type=file_extension,
                processing_status="failed",
                error_message=str(e)
            )
            db.add(failed_receipt)
            db.commit()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/receipts/", response_model=List[ReceiptResponse])
async def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get list of all receipts with pagination"""
    receipts = db.query(Receipt).offset(skip).limit(limit).all()
    return receipts

@app.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Get specific receipt by ID"""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

@app.put("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: int,
    receipt_update: ReceiptUpdate,
    db: Session = Depends(get_db)
):
    """Update receipt data"""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Update fields
    for field, value in receipt_update.dict(exclude_unset=True).items():
        setattr(receipt, field, value)
    
    db.commit()
    db.refresh(receipt)
    return receipt

@app.post("/receipts/{receipt_id}/correct")
async def manual_correction(
    receipt_id: int,
    correction: ManualCorrectionRequest,
    db: Session = Depends(get_db)
):
    """Apply manual corrections to receipt fields"""
    try:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Apply corrections
        if correction.vendor is not None:
            receipt.vendor = correction.vendor
        if correction.transaction_date is not None:
            receipt.transaction_date = correction.transaction_date
        if correction.amount is not None:
            receipt.amount = correction.amount
        if correction.category is not None:
            receipt.category = correction.category
        
        # Add correction notes to error_message field for tracking
        if correction.notes:
            receipt.error_message = f"Manual correction: {correction.notes}"
        
        # Mark as manually corrected
        receipt.processing_status = "processed"
        
        db.commit()
        db.refresh(receipt)
        
        logger.info(f"Manual correction applied to receipt {receipt_id}")
        return ReceiptResponse.from_orm(receipt)
        
    except Exception as e:
        logger.error(f"Manual correction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Manual correction failed: {str(e)}")

@app.delete("/receipts/{receipt_id}")
async def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Delete receipt"""
    try:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Delete file if it exists
        if receipt.filename and os.path.exists(os.path.join(UPLOAD_DIR, receipt.filename)):
            os.remove(os.path.join(UPLOAD_DIR, receipt.filename))
        
        db.delete(receipt)
        db.commit()
        
        logger.info(f"Receipt {receipt_id} deleted successfully")
        return {"message": "Receipt deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.post("/receipts/search", response_model=List[ReceiptResponse])
async def search_receipts(
    filters: SearchFilters,
    sort: Optional[SortOptions] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Advanced search with multiple criteria and sorting
    Demonstrates various search algorithms
    """
    try:
        # Initialize search algorithms
        search_algo = SearchAlgorithms(db)
        
        # Convert filters to dict for multi-criteria search
        filter_dict = filters.dict(exclude_unset=True)
        
        # Perform search
        results = search_algo.multi_criteria_search(filter_dict)
        
        # Apply sorting if specified
        if sort:
            sort_algo = SortAlgorithms()
            
            if sort.field == "amount":
                results = sort_algo.sort_by_amount(results, sort.direction == "desc")
            elif sort.field in ["transaction_date", "upload_date"]:
                results = sort_algo.sort_by_date(results, sort.field, sort.direction == "desc")
            elif sort.field == "vendor":
                results = sort_algo.sort_by_vendor(results, sort.direction == "desc")
            elif sort.field == "category":
                results = sort_algo.sort_by_category(results, sort.direction == "desc")
        
        # Apply pagination
        paginated_results = results[skip:skip + limit]
        
        logger.info(f"Search completed: {len(results)} results found")
        return paginated_results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/receipts/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive analytics summary
    Demonstrates aggregation algorithms
    """
    try:
        # Get all receipts
        receipts = db.query(Receipt).filter(Receipt.processing_status == "processed").all()
        
        # Initialize aggregation algorithms
        agg_algo = AggregationAlgorithms(db)
        
        # Generate comprehensive analysis
        analysis = agg_algo.comprehensive_analysis(receipts)
        
        logger.info("Analytics summary generated successfully")
        return analysis
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@app.get("/receipts/analytics/vendors")
async def get_vendor_analytics(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top vendors by spending"""
    receipts = db.query(Receipt).filter(Receipt.processing_status == "processed").all()
    agg_algo = AggregationAlgorithms(db)
    
    return {
        "top_vendors": agg_algo.top_vendors_by_amount(receipts, limit),
        "vendor_distribution": agg_algo.vendor_frequency_distribution(receipts)
    }

@app.get("/receipts/analytics/trends")
async def get_spending_trends(db: Session = Depends(get_db)):
    """Get spending trends and patterns"""
    receipts = db.query(Receipt).filter(Receipt.processing_status == "processed").all()
    agg_algo = AggregationAlgorithms(db)
    
    return {
        "monthly_trends": agg_algo.monthly_spending_trends(receipts),
        "daily_patterns": agg_algo.spending_by_day_of_week(receipts),
        "quarterly_analysis": agg_algo.quarterly_analysis(receipts)
    }

@app.get("/receipts/analytics/categories")
async def get_category_analytics(db: Session = Depends(get_db)):
    """Get category-based analytics"""
    receipts = db.query(Receipt).filter(Receipt.processing_status == "processed").all()
    agg_algo = AggregationAlgorithms(db)
    
    return {
        "category_distribution": agg_algo.category_frequency_distribution(receipts),
        "amount_histogram": agg_algo.amount_distribution_histogram(receipts)
    }

@app.post("/receipts/export")
async def export_receipts(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export receipts as CSV or JSON"""
    try:
        # Get receipts based on filters
        query = db.query(Receipt).filter(Receipt.processing_status == "processed")
        
        if export_request.filters:
            filters = export_request.filters
            if filters.vendor:
                query = query.filter(Receipt.vendor.ilike(f"%{filters.vendor}%"))
            if filters.category:
                query = query.filter(Receipt.category.ilike(f"%{filters.category}%"))
            if filters.min_amount is not None:
                query = query.filter(Receipt.amount >= filters.min_amount)
            if filters.max_amount is not None:
                query = query.filter(Receipt.amount <= filters.max_amount)
            if filters.start_date:
                query = query.filter(Receipt.transaction_date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Receipt.transaction_date <= filters.end_date)
        
        receipts = query.all()
        
        # Define default fields
        default_fields = ['id', 'filename', 'vendor', 'transaction_date', 'amount', 'category', 'upload_date']
        fields = export_request.include_fields or default_fields
        
        if export_request.format == "csv":
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(fields)
            
            # Write data
            for receipt in receipts:
                row = []
                for field in fields:
                    value = getattr(receipt, field, '')
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row.append(value)
                writer.writerow(row)
            
            # Create response
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=receipts.csv"}
            )
        
        elif export_request.format == "json":
            # Create JSON
            data = []
            for receipt in receipts:
                item = {}
                for field in fields:
                    value = getattr(receipt, field, None)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    item[field] = value
                data.append(item)
            
            json_str = json.dumps(data, indent=2, default=str)
            return StreamingResponse(
                io.BytesIO(json_str.encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=receipts.json"}
            )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/currency/supported")
async def get_supported_currencies():
    """Get list of supported currencies"""
    try:
        currencies = currency_service.get_supported_currencies()
        return {
            "supported_currencies": currencies,
            "default_base": "USD"
        }
    except Exception as e:
        logger.error(f"Failed to get supported currencies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get supported currencies")

@app.post("/currency/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str = "USD"
):
    """Convert amount between currencies"""
    try:
        converted_amount = currency_service.convert_currency(amount, from_currency, to_currency)
        
        if converted_amount is None:
            raise HTTPException(status_code=400, detail="Currency conversion failed")
        
        # Get exchange rate
        exchange_rate = converted_amount / amount if amount > 0 else 0
        
        return {
            "original_amount": amount,
            "original_currency": from_currency,
            "converted_amount": converted_amount,
            "target_currency": to_currency,
            "exchange_rate": exchange_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Currency conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Currency conversion failed: {str(e)}")

@app.post("/receipts/{receipt_id}/currency-info")
async def get_receipt_currency_info(
    receipt_id: int,
    target_currency: str = "USD",
    db: Session = Depends(get_db)
):
    """Get currency information for a specific receipt"""
    try:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if not receipt.raw_text:
            raise HTTPException(status_code=400, detail="No text available for currency analysis")
        
        # Detect and convert currency
        currency_info = currency_service.detect_and_convert_currency(receipt.raw_text, target_currency)
        
        return {
            "receipt_id": receipt_id,
            "currency_analysis": currency_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Currency analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Currency analysis failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
