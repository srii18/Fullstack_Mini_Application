from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Receipt(Base):
    """Receipt/Bill model with normalized schema and indexing for optimized search"""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # jpg, png, pdf, txt
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Extracted data fields
    vendor = Column(String(255), index=True)  # Indexed for search optimization
    transaction_date = Column(DateTime, index=True)  # Indexed for date range queries
    amount = Column(Float, index=True)  # Indexed for numerical sorting/filtering
    category = Column(String(100), index=True)  # Indexed for categorical filtering
    
    # Raw extracted text and processing metadata
    raw_text = Column(Text)
    confidence_score = Column(Float)  # OCR confidence if applicable
    processing_status = Column(String(50), default="pending")  # pending, processed, failed
    error_message = Column(Text)
    
    # Additional indexes for compound queries
    __table_args__ = (
        Index('idx_vendor_date', 'vendor', 'transaction_date'),
        Index('idx_amount_date', 'amount', 'transaction_date'),
        Index('idx_category_date', 'category', 'transaction_date'),
    )

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
