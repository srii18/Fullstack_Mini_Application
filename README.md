# Receipt Processing Application

A comprehensive full-stack application for processing receipts and bills with OCR, data extraction, analytics, and advanced features including multi-currency support and multi-language processing.

## Overview

This application provides a complete solution for digitizing and analyzing receipts/bills with automatic text extraction, data parsing, and business intelligence capabilities. It features a modern web interface built with Streamlit and a robust FastAPI backend.

## Core Features

### Document Processing
- **Multi-format Support**: Process .jpg, .png, .pdf, .txt files
- **OCR Technology**: Advanced text extraction using Tesseract with preprocessing
- **Multi-language Support**: Process receipts in English, Spanish, French, and more
- **Data Extraction**: Automatic parsing of vendor, date, amount, and category information
- **Confidence Scoring**: OCR accuracy assessment for quality control

### Data Management
- **Database Storage**: SQLite with optimized schema and indexing
- **Manual Correction**: Edit and correct parsed data through intuitive UI
- **Data Validation**: Comprehensive input validation and error handling
- **Search & Filter**: Advanced search with multiple criteria and sorting options
- **Export Capabilities**: Export data as CSV or JSON with flexible filtering

### Analytics & Insights
- **Statistical Analysis**: Comprehensive spending analytics and trends
- **Visualization**: Interactive charts and graphs using Plotly
- **Vendor Analytics**: Top vendors and spending patterns
- **Category Breakdown**: Expense categorization and distribution
- **Time-based Analysis**: Monthly trends and seasonal patterns

### Advanced Features
- **Multi-currency Support**: Automatic currency detection and conversion (19+ currencies)
- **Real-time Exchange Rates**: Live currency conversion with caching
- **Language Detection**: Automatic language identification for optimal OCR
- **Batch Processing**: Handle multiple receipts efficiently
- **API-first Design**: Complete REST API for integration

## Technology Stack

### Backend
- **Framework**: FastAPI with async support
- **Database**: SQLAlchemy ORM with SQLite
- **OCR Engine**: Tesseract with OpenCV preprocessing
- **Validation**: Pydantic schemas with comprehensive validation
- **Currency API**: Real-time exchange rate integration

### Frontend
- **Framework**: Streamlit for interactive web interface
- **Visualization**: Plotly for charts and analytics
- **UI Components**: Custom styled components with responsive design

### External Services
- **Exchange Rates**: exchangerate-api.com integration
- **OCR Languages**: Multi-language Tesseract models

## Quick Start

### Prerequisites
- Python 3.8+
- Tesseract OCR installed and in PATH
- Internet connection for currency conversion

### Installation

1. Clone the repository:
```bash
git clone https://github.com/srii18/Fullstack_Mini_Application.git
cd Fullstack_Mini_Application
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
   - **Windows**: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

4. Install additional language packs (optional):
   - **Spanish**: `tesseract-ocr-spa`
   - **French**: `tesseract-ocr-fra`
   - **German**: `tesseract-ocr-deu`

### Running the Application

#### Option 1: Quick Start (Recommended)
```bash
python start_app.py
```

#### Option 2: Manual Start
```bash
# Terminal 1 - Start backend API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Start frontend dashboard
streamlit run dashboard.py
```

### Access the Application
- **Web Interface**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## Project Structure

```
Fullstack_Mini_Application/
├── main.py                 # FastAPI backend application
├── dashboard.py            # Streamlit frontend interface
├── start_app.py           # Application launcher
├── requirements.txt       # Python dependencies
├── database.db           # SQLite database (auto-created)
├── .gitignore            # Git ignore rules
│
├── models/               # Database models and schemas
│   ├── __init__.py
│   └── database.py       # SQLAlchemy models and database setup
│
├── schemas/              # Pydantic validation schemas
│   ├── __init__.py
│   └── receipt_schemas.py # Request/response schemas
│
├── services/             # Business logic and external services
│   ├── __init__.py
│   ├── ocr_service.py    # OCR processing with multi-language support
│   ├── text_parser.py    # Text parsing and data extraction
│   └── currency_service.py # Currency detection and conversion
│
├── algorithms/           # Data processing algorithms
│   ├── __init__.py
│   ├── search_algorithms.py    # Search and filtering logic
│   ├── sort_algorithms.py      # Sorting implementations
│   └── aggregation_algorithms.py # Analytics and aggregations
│
├── uploads/              # File storage directory
│
├── tests/                # Test files and utilities
│   ├── test_api.py       # API endpoint tests
│   └── test_data_generator.py # Test data generation
│
└── docs/                 # Documentation
    ├── QUICKSTART.md     # Quick start guide
    └── BONUS_FEATURES.md # Advanced features documentation
```

## API Endpoints

### Core Endpoints
- `POST /receipts/upload` - Upload and process receipt
- `GET /receipts/` - List all receipts with pagination
- `GET /receipts/{id}` - Get specific receipt
- `PUT /receipts/{id}` - Update receipt data
- `DELETE /receipts/{id}` - Delete receipt
- `POST /receipts/search` - Advanced search with filters

### Analytics Endpoints
- `GET /receipts/analytics/summary` - Comprehensive analytics
- `GET /receipts/analytics/vendors` - Vendor analysis
- `GET /receipts/analytics/trends` - Spending trends
- `GET /receipts/analytics/categories` - Category breakdown

### Advanced Features
- `POST /receipts/{id}/correct` - Manual field correction
- `POST /receipts/export` - Export data as CSV/JSON
- `GET /currency/supported` - Supported currencies
- `POST /currency/convert` - Currency conversion
- `POST /receipts/{id}/currency-info` - Receipt currency analysis

## Usage Examples

### Basic Receipt Processing
1. Navigate to the Upload page
2. Select a receipt file (image, PDF, or text)
3. Click "Process Receipt" to extract data
4. Review extracted information
5. Make corrections if needed using Manual Correction page

### Advanced Analytics
1. Go to Analytics page
2. View spending summaries and trends
3. Analyze vendor patterns
4. Export data for external analysis

### Multi-currency Handling
1. Upload receipts in different currencies
2. System automatically detects currency symbols
3. View converted amounts in preferred currency
4. Use currency conversion API for custom conversions

## Configuration

### Environment Variables
- `TESSERACT_CMD`: Path to Tesseract executable (if not in PATH)
- `DATABASE_URL`: Database connection string (default: SQLite)
- `UPLOAD_DIR`: File upload directory (default: ./uploads)

### Customization
- **OCR Languages**: Modify `supported_languages` in `ocr_service.py`
- **Currency Support**: Update `currency_patterns` in `text_parser.py`
- **Categories**: Customize `vendor_categories` mapping

## Testing

### Generate Test Data
```bash
python test_data_generator.py generate 50
```

### Run API Tests
```bash
python test_api.py
```

### Clear Test Data
```bash
python test_data_generator.py clear
```

## Troubleshooting

### Common Issues
1. **Tesseract not found**: Ensure Tesseract is installed and in PATH
2. **OCR accuracy low**: Check image quality and language settings
3. **Currency conversion fails**: Verify internet connection for exchange rates
4. **Database errors**: Check file permissions and disk space

### Performance Optimization
- **Image preprocessing**: Adjust OCR preprocessing parameters
- **Database indexing**: Optimize queries for large datasets
- **Caching**: Exchange rates cached for 1 hour
- **Batch processing**: Process multiple files efficiently

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the documentation in the `docs/` directory
2. Review the troubleshooting section
3. Create an issue on GitHub
4. Check API documentation at `/docs` endpoint
