# Catalyst Backend

## Setup

1. Create a `.env` file in the backend directory with the following content:
```
GOOGLE_API_KEY=your_google_api_key_here
```

2. Get your Google API key from: https://makersuite.google.com/app/apikey

3. Install dependencies (already done):
```bash
npm install
```

4. Start the server:
```bash
npm start
```

The server will run on http://localhost:5001

## API Endpoints

### POST /api/evaluate
Evaluates a user's analysis text and returns scores and feedback.

**Request Body:**
```json
{
  "analysisText": "Your analysis here..."
}
```

**Response:**
```json
{
  "rootCauseScore": 8,
  "solutionScore": 7,
  "feedback": "Good analysis with clear identification of root causes..."
}
``` 