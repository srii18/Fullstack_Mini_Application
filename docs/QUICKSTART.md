# Quick Start Guide

##  Getting Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Generate Test Data (Optional)
```bash
python test_data_generator.py generate 30
```

### Step 3: Start the Application
```bash
# Option A: Use the startup script (recommended)
python start_app.py

# Option B: Start services manually
# Terminal 1 - Backend API
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend Dashboard
python -m streamlit run dashboard.py --server.port 8501
```

## Access Points

- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Features Available

### Upload & Process
- Drag and drop receipt files (.jpg, .png, .pdf, .txt)
- Real-time OCR processing with confidence scoring
- Automatic data extraction (vendor, amount, date, category)

### Search & Filter
- Keyword search across all receipt text
- Filter by vendor, category, amount range, date range
- Advanced multi-criteria search with sorting

### Analytics & Insights
- Total spending and transaction statistics
- Top vendors and category breakdowns
- Monthly spending trends with moving averages
- Interactive charts and visualizations

### API Testing
```bash
# Test all API endpoints
python test_api.py

# Clear test data
python test_data_generator.py clear
```

## Troubleshooting

### Port Already in Use
If you get a port conflict error:
```bash
# Kill processes on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use different ports
uvicorn main:app --port 8001
streamlit run dashboard.py --server.port 8502
```

### OCR Not Working
Make sure Tesseract is installed:
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH environment variable
- Restart terminal after installation

### Database Issues
```bash
# Reset database
python -c "import os; os.remove('database.db') if os.path.exists('database.db') else None"
python test_data_generator.py generate 20
```

## Project Structure

```
├── algorithms/              # Core algorithms (search, sort, aggregation)
├── models/                  # Database models
├── schemas/                 # Data validation schemas
├── services/                # OCR and text processing
├── main.py                  # FastAPI backend
├── dashboard.py             # Streamlit frontend
├── start_app.py            # Application launcher
└── test_*.py               # Testing utilities
```

##  Next Steps

1. **Upload your receipts** through the dashboard
2. **Explore analytics** to understand spending patterns
3. **Use search features** to find specific transactions
4. **Customize categories** by editing `services/text_parser.py`
5. **Add new features** using the modular architecture
