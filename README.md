# Receipt Processing Mini-Application

A full-stack application for uploading and processing receipts/bills with OCR, data extraction, and analytics.

## Features

- **File Upload**: Support for .jpg, .png, .pdf, .txt formats
- **OCR Processing**: Extract text from images using Tesseract
- **Data Extraction**: Parse vendor, date, amount, and category information
- **Database Storage**: SQLite with normalized schema and indexing
- **Search & Sort**: Advanced search algorithms with multiple criteria
- **Analytics**: Statistical aggregations and visualizations
- **Web Interface**: Streamlit dashboard for easy interaction

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Database**: SQLite
- **OCR**: Tesseract + OpenCV
- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Validation**: Pydantic

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Tesseract OCR:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Add to PATH environment variable

3. Run the application:
```bash
# Start backend API
uvicorn main:app --reload

# Start Streamlit dashboard (in another terminal)
streamlit run dashboard.py
```

## Project Structure

```
├── main.py              # FastAPI backend
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── algorithms/          # Search, sort, aggregation
├── dashboard.py         # Streamlit frontend
├── uploads/             # File storage
└── database.db         # SQLite database
```
