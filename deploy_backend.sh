#!/bin/bash

# Backend Deployment Script for Catalyst Application
echo "🚀 Deploying Catalyst Backend..."

# Navigate to backend directory
cd backend

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file template..."
    echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
    echo "❗ Please edit .env file and add your Google API key before running the server!"
    echo "   You can get your API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Start the server
echo "🌟 Starting FastAPI server..."
echo "Backend will be available at: http://localhost:8000"
echo "API docs available at: http://localhost:8000/docs"
python main.py 