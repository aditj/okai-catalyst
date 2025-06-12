from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Configure Google AI
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("Google AI configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Google AI: {e}")
    model = None

# Enhanced Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    analysisText: str

class PartSubmissionRequest(BaseModel):
    partId: int
    responses: Dict[str, str]  # questionId -> response
    sessionId: str

class EvaluationResponse(BaseModel):
    rootCauseScore: int
    solutionScore: int
    feedback: str

class PartEvaluationResponse(BaseModel):
    partId: int
    scores: Dict[str, int]  # rubricId -> score
    feedback: str
    canProceed: bool
    averageScore: float
    nextPartId: Optional[int] = None

class FinalEvaluationResponse(BaseModel):
    overallScores: Dict[str, int]  # Overall scores across all parts
    partScores: List[Dict]  # Individual part scores
    detailedFeedback: str
    overallPerformance: str
    totalQuestions: int
    averageScore: float
    completionTime: str

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

# Enhanced session management with timestamps and cleanup
sessions_data = {}

def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    cutoff_time = datetime.now() - timedelta(hours=24)
    expired_sessions = [
        session_id for session_id, data in sessions_data.items()
        if datetime.fromisoformat(data.get("created_at", "1970-01-01T00:00:00")) < cutoff_time
    ]
    for session_id in expired_sessions:
        del sessions_data[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")

def get_current_part(session_data):
    """Determine the current part based on completed parts"""
    completed = session_data.get("completed_parts", [])
    for part_id in range(1, 5):
        if part_id not in completed:
            return part_id
    return 5  # All parts completed

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
                "minLength": 4
            },
            {
                "id": "q1_stakeholders", 
                "question": "Who are the key people you would interview to gather information about this issue? For each person/role, specify what unique insights they could provide.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q1_observations",
                "question": "What direct observations would you make on the production floor? Describe your observation plan including timing, duration, and specific things to look for.",
                "type": "text",
                "minLength": 4
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
                "minLength": 4
            },
            {
                "id": "q2_method",
                "question": "What structured root cause analysis method would you use (e.g., 5 Whys, Fishbone Diagram, Fault Tree Analysis)? Explain your choice and how you would apply it to this specific problem.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q2_validation",
                "question": "How would you validate which root cause is the actual cause? Describe your testing/validation approach and what evidence you would look for.",
                "type": "text",
                "minLength": 4
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
                "minLength": 4
            },
            {
                "id": "q3_implementation",
                "question": "For your highest-priority solution, create a detailed implementation plan including: key steps, timeline, required resources, responsible parties, and success criteria.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q3_risks",
                "question": "What are the potential risks, challenges, or unintended consequences of your solution? For each risk, propose a mitigation strategy.",
                "type": "text",
                "minLength": 4
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
                "minLength": 4
            },
            {
                "id": "q4_timeline",
                "question": "Create a realistic timeline showing: implementation phases, when you expect to see initial improvements, when to measure full impact, and review checkpoints. Justify your timeframes.",
                "type": "text",
                "minLength": 4
            },
            {
                "id": "q4_sustainability",
                "question": "How would you ensure the solution is sustained long-term? Address: training needs, process standardization, accountability measures, and continuous improvement mechanisms.",
                "type": "text",
                "minLength": 4
            }
        ],
        "rubrics": {
            "measurement_focus": "Did they identify appropriate leading and lagging indicators for success?",
            "realistic_timeline": "Is their timeline realistic with proper justification for timeframes?",
            "sustainability": "How well did they address long-term sustainability and continuous improvement?"
        },
        "passingScore": 5.0
    }
]

# Health check endpoint with enhanced info
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with system status"""
    cleanup_old_sessions()  # Clean up old sessions on health check
    return HealthResponse(
        message="Catalyst Backend API is running!",
        activeSessionsCount=len(sessions_data),
        version="2.0.0"
    )

# Enhanced multi-part case study generation
@app.get("/api/generate-multipart-case", response_model=MultiPartCaseStudyResponse)
async def generate_multipart_case():
    """Generate a comprehensive manufacturing case study for multi-part evaluation"""
    try:
        cleanup_old_sessions()  # Clean up before creating new session
        
        if not model:
            raise HTTPException(status_code=500, detail="AI model not configured")
        
        # Enhanced case study generation prompt
        prompt = """
You are a senior manufacturing process expert. Create a realistic, complex manufacturing case study that will challenge problem-solving skills across multiple dimensions.

Write a case study (200-250 words) about a significant operational problem in a modern manufacturing facility.

The problem should involve multiple interconnected issues such as:
- Quality defects with unclear root causes
- Production inefficiencies or bottlenecks
- Equipment reliability issues
- Process control problems
- Supply chain or material issues
- Worker safety or ergonomic concerns
- Cost overruns or waste

Requirements:
- Start with "Case Study: [Descriptive Title]"
- Include specific, realistic data (percentages, quantities, timeframes, costs)
- Mention multiple departments/stakeholders affected
- Include both immediate symptoms and underlying issues
- Provide enough complexity to support 4-part analysis (data gathering, root cause analysis, solution development, implementation)
- Do NOT include any solutions or hints about causes
- End with "Your task is to analyze this problem systematically through a structured approach."

Make it realistic for a mid-to-large manufacturing operation with modern equipment and processes.
        """

        # Generate response with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
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
                    raise e

        # Generate session ID and initialize session
        session_id = str(uuid.uuid4())
        
        # Initialize enhanced session data
        sessions_data[session_id] = {
            "case_study": case_study,
            "completed_parts": [],
            "responses": {},
            "part_evaluations": {},
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "total_questions": sum(len(part["questions"]) for part in EVALUATION_PARTS)
        }

        return MultiPartCaseStudyResponse(
            caseStudy=case_study,
            sessionId=session_id,
            parts=EVALUATION_PARTS,
            totalParts=len(EVALUATION_PARTS),
            estimatedTime="30-45 minutes"
        )

    except Exception as e:
        logger.error(f"Error in generate_multipart_case: {e}")
        
        # Enhanced fallback case study
        fallback_case_study = (
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
        
        # Generate session ID for fallback
        session_id = str(uuid.uuid4())
        sessions_data[session_id] = {
            "case_study": fallback_case_study,
            "completed_parts": [],
            "responses": {},
            "part_evaluations": {},
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "total_questions": sum(len(part["questions"]) for part in EVALUATION_PARTS)
        }
        
        return MultiPartCaseStudyResponse(
            caseStudy=fallback_case_study,
            sessionId=session_id,
            parts=EVALUATION_PARTS,
            totalParts=len(EVALUATION_PARTS),
            estimatedTime="30-45 minutes"
        )

# Enhanced part submission with improved validation and AI evaluation
@app.post("/api/submit-part", response_model=PartEvaluationResponse)
async def submit_part(request: PartSubmissionRequest):
    """Submit responses for a specific part with enhanced validation and evaluation"""
    try:
        # Validate session exists
        if request.sessionId not in sessions_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        if not model:
            raise HTTPException(status_code=500, detail="AI model not configured")

        session = sessions_data[request.sessionId]
        part = next((p for p in EVALUATION_PARTS if p["id"] == request.partId), None)
        
        if not part:
            raise HTTPException(status_code=400, detail="Invalid part ID")

        # Check if part already completed
        if request.partId in session["completed_parts"]:
            raise HTTPException(status_code=400, detail="Part already completed")

        # Validate required responses
        missing_questions = validate_part_responses(part, request.responses)
        if missing_questions:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing or empty responses for: {', '.join(missing_questions)}"
            )

        # Validate minimum response lengths
        for question in part["questions"]:
            response_text = request.responses.get(question["id"], "").strip()
            min_length = question.get("minLength", 50)
            if len(response_text) < min_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Response to '{question['question'][:50]}...' is too short. Minimum {min_length} characters required."
                )

        # Update session activity
        session["last_activity"] = datetime.now().isoformat()
        session["responses"][str(request.partId)] = request.responses
        
        # Create enhanced evaluation prompt
        case_study = session["case_study"]
        responses_text = ""
        for i, question in enumerate(part["questions"], 1):
            response = request.responses.get(question["id"], "No response")
            responses_text += f"\nQuestion {i}: {question['question']}\nStudent Response: {response}\n"
        
        rubrics_text = ""
        for key, description in part["rubrics"].items():
            rubrics_text += f"\n Rubric Text:  {key.replace('_', ' ').title()}: {description}"
            rubrics_text += f"\n Rubric Label: {key}"
        
        prompt = f"""
You are an expert Operational Excellence consultant with 20+ years of experience evaluating manufacturing problem-solving capabilities.

EVALUATION CONTEXT:
Part {request.partId}: {part['title']}

ORIGINAL CASE STUDY:
{case_study}

STUDENT RESPONSES:
{responses_text}

EVALUATION CRITERIA (Score 1-10 for each):
{rubrics_text}

EVALUATION INSTRUCTIONS:
0. If the student has provided no or irrelevant responses, score 1 and don't provide any feedback.
1. Score each criterion on a 1-10 scale where:
   - 1-3: Poor (lacks understanding, minimal effort, unrealistic)
   - 4-5: Below Average (basic understanding, limited depth)
   - 6-7: Good (solid understanding, practical approach)
   - 8-9: Excellent (comprehensive, insightful, well-structured)
   - 10: Outstanding (exceptional insight, innovative thinking)

2. Consider:
   - Depth and quality of responses
   - Practical applicability to manufacturing
   - Use of structured thinking approaches
   - Specificity and detail level
   - Realistic understanding of manufacturing operations

3. Student can proceed if average score ≥ {part['passingScore']}

4. Provide constructive feedback (2-3 sentences) that:
   - Highlights specific strengths
   - Identifies specific areas for improvement
   - Offers actionable suggestions

   MAKE SURE THE CRITERIA ARE LABELLED EXACTLY AS THEY ARE IN THE PROMPT. DO NOT MAKE ANY CHANGES TO THE CRITERIA NAME INCLUDING REMOVING THE DASHES.
Format as JSON:
{{
    "scores": {{"criterion1": score, "criterion2": score, ...}},
    "feedback": "detailed constructive feedback"
}}

Respond only with valid JSON, no additional text.
        """
        print(prompt)
        # Generate evaluation with retry logic
        max_retries = 3
        evaluation_data = None
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
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
                
                # Validate scores are numeric and in range
                for rubric_key in part["rubrics"].keys():
                    if rubric_key not in evaluation_data["scores"]:
                        raise ValueError(f"Missing score for rubric: {rubric_key}")
                    score = evaluation_data["scores"][rubric_key]
                    if not isinstance(score, (int, float)) or not (1 <= score <= 10):
                        raise ValueError(f"Invalid score for {rubric_key}: {score}")
                
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
                "scores": {key: 6 for key in part["rubrics"].keys()},
                "feedback": "Technical evaluation issue encountered. Your responses show good understanding. Please continue to the next part.",
                "canProceed": True
            }

        # Calculate average score
        average_score = calculate_average_score(evaluation_data["scores"])
        
        # Determine if student can proceed
        can_proceed = True#average_score >= part["passingScore"]
        evaluation_data["canProceed"] = can_proceed

        # Store evaluation
        session["part_evaluations"][str(request.partId)] = evaluation_data
        
        # Update completed parts if student can proceed
        next_part_id = None
        if can_proceed:
            session["completed_parts"].append(request.partId)
            if request.partId < len(EVALUATION_PARTS):
                next_part_id = request.partId + 1

        return PartEvaluationResponse(
            partId=request.partId,
            scores=evaluation_data["scores"],
            feedback=evaluation_data["feedback"],
            canProceed=can_proceed,
            averageScore=average_score,
            nextPartId=next_part_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_part: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get session status endpoint
@app.get("/api/session-status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Get current status of an evaluation session"""
    if session_id not in sessions_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_data[session_id]
    current_part = get_current_part(session)
    
    return SessionStatusResponse(
        sessionId=session_id,
        completedParts=session["completed_parts"],
        currentPart=current_part,
        isComplete=len(session["completed_parts"]) >= len(EVALUATION_PARTS),
        createdAt=session["created_at"]
    )

# Enhanced final evaluation endpoint
@app.get("/api/final-evaluation/{session_id}", response_model=FinalEvaluationResponse)
async def get_final_evaluation(session_id: str):
    """Get comprehensive evaluation across all completed parts"""
    try:
        if session_id not in sessions_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        if not model:
            raise HTTPException(status_code=500, detail="AI model not configured")

        session = sessions_data[session_id]
        
        if len(session["completed_parts"]) < len(EVALUATION_PARTS):
            raise HTTPException(status_code=400, detail="Not all parts completed")

        # Compile comprehensive data for final evaluation
        all_responses = ""
        all_evaluations = []
        total_score = 0
        total_criteria = 0
        
        for part_id in range(1, len(EVALUATION_PARTS) + 1):
            part = EVALUATION_PARTS[part_id - 1]
            responses = session["responses"].get(str(part_id), {})
            evaluation = session["part_evaluations"].get(str(part_id), {})
            
            all_responses += f"\n--- Part {part_id}: {part['title']} ---\n"
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
                "averageScore": calculate_average_score(part_scores),
                "feedback": evaluation.get("feedback", "")
            })

        overall_average = round(total_score / total_criteria, 1) if total_criteria > 0 else 0

        # Enhanced comprehensive evaluation prompt
        prompt = f"""
You are a senior manufacturing consultant providing a comprehensive evaluation of problem-solving capabilities.

EVALUATION SUMMARY:
- Total Questions Answered: {session.get('total_questions', 12)}
- Overall Average Score: {overall_average}/10
- All Parts Completed Successfully

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

2. Performance Rating based on overall average:
   - "Excellent" (8.0+): Exceptional manufacturing problem-solving skills
   - "Good" (6.5-7.9): Strong competencies with minor gaps
   - "Satisfactory" (5.0-6.4): Adequate skills, needs development
   - "Needs Improvement" (<5.0): Significant skills gaps

3. Detailed Feedback (4-5 sentences):
   - Specific strengths demonstrated across all parts
   - Key areas for improvement with actionable recommendations
   - Overall assessment of manufacturing problem-solving maturity
   - Suggestions for continued development

Provide realistic, constructive evaluation that accurately reflects demonstrated capabilities.

Format as JSON:
{{
    "overallScores": {{
        "analytical_thinking": score,
        "problem_solving": score,
        "systematic_approach": score,
        "practical_application": score
    }},
    "detailedFeedback": "comprehensive feedback paragraph",
    "overallPerformance": "performance rating"
}}

Respond only with valid JSON.
        """

        # Generate final evaluation with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                text = response.text

                # Clean and parse JSON
                cleaned_text = text.replace("```json", "").replace("```", "").strip()
                start_idx = cleaned_text.find('{')
                end_idx = cleaned_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                
                final_data = json.loads(cleaned_text)
                
                # Validate structure
                required_keys = ["overallScores", "detailedFeedback", "overallPerformance"]
                if not all(key in final_data for key in required_keys):
                    raise ValueError("Missing required keys in final evaluation")
                
                break
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Final evaluation attempt {attempt + 1} failed: {e}")
                    continue
                else:
                    # Fallback response
                    final_data = {
                        "overallScores": {
                            "analytical_thinking": min(8, max(5, int(overall_average))),
                            "problem_solving": min(8, max(5, int(overall_average))),
                            "systematic_approach": min(7, max(5, int(overall_average - 0.5))),
                            "practical_application": min(8, max(5, int(overall_average)))
                        },
                        "detailedFeedback": f"You completed all parts of the evaluation with an overall average of {overall_average}/10, demonstrating solid problem-solving capabilities. Your systematic approach to manufacturing challenges shows good foundational skills. Continue developing your analytical depth and practical application of problem-solving frameworks in real manufacturing environments.",
                        "overallPerformance": "Good" if overall_average >= 6.5 else "Satisfactory"
                    }

        # Calculate completion time
        created_at = datetime.fromisoformat(session["created_at"])
        completion_time = datetime.now() - created_at
        completion_str = f"{int(completion_time.total_seconds() // 60)} minutes"

        return FinalEvaluationResponse(
            overallScores=final_data["overallScores"],
            partScores=all_evaluations,
            detailedFeedback=final_data["detailedFeedback"],
            overallPerformance=final_data["overallPerformance"],
            totalQuestions=session.get("total_questions", 12),
            averageScore=overall_average,
            completionTime=completion_str
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_final_evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Legacy endpoints for backward compatibility
@app.get("/api/generate-case", response_model=CaseStudyResponse)
async def generate_case():
    """Generate a new manufacturing case study using AI (legacy endpoint)"""
    try:
        if not model:
            raise HTTPException(status_code=500, detail="AI model not configured")
        
        # Create the case study generation prompt
        prompt = """
You are a manufacturing process expert. Write a short, single-paragraph case study (about 100 words) about a common operational problem in a factory. 

The problem could be about:
- Quality defects or control issues
- Production delays or bottlenecks
- Safety incidents or concerns  
- Equipment malfunctions or maintenance
- Material waste or cost overruns
- Process inefficiencies

Format: Start with "Case Study: [Brief Title]." then continue with the problem description.

Requirements:
- Make it realistic and specific to manufacturing
- Include some data or metrics (percentages, numbers, timeframes)
- Do NOT include the solution - only describe the problem
- End with "Your task is to analyze this problem."

Please provide only the case study text without any additional formatting or explanation.
        """

        # Generate response
        response = model.generate_content(prompt)
        case_study = response.text.strip()

        return CaseStudyResponse(caseStudy=case_study)

    except Exception as e:
        logger.error(f"Error in generate_case: {e}")
        
        # Fallback case study if API fails
        fallback_case_study = (
            "Case Study: Unexplained Defects on Assembly Line 3. For the past week, "
            "the final quality check on Assembly Line 3 has seen a 15% increase in "
            "product defects. The defects are minor scratches on the product housing. "
            "This is causing rework delays and increasing material waste. Your task is "
            "to analyze this problem."
        )
        
        return CaseStudyResponse(caseStudy=fallback_case_study)

# Legacy evaluation endpoint
@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_analysis(request: AnalysisRequest):
    """Evaluate user's manufacturing problem analysis using AI (legacy endpoint)"""
    try:
        if not request.analysisText or request.analysisText.strip() == "":
            raise HTTPException(status_code=400, detail="Analysis text is required")
        
        if not model:
            raise HTTPException(status_code=500, detail="AI model not configured")

        # Create the evaluation prompt
        prompt = f"""
You are an expert Operational Excellence consultant. Evaluate the following problem analysis from a manufacturing manager.

Based on the analysis below, provide a score out of 10 for "Root Cause Identification" and a score out of 10 for "Solution Practicality".
Also, provide a short paragraph of constructive feedback (2-3 sentences).

Scoring Criteria:
- Root Cause Identification (1-10): How well did they identify the actual root cause vs just symptoms? Did they use structured thinking (5W, Fishbone, etc.)?
- Solution Practicality (1-10): Are the proposed solutions realistic, cost-effective, and directly address the root cause?

Format your response as a JSON object with three keys: "rootCauseScore", "solutionScore", and "feedback".

Here is the manager's analysis:
"{request.analysisText}"

Please provide only the JSON response without any additional text or formatting.
        """

        # Generate response
        response = model.generate_content(prompt)
        text = response.text

        # Try to parse the JSON response
        try:
            # Clean the response text to extract JSON
            cleaned_text = text.replace("```json", "").replace("```", "").strip()
            evaluation_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {text}")
            # Fallback response if JSON parsing fails
            evaluation_data = {
                "rootCauseScore": 5,
                "solutionScore": 5,
                "feedback": "Unable to fully evaluate the analysis at this time. Please try again with a more detailed response."
            }

        # Validate the response structure
        if not all(key in evaluation_data for key in ["rootCauseScore", "solutionScore", "feedback"]):
            raise ValueError("Invalid evaluation structure received from LLM")

        # Ensure scores are within valid range
        root_cause_score = max(1, min(10, int(evaluation_data["rootCauseScore"])))
        solution_score = max(1, min(10, int(evaluation_data["solutionScore"])))
        feedback = str(evaluation_data["feedback"])

        return EvaluationResponse(
            rootCauseScore=root_cause_score,
            solutionScore=solution_score,
            feedback=feedback
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in evaluate_analysis: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error during evaluation: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 