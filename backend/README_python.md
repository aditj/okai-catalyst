# Catalyst Backend API (Python FastAPI)

This is the Python FastAPI backend for the Catalyst MVP application. It provides AI-powered manufacturing case study generation and analysis evaluation.

## Features

- **Case Study Generation**: Generate unique manufacturing problem scenarios using Google AI
- **Analysis Evaluation**: Score and provide feedback on user's problem analysis
- **REST API**: Clean, documented API endpoints with automatic OpenAPI/Swagger documentation
- **CORS Support**: Configured for frontend integration
- **Error Handling**: Robust error handling with fallback responses

## Setup

### Prerequisites
- Python 3.8 or higher
- Google AI API key (for Gemini model access)

### Installation

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment setup**:
   Create a `.env` file in the backend directory:
   ```env
   GOOGLE_API_KEY=your_google_ai_api_key_here
   ```

## Running the Server

### Development Mode
```bash
python main.py
```

### Using Uvicorn directly
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### GET `/`
Health check endpoint
- **Response**: `{"message": "Catalyst Backend API is running!"}`

### GET `/api/generate-case`
Generate a new manufacturing case study
- **Response**: `{"caseStudy": "Case Study: [Generated case study text]"}`

### POST `/api/evaluate`
Evaluate user's manufacturing problem analysis
- **Request Body**: `{"analysisText": "User's analysis text"}`
- **Response**: 
  ```json
  {
    "rootCauseScore": 8,
    "solutionScore": 7,
    "feedback": "Good analysis with specific recommendations..."
  }
  ```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (create this)
└── README_python.md    # This file
```

## Migration from Node.js

This Python FastAPI backend provides identical functionality to the original Node.js Express server:

- Same endpoints (`/`, `/api/generate-case`, `/api/evaluate`)
- Same request/response formats
- Same Google AI integration
- Same error handling patterns
- Same CORS configuration

The frontend code requires no changes to work with this Python backend.

## Development Notes

- Uses Pydantic for request/response validation
- Structured logging for better debugging
- Type hints for better code maintainability
- Async/await for better performance
- Automatic API documentation generation 