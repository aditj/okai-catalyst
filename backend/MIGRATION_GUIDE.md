# Migration Guide: Node.js to Python FastAPI

This guide helps you migrate from the Node.js Express backend to the new Python FastAPI backend.

## Why Migrate?

The Python FastAPI backend offers several advantages:

- **Better Performance**: FastAPI is one of the fastest Python frameworks
- **Automatic Documentation**: Built-in OpenAPI/Swagger documentation
- **Type Safety**: Pydantic models provide request/response validation
- **Modern Python**: Uses async/await and type hints
- **Better Error Handling**: More robust error handling and logging
- **Development Tools**: Auto-reload, interactive docs, and better debugging

## Quick Migration Steps

### 1. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Copy Environment Variables

If you have a `.env` file with your Google API key:
```bash
# Your existing .env file will work as-is
# Make sure it contains: GOOGLE_API_KEY=your_actual_key
```

If you don't have a `.env` file:
```bash
# Copy the example file
cp env.example .env
# Edit .env and add your Google AI API key
```

### 3. Stop Node.js Server and Start Python Server

```bash
# Stop your Node.js server (Ctrl+C if running)

# Start the Python server
python main.py
# OR
python start_python.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 5001
```

### 4. Test the Migration

The API endpoints are identical, so your frontend will work without changes:

- Health check: `GET http://localhost:5001/`
- Generate case: `GET http://localhost:5001/api/generate-case`
- Evaluate analysis: `POST http://localhost:5001/api/evaluate`

## API Compatibility

✅ **Fully Compatible** - No frontend changes needed!

| Endpoint | Method | Request Format | Response Format | Status |
|----------|--------|----------------|-----------------|---------|
| `/` | GET | - | `{"message": "..."}` | ✅ Identical |
| `/api/generate-case` | GET | - | `{"caseStudy": "..."}` | ✅ Identical |
| `/api/evaluate` | POST | `{"analysisText": "..."}` | `{"rootCauseScore": N, "solutionScore": N, "feedback": "..."}` | ✅ Identical |

## New Features in Python Version

### 1. Interactive API Documentation
- **Swagger UI**: `http://localhost:5001/docs`
- **ReDoc**: `http://localhost:5001/redoc`

### 2. Request/Response Validation
- Automatic validation of request bodies
- Clear error messages for invalid requests
- Type-safe response models

### 3. Better Logging
- Structured logging with timestamps
- Clearer error messages
- Better debugging information

### 4. Performance Improvements
- Async/await for better concurrency
- Faster JSON processing
- More efficient memory usage

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Make sure to stop the Node.js server first
# Or use a different port:
uvicorn main:app --port 5002
```

**2. Missing Dependencies**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**3. Google AI API Issues**
```bash
# Check your .env file
cat .env
# Verify your API key is valid
```

**4. Import Errors**
```bash
# Make sure you're in the right directory
cd backend
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Rollback (If Needed)

If you need to go back to Node.js:

```bash
# Stop Python server (Ctrl+C)

# Start Node.js server
npm start
# OR
node server.js
```

Your Node.js code remains unchanged and fully functional.

## Performance Comparison

| Metric | Node.js Express | Python FastAPI |
|--------|----------------|----------------|
| Startup Time | ~1-2 seconds | ~1-2 seconds |
| Request/Response | Fast | Fast |
| Memory Usage | Moderate | Moderate |
| Development Experience | Good | Excellent |
| Documentation | Manual | Automatic |
| Type Safety | Limited | Excellent |

## Next Steps

1. **Test thoroughly** - Verify all functionality works as expected
2. **Check logs** - Monitor the console for any issues
3. **Use new features** - Explore the automatic API documentation
4. **Remove Node.js files** (optional) - Once you're confident, you can clean up:
   ```bash
   # Remove Node.js files (optional)
   rm server.js package.json package-lock.json
   rm -rf node_modules/
   ```

## Support

If you encounter any issues during migration:

1. Check the logs for error messages
2. Verify your `.env` file is correctly formatted
3. Ensure all dependencies are installed
4. Test individual endpoints using the interactive docs at `/docs` 