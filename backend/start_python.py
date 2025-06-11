#!/usr/bin/env python3
"""
Startup script for the Catalyst FastAPI Backend
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Start the FastAPI server with appropriate configuration"""
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check if .env file exists
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your GOOGLE_API_KEY")
        print("Example:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print()
    
    # Start the server
    print("🚀 Starting Catalyst FastAPI Backend...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print()
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=5002,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 