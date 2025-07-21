#!/usr/bin/env python3
"""
Startup script for the Receipt Processing Application
This script starts both the FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print(" Starting FastAPI backend server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n Backend server stopped")
    except Exception as e:
        print(f" Error starting backend: {e}")

def start_frontend():
    """Start the Streamlit frontend"""
    print(" Starting Streamlit frontend...")
    time.sleep(3)  # Wait for backend to start
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "dashboard.py", 
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ], check=True)
    except KeyboardInterrupt:
        print("\n Frontend server stopped")
    except Exception as e:
        print(f" Error starting frontend: {e}")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'sqlalchemy', 
        'pydantic', 'pytesseract', 'opencv-python', 'pillow'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(" Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def open_browser():
    """Open browser to the application"""
    time.sleep(5)  # Wait for servers to start
    print(" Opening browser...")
    webbrowser.open("http://localhost:8501")

def main():
    """Main startup function"""
    print("=" * 60)
    print(" RECEIPT PROCESSING APPLICATION")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print(" Please run this script from the project root directory")
        sys.exit(1)
    
    print("\n Starting application components...")
    print("   Backend API: http://localhost:8000")
    print("   Frontend Dashboard: http://localhost:8501")
    print("\n  Press Ctrl+C to stop both servers\n")
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Open browser in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start frontend in main thread
        start_frontend()
        
    except KeyboardInterrupt:
        print("\n\n Shutting down application...")
        print(" Application stopped successfully")

if __name__ == "__main__":
    main()
