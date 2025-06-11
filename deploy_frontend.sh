#!/bin/bash

# Frontend Deployment Script for Catalyst Application
echo "🚀 Deploying Catalyst Frontend..."

# Navigate to frontend directory
cd frontend/frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "📋 Node.js version: $(node --version)"
echo "📋 npm version: $(npm --version)"

# Install dependencies
echo "📚 Installing dependencies..."
npm install

# Build the application for production
echo "🏗️  Building application for production..."
npm run build

# Start the development server (for local testing)
echo "🌟 Starting development server..."
echo "Frontend will be available at: http://localhost:3000"
echo "Make sure the backend is running at: http://localhost:8000"
npm start 