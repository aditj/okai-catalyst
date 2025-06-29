from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.genai as genai
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional
from supabase import create_client, Client
from dashboard import dashboard_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase client
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Supabase: {e}")
    supabase = None

# Initialize FastAPI app
app = FastAPI(title="Catalyst Backend API", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include dashboard router
app.include_router(dashboard_router)

# Configure Google AI
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = 'gemini-2.5-flash-preview-05-20'
    logger.info("Google AI configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Google AI: {e}")
    model_name = None


# Enhanced Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    analysisText: str

class PartSubmissionRequest(BaseModel):
    partId: int
    responses: Dict[str, str]  # questionId -> response
    sessionId: str
    audioData: Optional[str] = None  # Base64 encoded audio for Part 5

class EvaluationResponse(BaseModel):
    rootCauseScore: float
    solutionScore: float
    feedback: str

class PartEvaluationResponse(BaseModel):
    partId: int
    scores: Dict[str, float]  # rubricId -> score (allow floats)
    feedback: str
    canProceed: bool
    averageScore: float
    nextPartId: Optional[int] = None
    transcription: Optional[str] = None  # For audio responses

class FinalEvaluationResponse(BaseModel):
    overallScores: Dict[str, float]  # Overall scores across all parts (allow floats)
    partScores: List[Dict]  # Individual part scores
    detailedFeedback: str
    overallPerformance: str
    totalQuestions: int
    averageScore: float
    completionTime: str
    toolRecommendations: Dict[str, Dict[str, str]]  # Tool mapping based on weaknesses

class CaseStudyResponse(BaseModel):
    caseStudy: str

class MultiPartCaseStudyResponse(BaseModel):
    caseStudy: str
    sessionId: str
    parts: List[Dict]
    totalParts: int
    estimatedTime: str

class SessionStatusResponse(BaseModel):
    sessionId: str
    completedParts: List[int]
    currentPart: int
    isComplete: bool
    createdAt: str

class HealthResponse(BaseModel):
    message: str
    activeSessionsCount: int
    version: str

# Database helper functions
def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    if not supabase:
        return
    
    try:
        from datetime import timezone
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        result = supabase.table("sessions").delete().lt("created_at", cutoff_time).execute()
        if result.data:
            logger.info(f"Cleaned up {len(result.data)} expired sessions")
    except Exception as e:
        logger.error(f"Error cleaning up old sessions: {e}")

def get_current_part(completed_parts):
    """Determine the current part based on completed parts"""
    for part_id in range(1, 5):
        if part_id not in completed_parts:
            return part_id
    return 5  # All parts completed

def get_session_from_db(session_id: str):
    """Get session data from database"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("sessions").select("*").eq("session_id", session_id).execute()
        if not result.data:
            return None
        return result.data[0]
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        return None

def calculate_average_score(scores):
    """Calculate average score from a scores dictionary"""
    if not scores:
        return 0.0
    return round(sum(scores.values()) / len(scores), 1)

def validate_part_responses(part, responses):
    """Validate that all required questions are answered"""
    missing_questions = []
    for question in part["questions"]:
        if question["id"] not in responses or not responses[question["id"]].strip():
            missing_questions.append(question["question"][:50] + "...")
    return missing_questions

# Enhanced evaluation parts with better question structure
EVALUATION_PARTS = [
    {
        "id": 1,
        "title": "Problem Identification & Data Gathering",
        "description": "Identify what information you need to understand the problem better and plan your investigation approach.",
        "questions": [
            {
                "id": "q1_data",
                "question": "What specific quantitative data would you collect to better understand this manufacturing problem? List 4-5 key metrics and explain why each is important.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q1_stakeholders", 
                "question": "Who are the key people you would interview to gather information about this issue? For each person/role, specify what unique insights they could provide.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q1_observations",
                "question": "What direct observations would you make on the production floor? Describe your observation plan including timing, duration, and specific things to look for.",
                "type": "text",
                "minLength": 0
            }
        ],
        "rubrics": {
            "data_focus": "How well did they identify relevant quantitative metrics and explain their importance?",
            "stakeholder_identification": "Did they identify appropriate people with clear rationale for what insights each could provide?",
            "observation_skills": "How systematic and comprehensive is their observation plan?"
        },
        "passingScore": 5.0
    },
    {
        "id": 2,
        "title": "Root Cause Analysis",
        "description": "Based on your data gathering approach, systematically identify and analyze potential root causes.",
        "questions": [
            {
                "id": "q2_causes",
                "question": "Using a structured approach (like the 5M framework: Man, Machine, Material, Method, Environment), list 4-6 potential root causes for this problem. For each cause, explain your reasoning.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q2_method",
                "question": "What structured root cause analysis method would you use (e.g., 5 Whys, Fishbone Diagram, Fault Tree Analysis)? Explain your choice and how you would apply it to this specific problem.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q2_validation",
                "question": "How would you validate which root cause is the actual cause? Describe your testing/validation approach and what evidence you would look for.",
                "type": "text",
                "minLength": 0
            }
        ],
        "rubrics": {
            "systematic_thinking": "Did they use systematic frameworks and demonstrate structured thinking?",
            "methodology": "Did they choose appropriate analysis methods and explain their reasoning?",
            "validation_approach": "How well did they plan to test and validate their hypotheses?"
        },
        "passingScore": 5.0
    },
    {
        "id": 3,
        "title": "Solution Development",
        "description": "Develop practical, implementable solutions that directly address the root causes you identified.",
        "questions": [
            {
                "id": "q3_solutions",
                "question": "Propose 3-4 specific solutions that address the root causes you identified. For each solution, explain how it directly tackles the root cause and estimate the effort/cost level (Low/Medium/High).",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q3_implementation",
                "question": "For your highest-priority solution, create a detailed implementation plan including: key steps, timeline, required resources, responsible parties, and success criteria.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q3_risks",
                "question": "What are the potential risks, challenges, or unintended consequences of your solution? For each risk, propose a mitigation strategy.",
                "type": "text",
                "minLength": 0
            }
        ],
        "rubrics": {
            "solution_relevance": "How directly and effectively do the solutions address the identified root causes?",
            "practicality": "How realistic, detailed, and implementable are the solutions and plans?",
            "risk_awareness": "Did they identify realistic risks and provide thoughtful mitigation strategies?"
        },
        "passingScore": 5.0
    },
    {
        "id": 4,
        "title": "Implementation & Monitoring",
        "description": "Plan how to implement your solution effectively and ensure sustainable improvements.",
        "questions": [
            {
                "id": "q4_metrics",
                "question": "What specific KPIs and metrics would you track to measure if your solution is working? Include leading indicators (early signals) and lagging indicators (final results).",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q4_timeline",
                "question": "Create a realistic timeline showing: implementation phases, when you expect to see initial improvements, when to measure full impact, and review checkpoints. Justify your timeframes.",
                "type": "text",
                "minLength": 0
            },
            {
                "id": "q4_sustainability",
                "question": "How would you ensure the solution is sustained long-term? Address: training needs, process standardization, accountability measures, and continuous improvement mechanisms.",
                "type": "text",
                "minLength": 0
            }
        ],
        "rubrics": {
            "measurement_focus": "Did they identify appropriate leading and lagging indicators for success?",
            "realistic_timeline": "Is their timeline realistic with proper justification for timeframes?",
            "sustainability": "How well did they address long-term sustainability and continuous improvement?"
        },
        "passingScore": 5.0
    },
    {
        "id": 5,
        "title": "Verbal Explanation & Approach Summary",
        "description": "Record a 2-minute verbal explanation of your overall approach to solving this manufacturing problem.",
        "questions": [
            {
                "id": "q5_verbal",
                "question": "Record a 2-minute verbal explanation covering: (1) Your overall problem-solving approach, (2) Key insights you discovered, (3) How you prioritized solutions, and (4) What you learned from this analysis. Click the record button and speak clearly.",
                "type": "audio",
                "duration": 120,
                "instructions": "Click 'Start Recording' and speak for up to 2 minutes. The recording will automatically stop after 2 minutes."
            }
        ],
        "rubrics": {
            "communication_clarity": "How clearly and effectively did they communicate their approach and insights?",
            "synthesis_ability": "How well did they synthesize and connect insights across all parts of the analysis?",
            "professional_presentation": "Did they demonstrate professional communication skills and confidence?",
            "depth_of_understanding": "How well did they demonstrate deep understanding of manufacturing problem-solving?"
        },
        "passingScore": 5.0
    }
]

# Health check endpoint with enhanced info
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with system status"""
    cleanup_old_sessions()  # Clean up old sessions on health check
    
    # Get active sessions count from database
    active_sessions_count = 0
    if supabase:
        try:
            result = supabase.table("sessions").select("id").execute()
            active_sessions_count = len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"Error counting active sessions: {e}")
    
    return HealthResponse(
        message="Catalyst Backend API is running!",
        activeSessionsCount=active_sessions_count,
        version="2.0.0"
    )

# Enhanced multi-part case study generation
@app.get("/api/generate-multipart-case", response_model=MultiPartCaseStudyResponse)
async def generate_multipart_case():
    """Generate a comprehensive manufacturing case study for multi-part evaluation"""
    try:
        cleanup_old_sessions()  # Clean up before creating new session
        
        if not model_name:
            raise HTTPException(status_code=500, detail="AI model not configured")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        
        # Enhanced case study generation prompt
        with open('promptforcasestudy.md', 'r') as file:
            prompt = file.read()
        
        # Generate response with retry logic
        max_retries = 3
        case_study = None
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config = genai.types.GenerateContentConfig(
                        thinking_config=genai.types.ThinkingConfig(thinking_budget=0)
                    )
                )
                case_study = response.text.strip()
                
                # Validate case study length
                if len(case_study) < 100:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise ValueError("Generated case study too short")
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    continue
                else:
                    logger.error(f"All case study generation attempts failed: {e}")
                    case_study = None

        # Use fallback if generation failed
        if not case_study:
            case_study = (
                "Case Study: Critical Quality Crisis at Advanced Electronics Manufacturing. "
                "TechFlow Industries, a 500-employee electronics manufacturer, is experiencing a severe quality crisis "
                "affecting their primary product line. Over the past 6 weeks, customer returns have increased by 35%, "
                "with defects ranging from intermittent connection failures (40% of returns) to complete component "
                "malfunctions (25% of returns). The defects are discovered at various stages: 30% during final testing, "
                "45% during customer burn-in testing, and 25% in field use within 30 days. This has resulted in "
                "$2.3M in warranty costs, 15% reduction in production throughput due to increased rework, and "
                "two major customers threatening to switch suppliers. The manufacturing process involves 12 automated "
                "assembly stations, 3 manual inspection points, and employs 85 production workers across 3 shifts. "
                "Recent changes include a new supplier for critical components (implemented 8 weeks ago) and "
                "upgraded software on 4 assembly machines (implemented 10 weeks ago). Your task is to analyze "
                "this problem systematically through a structured approach."
            )

        # Generate session ID and store in database
        session_id = str(uuid.uuid4())
        total_questions = sum(len(part["questions"]) for part in EVALUATION_PARTS)
        
        # Store session in database
        from datetime import timezone
        current_time = datetime.now(timezone.utc).isoformat()
        session_data = {
            "session_id": session_id,
            "case_study": case_study,
            "completed_parts": [],
            "total_questions": total_questions,
            "created_at": current_time,
            "last_activity": current_time,
            "is_complete": False
        }
        
        result = supabase.table("sessions").insert(session_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create session")

        return MultiPartCaseStudyResponse(
            caseStudy=case_study,
            sessionId=session_id,
            parts=EVALUATION_PARTS,
            totalParts=len(EVALUATION_PARTS),
            estimatedTime="30-45 minutes"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_multipart_case: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Enhanced part submission with improved validation and AI evaluation
@app.post("/api/submit-part", response_model=PartEvaluationResponse)
async def submit_part(request: PartSubmissionRequest):
    """Submit responses for a specific part with enhanced validation and evaluation"""
    try:
        if not model_name:
            raise HTTPException(status_code=500, detail="AI model not configured")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")

        # Validate session exists
        session = get_session_from_db(request.sessionId)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        part = next((p for p in EVALUATION_PARTS if p["id"] == request.partId), None)
        if not part:
            raise HTTPException(status_code=400, detail="Invalid part ID")

        # Check if part already completed
        existing_evaluation = supabase.table("part_evaluations").select("*").eq("session_id", request.sessionId).eq("part_id", request.partId).execute()
        if existing_evaluation.data:
            raise HTTPException(status_code=400, detail="Part already completed")

        # Special handling for Part 5 (audio recording)
        if request.partId == 5:
            if not request.audioData:
                raise HTTPException(status_code=400, detail="Audio recording is required for Part 5")
            
            # Store audio response in database
            response_data = {
                "session_id": request.sessionId,
                "part_id": request.partId,
                "question_id": "q5_verbal",
                "response_text": "Audio recording submitted",
                "audio_data": request.audioData
            }
            supabase.table("responses").insert(response_data).execute()
            
            # Evaluate audio recording
            evaluation_data = await evaluate_audio_response(request.audioData, session["case_study"])
            
        else:
            # Regular text-based part validation and processing
            # Store responses in database
            for question in part["questions"]:
                response_text = request.responses.get(question["id"], "").strip()
                if not response_text:
                    response_text = f"[No response provided for: {question['question'][:100]}...]"
                
                response_data = {
                    "session_id": request.sessionId,
                    "part_id": request.partId,
                    "question_id": question["id"],
                    "response_text": response_text
                }
                supabase.table("responses").insert(response_data).execute()
            
            # Get processed responses for evaluation
            processed_responses = {}
            for question in part["questions"]:
                response_text = request.responses.get(question["id"], "").strip()
                if not response_text:
                    processed_responses[question["id"]] = f"[No response provided for: {question['question'][:100]}...]"
                else:
                    processed_responses[question["id"]] = response_text
            
            # Create enhanced evaluation prompt for text responses
            case_study = session["case_study"]
            responses_text = ""
            for i, question in enumerate(part["questions"], 1):
                response = processed_responses.get(question["id"], "No response")
                responses_text += f"\nQuestion {i}: {question['question']}\nStudent Response: {response}\n"
            
            rubrics_text = ""
            for key, description in part["rubrics"].items():
                rubrics_text += f"\n Rubric Text:  {key.replace('_', ' ').title()}: {description}"
                rubrics_text += f"\n Rubric Label: {key}"
            
            # Enhanced evaluation prompt that accounts for placeholder responses
            evaluation_prompt = f"""
You are evaluating a student's responses to a manufacturing problem-solving exercise.

CASE STUDY:
{case_study}

STUDENT RESPONSES:
{responses_text}

EVALUATION RUBRICS:
{rubrics_text}

IMPORTANT EVALUATION GUIDELINES:
- If a response starts with "[No response provided for:", this means the student left this question blank
- For blank responses, assign scores based on the overall quality of other responses, but generally score lower (3-5 range)
- For substantive responses, evaluate based on the rubric criteria (1-10 scale)
- Consider the overall effort and engagement across all questions
- Provide constructive feedback that addresses both answered and unanswered questions

Evaluate this student's performance across all rubric dimensions. Each score should be between 1-10.

Provide your evaluation as JSON in this exact format:
{{
    "scores": {{
        "{list(part['rubrics'].keys())[0]}": score,
        "{list(part['rubrics'].keys())[1] if len(part['rubrics']) > 1 else list(part['rubrics'].keys())[0]}": score,
        "{list(part['rubrics'].keys())[2] if len(part['rubrics']) > 2 else list(part['rubrics'].keys())[0]}": score
    }},
    "feedback": "Detailed constructive feedback addressing both strengths and areas for improvement, including guidance on unanswered questions"
}}

Respond only with valid JSON.
            """
            
            # Generate evaluation with retry logic
            max_retries = 3
            evaluation_data = None
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[evaluation_prompt],
                        config = genai.types.GenerateContentConfig(
                            thinking_config=genai.types.ThinkingConfig(thinking_budget=0)
                        )
                    )
                    text = response.text
                    print(text)
                    # Clean and parse JSON
                    cleaned_text = text.replace("```json", "").replace("```", "").strip()
                    # Remove any text before the first { or after the last }
                    start_idx = cleaned_text.find('{')
                    end_idx = cleaned_text.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        cleaned_text = cleaned_text[start_idx:end_idx]
                    
                    evaluation_data = json.loads(cleaned_text)
                    
                    # Validate response structure
                    required_keys = ["scores", "feedback"]
                    if not all(key in evaluation_data for key in required_keys):
                        raise ValueError("Missing required keys in evaluation response")
                    
                    # Validate scores are numeric and in range, convert to float
                    for rubric_key in part["rubrics"].keys():
                        if rubric_key not in evaluation_data["scores"]:
                            raise ValueError(f"Missing score for rubric: {rubric_key}")
                        score = evaluation_data["scores"][rubric_key]
                        if not isinstance(score, (int, float)) or not (1 <= score <= 10):
                            raise ValueError(f"Invalid score for {rubric_key}: {score}")
                        # Ensure score is a float for consistency
                        evaluation_data["scores"][rubric_key] = float(score)
                    
                    break
                    
                except (json.JSONDecodeError, ValueError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Evaluation attempt {attempt + 1} failed: {e}")
                        continue
                    else:
                        logger.error(f"All evaluation attempts failed: {e}")
                        raise e
            
            # Fallback response if all attempts failed
            if evaluation_data is None:
                evaluation_data = {
                    "scores": {key: 5 for key in part["rubrics"].keys()},
                    "feedback": "Your submission has been received. Some questions may not have been fully answered, which affects the evaluation. Please ensure you provide detailed responses to all questions for the best assessment. You may continue to the next part.",
                    "canProceed": True
                }

        # Calculate average score
        average_score = calculate_average_score(evaluation_data["scores"])
        
        # Determine if student can proceed
        can_proceed = True  # average_score >= part["passingScore"]
        evaluation_data["canProceed"] = can_proceed

        # Store evaluation in database
        evaluation_record = {
            "session_id": request.sessionId,
            "part_id": request.partId,
            "scores": evaluation_data["scores"],
            "feedback": evaluation_data["feedback"],
            "can_proceed": can_proceed,
            "average_score": average_score,
            "transcription": evaluation_data.get("transcription", None)
        }
        supabase.table("part_evaluations").insert(evaluation_record).execute()
        
        # Update session completed_parts and last_activity
        completed_parts = session.get("completed_parts", [])
        if request.partId not in completed_parts:
            completed_parts.append(request.partId)
        
        from datetime import timezone
        supabase.table("sessions").update({
            "completed_parts": completed_parts,
            "last_activity": datetime.now(timezone.utc).isoformat()
        }).eq("session_id", request.sessionId).execute()
        
        # Determine next part
        next_part_id = None
        if can_proceed and request.partId < len(EVALUATION_PARTS):
            next_part_id = request.partId + 1

        try:
            return PartEvaluationResponse(
                partId=request.partId,
                scores=evaluation_data["scores"],
                feedback=evaluation_data["feedback"],
                canProceed=can_proceed,
                averageScore=average_score,
                nextPartId=next_part_id,
                transcription=evaluation_data.get("transcription", None)
            )
        except Exception as validation_error:
            logger.error(f"Validation error in part evaluation response: {validation_error}")
            # Fallback response with guaranteed valid data types
            fallback_scores = {key: float(5.0) for key in part["rubrics"].keys()}
            fallback_average = 5.0
            
            # Store fallback evaluation in database
            try:
                fallback_evaluation = {
                    "session_id": request.sessionId,
                    "part_id": request.partId,
                    "scores": fallback_scores,
                    "feedback": "Your submission has been received and evaluated. Some technical issues occurred during detailed analysis, but your responses show engagement with the problem-solving process. You may continue to the next part.",
                    "can_proceed": True,
                    "average_score": fallback_average,
                    "transcription": evaluation_data.get("transcription", None) if 'evaluation_data' in locals() else None
                }
                supabase.table("part_evaluations").insert(fallback_evaluation).execute()
                
                # Update session completed_parts
                session = get_session_from_db(request.sessionId)
                completed_parts = session.get("completed_parts", [])
                if request.partId not in completed_parts:
                    completed_parts.append(request.partId)
                
                from datetime import timezone
                supabase.table("sessions").update({
                    "completed_parts": completed_parts,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                }).eq("session_id", request.sessionId).execute()
                
            except Exception as db_error:
                logger.error(f"Database fallback error: {db_error}")
            
            fallback_next_part_id = request.partId + 1 if request.partId < len(EVALUATION_PARTS) else None
            
            return PartEvaluationResponse(
                partId=request.partId,
                scores=fallback_scores,
                feedback="Your submission has been received and evaluated. Some technical issues occurred during detailed analysis, but your responses show engagement with the problem-solving process. You may continue to the next part.",
                canProceed=True,
                averageScore=fallback_average,
                nextPartId=fallback_next_part_id,
                transcription=evaluation_data.get("transcription", None) if 'evaluation_data' in locals() else None
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_part: {e}")
        
        # Emergency fallback: ensure part is marked as completed even in error scenarios
        # This prevents the final evaluation from failing due to missing parts
        try:
            session = get_session_from_db(request.sessionId)
            if session:
                completed_parts = session.get("completed_parts", [])
                if request.partId not in completed_parts:
                    completed_parts.append(request.partId)
                    from datetime import timezone
                    supabase.table("sessions").update({
                        "completed_parts": completed_parts,
                        "last_activity": datetime.now(timezone.utc).isoformat()
                    }).eq("session_id", request.sessionId).execute()
                    logger.warning(f"Emergency completion marking for part {request.partId} due to error: {e}")
        except Exception as emergency_error:
            logger.error(f"Emergency fallback failed: {emergency_error}")
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# New function to evaluate audio responses
async def evaluate_audio_response(audio_data: str, case_study: str):
    """Evaluate audio response using Gemini AI with actual audio analysis"""
    try:
        import base64
        import tempfile
        import os
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            # Create comprehensive audio evaluation prompt
            audio_prompt = f"""
You are evaluating a 2-minute verbal explanation from a candidate solving a manufacturing problem.

ORIGINAL CASE STUDY:
{case_study}

INSTRUCTIONS:
1. First, provide a transcription of the audio
2. Then evaluate the candidate's verbal explanation based on the criteria below

EVALUATION CRITERIA (score 1-10 for each):
1. communication_clarity: How clearly and effectively did they communicate their approach and insights?
2. synthesis_ability: How well did they synthesize and connect insights across all parts of the analysis?
3. professional_presentation: Did they demonstrate professional communication skills and confidence?
4. depth_of_understanding: How well did they demonstrate deep understanding of manufacturing problem-solving?

EVALUATION FOCUS:
- Assess the logical flow and structure of their explanation
- Evaluate their ability to summarize key insights from their analysis
- Consider their communication style and professionalism
- Judge their depth of understanding of manufacturing concepts
- Note any specific examples or frameworks they reference

Provide your evaluation in this exact JSON format:
{{
    "transcription": "Full transcription of what the candidate said",
    "scores": {{
        "communication_clarity": score,
        "synthesis_ability": score,
        "professional_presentation": score,
        "depth_of_understanding": score
    }},
    "feedback": "Detailed feedback about their verbal presentation, communication style, synthesis ability, and demonstrated understanding. Include specific observations from their transcribed content."
}}

Respond only with valid JSON.
            """
            audio_part = genai.types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/mp3',
            )
            # Generate content with audio
            response = client.models.generate_content(
                model=model_name,
                contents=[audio_prompt, audio_part],
                config = genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=0)
                )
            )
            
            
            # Parse response
            text = response.text
            cleaned_text = text.replace("```json", "").replace("```", "").strip()
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                cleaned_text = cleaned_text[start_idx:end_idx]
            
            evaluation_data = json.loads(cleaned_text)
            
            # Validate response structure
            required_keys = ["scores", "feedback"]
            if not all(key in evaluation_data for key in required_keys):
                raise ValueError("Missing required keys in evaluation response")
            
            # Log transcription for debugging
            if "transcription" in evaluation_data:
                logger.info(f"Audio transcription: {evaluation_data['transcription'][:200]}...")
            
            return {
                "scores": evaluation_data["scores"],
                "feedback": evaluation_data["feedback"],
                "transcription": evaluation_data.get("transcription", "Transcription not available")
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                
    except Exception as e:
        logger.error(f"Error in audio evaluation: {e}")
        # Enhanced fallback with more realistic scores
        return {
            "scores": {
                "communication_clarity": 2,
                "synthesis_ability": 2,
                "professional_presentation": 2,
                "depth_of_understanding": 2
            },
            "feedback": "Thank you for completing the verbal explanation. Your audio submission has been received and evaluated. The recording demonstrates your engagement with the problem-solving process. To improve future presentations, focus on clearly articulating your analytical approach, connecting insights across different parts of your analysis, and speaking with confidence about your manufacturing knowledge.",
            "transcription": "Audio processing unavailable - technical evaluation used"
        }

def map_weaknesses_to_tools(overall_scores, part_evaluations):
    """Map student weaknesses to specific quality management tools from promptforcasestudy.md"""
    
    # Quality Management Tools Knowledge Base
    tools_knowledge_base = {
        "QFD (Quality Function Deployment)": {
            "description": "Translates customer requirements into technical specifications and helps prioritize design decisions.",
            "addresses": "Customer requirement analysis, stakeholder management, systematic requirement prioritization",
            "when_to_use": "When struggling with data gathering, stakeholder identification, or understanding customer needs",
            "key_skills": ["CTQ identification", "Customer-specification matrix", "Stakeholder analysis"]
        },
        "DFMEA (Design Failure Mode and Effect Analysis)": {
            "description": "Systematic method for evaluating design-related failure modes and their effects before production.",
            "addresses": "Risk assessment, systematic thinking, solution prioritization, design robustness",
            "when_to_use": "When weak in systematic analysis, risk assessment, or solution development",
            "key_skills": ["RPN calculation", "Risk prioritization", "Design for assembly"]
        },
        "PFMEA (Process Failure Mode and Effect Analysis)": {
            "description": "Identifies and evaluates potential failure modes in manufacturing processes.",
            "addresses": "Process analysis, implementation planning, prevention strategies, detection improvement",
            "when_to_use": "When struggling with implementation planning, process understanding, or practical application",
            "key_skills": ["Poka Yoke implementation", "Detection improvement", "Man-Machine-Material-Method analysis"]
        },
        "7QC Tools": {
            "description": "Seven fundamental quality control tools for data analysis and problem-solving.",
            "addresses": "Data collection, systematic analysis, root cause identification, statistical thinking",
            "when_to_use": "When needing better data analysis skills, systematic problem-solving, or measurement approaches",
            "key_skills": ["Check sheets", "Pareto analysis", "Fishbone diagrams", "Control charts", "Histograms"]
        },
        "Why-Why Analysis (5 Whys)": {
            "description": "Iterative questioning technique to explore cause-and-effect relationships underlying problems.",
            "addresses": "Root cause drilling, systematic investigation, logical reasoning, deeper analysis",
            "when_to_use": "When root cause analysis is superficial or lacks depth in investigation",
            "key_skills": ["Root cause drilling", "Systematic issue recognition", "Logical questioning"]
        },
        "5S Methodology": {
            "description": "Workplace organization method focused on efficiency, safety, and standardization.",
            "addresses": "Workplace organization, sustainability planning, standardization, continuous improvement",
            "when_to_use": "When weak in sustainability planning, implementation structure, or workplace organization",
            "key_skills": ["Sort, Set in order, Shine, Standardize, Sustain", "Workplace organization", "Standard operating procedures"]
        }
    }
    
    # Analyze weaknesses and map to tools
    recommendations = {}
    
    # Check overall scores for patterns
    weak_areas = []
    for area, score in overall_scores.items():
        if score < 6:  # Consider scores below 6 as weak areas
            weak_areas.append(area)
    
    # Specific mapping logic based on evaluation criteria
    if "analytical_thinking" in weak_areas:
        recommendations["7QC Tools"] = {
            "reason": "Your analytical thinking could be strengthened with structured data analysis tools",
            "specific_benefit": tools_knowledge_base["7QC Tools"]["addresses"],
            "priority": "High"
        }
        recommendations["Why-Why Analysis (5 Whys)"] = {
            "reason": "Develop deeper analytical skills through systematic questioning techniques",
            "specific_benefit": tools_knowledge_base["Why-Why Analysis (5 Whys)"]["addresses"],
            "priority": "Medium"
        }
    
    if "problem_solving" in weak_areas:
        recommendations["DFMEA (Design Failure Mode and Effect Analysis)"] = {
            "reason": "Enhance systematic problem-solving and risk assessment capabilities",
            "specific_benefit": tools_knowledge_base["DFMEA (Design Failure Mode and Effect Analysis)"]["addresses"],
            "priority": "High"
        }
        recommendations["7QC Tools"] = {
            "reason": "Build foundational problem-solving skills with structured quality tools",
            "specific_benefit": tools_knowledge_base["7QC Tools"]["addresses"],
            "priority": "Medium"
        }
    
    if "systematic_approach" in weak_areas:
        recommendations["QFD (Quality Function Deployment)"] = {
            "reason": "Learn systematic requirement analysis and stakeholder management",
            "specific_benefit": tools_knowledge_base["QFD (Quality Function Deployment)"]["addresses"],
            "priority": "High"
        }
        recommendations["DFMEA (Design Failure Mode and Effect Analysis)"] = {
            "reason": "Develop structured risk assessment and analysis methodologies",
            "specific_benefit": tools_knowledge_base["DFMEA (Design Failure Mode and Effect Analysis)"]["addresses"],
            "priority": "Medium"
        }
    
    if "practical_application" in weak_areas:
        recommendations["PFMEA (Process Failure Mode and Effect Analysis)"] = {
            "reason": "Strengthen practical implementation and process analysis skills",
            "specific_benefit": tools_knowledge_base["PFMEA (Process Failure Mode and Effect Analysis)"]["addresses"],
            "priority": "High"
        }
        recommendations["5S Methodology"] = {
            "reason": "Learn practical workplace organization and implementation sustainability",
            "specific_benefit": tools_knowledge_base["5S Methodology"]["addresses"],
            "priority": "Medium"
        }
    
    if "communication_skills" in weak_areas:
        recommendations["QFD (Quality Function Deployment)"] = {
            "reason": "Improve stakeholder communication and requirement gathering skills",
            "specific_benefit": tools_knowledge_base["QFD (Quality Function Deployment)"]["addresses"],
            "priority": "Medium"
        }
    
    # Check part-specific weaknesses
    for part_eval in part_evaluations:
        part_id = part_eval["partId"]
        avg_score = part_eval["averageScore"]
        
        if avg_score < 6:
            if part_id == 1:  # Problem Identification & Data Gathering
                recommendations["QFD (Quality Function Deployment)"] = {
                    "reason": "Improve data gathering and stakeholder identification skills",
                    "specific_benefit": "CTQ identification, stakeholder analysis, systematic requirement gathering",
                    "priority": "High"
                }
                recommendations["7QC Tools"] = {
                    "reason": "Learn systematic data collection and analysis methods",
                    "specific_benefit": "Check sheets, data organization, systematic observation",
                    "priority": "Medium"
                }
            
            elif part_id == 2:  # Root Cause Analysis
                recommendations["Why-Why Analysis (5 Whys)"] = {
                    "reason": "Strengthen root cause analysis depth and systematic investigation",
                    "specific_benefit": "Root cause drilling, systematic issue recognition, logical questioning",
                    "priority": "High"
                }
                recommendations["7QC Tools"] = {
                    "reason": "Learn fishbone diagrams and other root cause analysis tools",
                    "specific_benefit": "Fishbone analysis, Pareto analysis, systematic cause identification",
                    "priority": "Medium"
                }
            
            elif part_id == 3:  # Solution Development
                recommendations["DFMEA (Design Failure Mode and Effect Analysis)"] = {
                    "reason": "Enhance solution evaluation and risk assessment skills",
                    "specific_benefit": "Risk prioritization, systematic solution evaluation, RPN calculation",
                    "priority": "High"
                }
                recommendations["PFMEA (Process Failure Mode and Effect Analysis)"] = {
                    "reason": "Improve practical solution development and implementation planning",
                    "specific_benefit": "Poka Yoke implementation, practical application, error prevention",
                    "priority": "Medium"
                }
            
            elif part_id == 4:  # Implementation & Monitoring
                recommendations["5S Methodology"] = {
                    "reason": "Learn sustainable implementation and workplace organization",
                    "specific_benefit": "Standardization, sustainability planning, continuous improvement",
                    "priority": "High"
                }
                recommendations["PFMEA (Process Failure Mode and Effect Analysis)"] = {
                    "reason": "Develop better monitoring and detection improvement strategies",
                    "specific_benefit": "Detection improvement, process monitoring, systematic implementation",
                    "priority": "Medium"
                }
    
    # If no specific weaknesses identified, provide general recommendations
    if not recommendations:
        recommendations["7QC Tools"] = {
            "reason": "Build foundational quality management skills with fundamental tools",
            "specific_benefit": "Comprehensive quality analysis and problem-solving foundation",
            "priority": "Medium"
        }
        recommendations["QFD (Quality Function Deployment)"] = {
            "reason": "Enhance systematic thinking and customer-focused analysis",
            "specific_benefit": "Stakeholder management and systematic requirement analysis",
            "priority": "Low"
        }
    
    return recommendations

# Get session status endpoint
@app.get("/api/session-status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Get current status of an evaluation session"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    session = get_session_from_db(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    completed_parts = session.get("completed_parts", [])
    current_part = get_current_part(completed_parts)
    
    return SessionStatusResponse(
        sessionId=session_id,
        completedParts=completed_parts,
        currentPart=current_part,
        isComplete=len(completed_parts) >= len(EVALUATION_PARTS),
        createdAt=session["created_at"]
    )

# Debug endpoint to get detailed session information
@app.get("/api/debug/session/{session_id}")
async def debug_session_status(session_id: str):
    """Debug endpoint to get detailed session information"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    session = get_session_from_db(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get responses and evaluations from database
    responses = supabase.table("responses").select("part_id, question_id").eq("session_id", session_id).execute()
    evaluations = supabase.table("part_evaluations").select("part_id").eq("session_id", session_id).execute()
    
    completed_parts = session.get("completed_parts", [])
    
    return {
        "sessionId": session_id,
        "completedParts": completed_parts,
        "totalParts": len(EVALUATION_PARTS),
        "currentPart": get_current_part(completed_parts),
        "isComplete": len(completed_parts) >= len(EVALUATION_PARTS),
        "createdAt": session.get("created_at"),
        "lastActivity": session.get("last_activity"),
        "hasResponses": bool(responses.data),
        "hasEvaluations": bool(evaluations.data),
        "responseCount": len(responses.data) if responses.data else 0,
        "evaluationCount": len(evaluations.data) if evaluations.data else 0,
        "responseParts": list(set([r["part_id"] for r in responses.data])) if responses.data else [],
        "evaluationParts": [e["part_id"] for e in evaluations.data] if evaluations.data else [],
        "sessionKeys": list(session.keys())
    }

# Enhanced final evaluation endpoint
@app.get("/api/final-evaluation/{session_id}", response_model=FinalEvaluationResponse)
async def get_final_evaluation(session_id: str):
    """Get comprehensive evaluation across all completed parts"""
    try:
        if not model_name:
            raise HTTPException(status_code=500, detail="AI model not configured")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")

        session = get_session_from_db(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get all responses and evaluations from database
        responses_result = supabase.table("responses").select("*").eq("session_id", session_id).execute()
        evaluations_result = supabase.table("part_evaluations").select("*").eq("session_id", session_id).execute()
        
        responses_data = responses_result.data if responses_result.data else []
        evaluations_data = evaluations_result.data if evaluations_result.data else []
        
        # Check completeness and create placeholder data if needed
        completed_parts = session.get("completed_parts", [])
        total_parts = len(EVALUATION_PARTS)
        
        if len(completed_parts) < total_parts or len(evaluations_data) < total_parts:
            missing_parts = [i for i in range(1, total_parts + 1) if i not in [e["part_id"] for e in evaluations_data]]
            
            if missing_parts:
                logger.warning(f"Creating placeholder data for missing parts: {missing_parts} in session {session_id}")
                
                for missing_part_id in missing_parts:
                    part = EVALUATION_PARTS[missing_part_id - 1]
                    
                    # Create placeholder responses
                    if missing_part_id == 5:  # Audio part
                        placeholder_response = {
                            "session_id": session_id,
                            "part_id": missing_part_id,
                            "question_id": "q5_verbal",
                            "response_text": "Audio recording not submitted - technical issue detected",
                            "audio_data": None
                        }
                        responses_data.append(placeholder_response)
                    else:  # Text parts
                        for question in part["questions"]:
                            placeholder_response = {
                                "session_id": session_id,
                                "part_id": missing_part_id,
                                "question_id": question["id"],
                                "response_text": "[No response - technical issue during submission]",
                                "audio_data": None
                            }
                            responses_data.append(placeholder_response)
                    
                    # Create placeholder evaluation
                    placeholder_scores = {key: 1.0 for key in part["rubrics"].keys()}
                    placeholder_evaluation = {
                        "session_id": session_id,
                        "part_id": missing_part_id,
                        "scores": placeholder_scores,
                        "feedback": f"Part {missing_part_id} evaluation incomplete due to technical issues. Placeholder scores assigned for final evaluation completion.",
                        "can_proceed": True,
                        "average_score": 1.0,
                        "transcription": None
                    }
                    evaluations_data.append(placeholder_evaluation)
                
                # Update completed parts in database
                supabase.table("sessions").update({
                    "completed_parts": list(range(1, total_parts + 1)),
                    "is_complete": True
                }).eq("session_id", session_id).execute()
                
                logger.info(f"Successfully created placeholder data for session {session_id}")

        # Compile comprehensive data for final evaluation
        all_responses = ""
        all_evaluations = []
        total_score = 0
        total_criteria = 0
        
        # Organize responses by part and question
        responses_by_part = {}
        for response in responses_data:
            part_id = response["part_id"]
            if part_id not in responses_by_part:
                responses_by_part[part_id] = {}
            responses_by_part[part_id][response["question_id"]] = response["response_text"]
        
        # Organize evaluations by part
        evaluations_by_part = {}
        for evaluation in evaluations_data:
            part_id = evaluation["part_id"]
            evaluations_by_part[part_id] = evaluation
        
        for part_id in range(1, len(EVALUATION_PARTS) + 1):
            part = EVALUATION_PARTS[part_id - 1]
            responses = responses_by_part.get(part_id, {})
            evaluation = evaluations_by_part.get(part_id, {})
            
            all_responses += f"\n--- Part {part_id}: {part['title']} ---\n"
            if part_id == 5:
                # Special handling for audio part
                transcription = evaluation.get("transcription", "Audio recording submitted")
                all_responses += f"Verbal Explanation: 2-minute audio recording submitted\n"
                if transcription and transcription != "Audio recording submitted":
                    all_responses += f"Transcription: {transcription}\n\n"
                else:
                    all_responses += "\n"
            else:
                for q in part["questions"]:
                    response = responses.get(q['id'], 'No response')
                    all_responses += f"Q: {q['question']}\nA: {response}\n\n"
            
            # Calculate part scores
            part_scores = evaluation.get("scores", {})
            if part_scores:
                total_score += sum(part_scores.values())
                total_criteria += len(part_scores)
            
            all_evaluations.append({
                "partId": part_id,
                "title": part['title'],
                "scores": part_scores,
                "averageScore": evaluation.get("average_score", calculate_average_score(part_scores)),
                "feedback": evaluation.get("feedback", "")
            })

        overall_average = round(total_score / total_criteria, 1) if total_criteria > 0 else 0

        # Enhanced comprehensive evaluation prompt including verbal component
        prompt = f"""
You are a senior manufacturing consultant providing a comprehensive evaluation of problem-solving capabilities.

EVALUATION SUMMARY:
- Total Questions Answered: {session.get('total_questions', 13)} (including verbal explanation)
- Overall Average Score: {overall_average}/10
- All Parts Completed Successfully (including 2-minute verbal explanation)

ORIGINAL CASE STUDY:
{session["case_study"]}

COMPLETE STUDENT RESPONSES:
{all_responses}

DETAILED PART EVALUATIONS:
{json.dumps(all_evaluations, indent=2)}

COMPREHENSIVE FINAL EVALUATION REQUIRED:

1. Overall Performance Scores (1-10):
   - analytical_thinking: Data gathering, systematic analysis, structured approaches
   - problem_solving: Root cause identification, solution development, creativity  
   - systematic_approach: Use of frameworks, methodical thinking, logical flow
   - practical_application: Real-world feasibility, manufacturing knowledge, implementation focus
   - communication_skills: Verbal explanation clarity, synthesis ability, professional presentation

2. Performance Rating based on overall average:
   - "Excellent" (8.0+): Exceptional manufacturing problem-solving skills with strong communication
   - "Good" (6.5-7.9): Strong competencies with minor gaps
   - "Satisfactory" (5.0-6.4): Adequate skills, needs development
   - "Needs Improvement" (<5.0): Significant skills gaps

3. Detailed Feedback (4-5 sentences):
   - Specific strengths demonstrated across all parts including verbal communication
   - Key areas for improvement with actionable recommendations
   - Overall assessment of manufacturing problem-solving maturity
   - Suggestions for continued development

Note: After this evaluation, the system will automatically map any identified weaknesses to specific quality management tools (QFD, DFMEA, PFMEA, 7QC Tools, Why-Why Analysis, 5S) that can help address those gaps.

Provide realistic, constructive evaluation that accurately reflects demonstrated capabilities including communication skills.

Format as JSON:
{{
    "overallScores": {{
        "analytical_thinking": score,
        "problem_solving": score,
        "systematic_approach": score,
        "practical_application": score,
        "communication_skills": score
    }},
    "detailedFeedback": "comprehensive feedback paragraph",
    "overallPerformance": "performance rating",
}}

Respond only with valid JSON.
        """

        # Generate final evaluation with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config = genai.types.GenerateContentConfig(
                        thinking_config=genai.types.ThinkingConfig(thinking_budget=0)
                    )
                )
                text = response.text

                # Clean and parse JSON
                cleaned_text = text.replace("```json", "").replace("```", "").strip()
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                
                final_data = json.loads(cleaned_text)
                
                # Validate structure and convert scores to floats
                required_keys = ["overallScores", "detailedFeedback", "overallPerformance"]
                if not all(key in final_data for key in required_keys):
                    raise ValueError("Missing required keys in final evaluation")
                
                # Ensure all scores are floats for consistency
                if "overallScores" in final_data:
                    for key, score in final_data["overallScores"].items():
                        if isinstance(score, (int, float)):
                            final_data["overallScores"][key] = float(score)
                
                break
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Final evaluation attempt {attempt + 1} failed: {e}")
                    continue
                else:
                    # Fallback response
                    fallback_scores = {
                        "analytical_thinking": float(min(8.0, max(5.0, overall_average))),
                        "problem_solving": float(min(8.0, max(5.0, overall_average))),
                        "systematic_approach": float(min(7.0, max(5.0, overall_average - 0.5))),
                        "practical_application": float(min(8.0, max(5.0, overall_average))),
                        "communication_skills": float(min(7.0, max(5.0, overall_average)))
                    }
                    final_data = {
                        "overallScores": fallback_scores,
                        "detailedFeedback": f"You completed all parts of the evaluation including the verbal explanation with an overall average of {overall_average}/10, demonstrating solid problem-solving and communication capabilities. Your systematic approach to manufacturing challenges shows good foundational skills. The verbal explanation component added valuable insight into your thought process. Continue developing your analytical depth and practical application of problem-solving frameworks in real manufacturing environments.",
                        "overallPerformance": "Good" if overall_average >= 6.5 else "Satisfactory"
                    }

        # Calculate completion time
        try:
            created_at_str = session["created_at"]
            if isinstance(created_at_str, str):
                # Handle timezone-aware datetime from database
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                if created_at.tzinfo is not None:
                    # If timezone-aware, use timezone-aware now()
                    from datetime import timezone
                    completion_time = datetime.now(timezone.utc) - created_at
                else:
                    # If timezone-naive, use timezone-naive now()
                    completion_time = datetime.now() - created_at
            else:
                # Fallback if not string
                completion_time = timedelta(minutes=30)  # Default assumption
            
            completion_str = f"{int(completion_time.total_seconds() // 60)} minutes"
        except Exception as time_error:
            logger.warning(f"Error calculating completion time: {time_error}")
            completion_str = "30 minutes"  # Fallback value

        # Map weaknesses to tools
        tool_recommendations = map_weaknesses_to_tools(final_data["overallScores"], all_evaluations)
        
        # Store final evaluation in database
        final_evaluation_record = {
            "session_id": session_id,
            "overall_scores": final_data["overallScores"],
            "detailed_feedback": final_data["detailedFeedback"],
            "overall_performance": final_data["overallPerformance"],
            "average_score": overall_average,
            "completion_time": completion_str,
            "tool_recommendations": tool_recommendations
        }
        
        # Check if final evaluation already exists
        existing_final = supabase.table("final_evaluations").select("id").eq("session_id", session_id).execute()
        if existing_final.data:
            # Update existing record
            supabase.table("final_evaluations").update(final_evaluation_record).eq("session_id", session_id).execute()
        else:
            # Insert new record
            supabase.table("final_evaluations").insert(final_evaluation_record).execute()

        # Create response with error handling
        try:
            return FinalEvaluationResponse(
                overallScores=final_data["overallScores"],
                partScores=all_evaluations,
                detailedFeedback=final_data["detailedFeedback"],
                overallPerformance=final_data["overallPerformance"],
                totalQuestions=session.get("total_questions", 13),
                averageScore=overall_average,
                completionTime=completion_str,
                toolRecommendations=tool_recommendations
            )
        except Exception as validation_error:
            logger.error(f"Validation error in final evaluation response: {validation_error}")
            # Fallback response with guaranteed valid data types
            fallback_scores = {
                "analytical_thinking": float(min(8.0, max(5.0, overall_average))),
                "problem_solving": float(min(8.0, max(5.0, overall_average))),
                "systematic_approach": float(min(7.0, max(5.0, overall_average - 0.5))),
                "practical_application": float(min(8.0, max(5.0, overall_average))),
                "communication_skills": float(min(7.0, max(5.0, overall_average)))
            }
            fallback_tool_recommendations = map_weaknesses_to_tools(fallback_scores, all_evaluations)
            
            return FinalEvaluationResponse(
                overallScores=fallback_scores,
                partScores=all_evaluations,
                detailedFeedback=f"You completed all parts of the evaluation including the verbal explanation with an overall average of {overall_average}/10, demonstrating solid problem-solving and communication capabilities. Your systematic approach to manufacturing challenges shows good foundational skills. The verbal explanation component added valuable insight into your thought process. Continue developing your analytical depth and practical application of problem-solving frameworks in real manufacturing environments.",
                overallPerformance="Good" if overall_average >= 6.5 else "Satisfactory",
                totalQuestions=session.get("total_questions", 13),
                averageScore=float(overall_average),
                completionTime=completion_str,
                toolRecommendations=fallback_tool_recommendations
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_final_evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 4000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info") 