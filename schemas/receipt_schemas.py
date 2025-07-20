from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class FileType(str, Enum):
    """Supported file types for validation"""
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    PDF = "pdf"
    TXT = "txt"

class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class ReceiptBase(BaseModel):
    """Base receipt schema with validation rules"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: FileType
    vendor: Optional[str] = Field(None, max_length=255)
    transaction_date: Optional[datetime] = None
    amount: Optional[float] = Field(None, ge=0)  # Amount must be >= 0
    category: Optional[str] = Field(None, max_length=100)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amount must be non-negative')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()

class ReceiptCreate(ReceiptBase):
    """Schema for creating new receipts"""
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)  # 0-1 range for OCR confidence

class ReceiptUpdate(BaseModel):
    """Schema for updating existing receipts"""
    vendor: Optional[str] = Field(None, max_length=255)
    transaction_date: Optional[datetime] = None
    amount: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    processing_status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None

class ReceiptResponse(ReceiptBase):
    """Schema for receipt responses"""
    id: int
    upload_date: datetime
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class SearchFilters(BaseModel):
    """Schema for search and filtering parameters"""
    vendor: Optional[str] = None
    category: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    keyword: Optional[str] = None  # For text search in vendor/raw_text
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v < values['min_amount']:
                raise ValueError('max_amount must be greater than or equal to min_amount')
        return v

class SortOptions(BaseModel):
    """Schema for sorting parameters"""
    field: str = Field(..., pattern="^(upload_date|transaction_date|amount|vendor|category)$")
    direction: str = Field("asc", pattern="^(asc|desc)$")

class AggregationResponse(BaseModel):
    """Schema for aggregation results"""
    total_receipts: int
    total_amount: float
    average_amount: float
    median_amount: float
    min_amount: float
    max_amount: float
    top_vendors: List[dict]  # [{"vendor": "name", "count": n, "total": amount}]
    category_distribution: List[dict]  # [{"category": "name", "count": n, "percentage": p}]
    monthly_trends: List[dict]  # [{"month": "YYYY-MM", "total": amount, "count": n}]
