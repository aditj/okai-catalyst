from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Supabase client
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    logger.error(f"Failed to configure Supabase for dashboard: {e}")
    supabase = None

# Create router
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Initialize templates
templates = Jinja2Templates(directory="templates")

@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard home page with overview analytics"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get overview statistics
        stats = await get_dashboard_stats()
        
        return templates.TemplateResponse("dashboard/home.html", {
            "request": request,
            "stats": stats,
            "page_title": "HR Analytics Dashboard"
        })
    except Exception as e:
        logger.error(f"Error loading dashboard home: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")

@dashboard_router.get("/sessions", response_class=HTMLResponse)
async def dashboard_sessions(request: Request):
    """View all evaluation sessions with filters"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get all sessions with basic info
        sessions = supabase.table("sessions").select(
            "session_id, created_at, last_activity, is_complete, completed_parts"
        ).order("created_at", desc=True).execute()
        
        # Get final evaluations for completed sessions
        final_evals = supabase.table("final_evaluations").select(
            "session_id, overall_performance, average_score"
        ).execute()
        
        # Combine data
        sessions_data = []
        final_eval_dict = {fe["session_id"]: fe for fe in (final_evals.data or [])}
        
        for session in (sessions.data or []):
            session_data = {
                "session_id": session["session_id"],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "is_complete": session["is_complete"],
                "completed_parts_count": len(session.get("completed_parts", [])),
                "duration_minutes": calculate_duration_minutes(session["created_at"], session["last_activity"]),
                "final_evaluation": final_eval_dict.get(session["session_id"])
            }
            sessions_data.append(session_data)
        
        return templates.TemplateResponse("dashboard/sessions.html", {
            "request": request,
            "sessions": sessions_data,
            "page_title": "Evaluation Sessions"
        })
    except Exception as e:
        logger.error(f"Error loading sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to load sessions")

@dashboard_router.get("/session/{session_id}", response_class=HTMLResponse)
async def dashboard_session_detail(request: Request, session_id: str):
    """Detailed view of a specific evaluation session"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get session info
        session = supabase.table("sessions").select("*").eq("session_id", session_id).execute()
        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = session.data[0]
        
        # Get all responses
        responses = supabase.table("responses").select("*").eq("session_id", session_id).execute()
        
        # Get all evaluations
        evaluations = supabase.table("part_evaluations").select("*").eq("session_id", session_id).execute()
        
        # Get final evaluation
        final_eval = supabase.table("final_evaluations").select("*").eq("session_id", session_id).execute()
        
        # Organize data by parts
        parts_data = organize_session_data(responses.data, evaluations.data)
        
        return templates.TemplateResponse("dashboard/session_detail.html", {
            "request": request,
            "session": session_data,
            "parts_data": parts_data,
            "final_evaluation": final_eval.data[0] if final_eval.data else None,
            "page_title": f"Session {session_id[:8]}"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading session detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to load session detail")

@dashboard_router.get("/analytics", response_class=HTMLResponse)
async def dashboard_analytics(request: Request):
    """Analytics page with charts and insights"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get analytics data
        analytics_data = await get_analytics_data()
        
        return templates.TemplateResponse("dashboard/analytics.html", {
            "request": request,
            "analytics": analytics_data,
            "page_title": "Performance Analytics"
        })
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to load analytics")

# API endpoints for dashboard data
@dashboard_router.get("/api/stats")
async def get_dashboard_stats():
    """Get overview statistics for dashboard"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Total sessions
        sessions_result = supabase.table("sessions").select("id, is_complete, created_at").execute()
        sessions = sessions_result.data or []
        
        # Completed sessions
        completed_sessions = [s for s in sessions if s.get("is_complete")]
        
        # Recent sessions (last 7 days)
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_sessions = [s for s in sessions if s["created_at"] > week_ago]
        
        # Final evaluations
        final_evals_result = supabase.table("final_evaluations").select("overall_performance, average_score").execute()
        final_evals = final_evals_result.data or []
        
        # Performance distribution
        performance_dist = {}
        for eval in final_evals:
            perf = eval.get("overall_performance", "Unknown")
            performance_dist[perf] = performance_dist.get(perf, 0) + 1
        
        # Average score
        scores = [fe.get("average_score", 0) for fe in final_evals if fe.get("average_score")]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "completion_rate": round(len(completed_sessions) / len(sessions) * 100, 1) if sessions else 0,
            "recent_sessions": len(recent_sessions),
            "average_score": avg_score,
            "performance_distribution": performance_dist
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "completion_rate": 0,
            "recent_sessions": 0,
            "average_score": 0,
            "performance_distribution": {}
        }

@dashboard_router.get("/api/recent-sessions")
async def get_recent_sessions():
    """Get recent evaluation sessions for dashboard preview"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get recent sessions (last 10)
        sessions = supabase.table("sessions").select(
            "session_id, created_at, last_activity, is_complete, completed_parts"
        ).order("created_at", desc=True).limit(10).execute()
        
        # Get final evaluations for recent sessions
        session_ids = [s["session_id"] for s in (sessions.data or [])]
        final_evals = []
        if session_ids:
            final_evals_result = supabase.table("final_evaluations").select(
                "session_id, overall_performance, average_score"
            ).in_("session_id", session_ids).execute()
            final_evals = final_evals_result.data or []
        
        # Combine data
        final_eval_dict = {fe["session_id"]: fe for fe in final_evals}
        
        sessions_data = []
        for session in (sessions.data or []):
            session_data = {
                "session_id": session["session_id"],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
                "is_complete": session["is_complete"],
                "completed_parts_count": len(session.get("completed_parts", [])),
                "duration_minutes": calculate_duration_minutes(session["created_at"], session["last_activity"]),
                "final_evaluation": final_eval_dict.get(session["session_id"])
            }
            sessions_data.append(session_data)
        
        return sessions_data
    except Exception as e:
        logger.error(f"Error getting recent sessions: {e}")
        return []

@dashboard_router.get("/api/analytics")
async def get_analytics_data():
    """Get detailed analytics data for charts"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Daily completion trends (last 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        sessions = supabase.table("sessions").select("created_at, is_complete").gte("created_at", thirty_days_ago).execute()
        sessions_data = sessions.data or []
        
        # Group by date
        daily_data = {}
        for session in sessions_data:
            date = session["created_at"][:10]  # Extract date part
            if date not in daily_data:
                daily_data[date] = {"total": 0, "completed": 0}
            daily_data[date]["total"] += 1
            if session.get("is_complete"):
                daily_data[date]["completed"] += 1
        
        # Performance by part analysis
        part_evals = supabase.table("part_evaluations").select("part_id, average_score, scores").execute()
        part_performance = analyze_part_performance(part_evals.data or [])
        
        # Score distribution
        final_evals = supabase.table("final_evaluations").select("average_score, overall_scores").execute()
        score_distribution = analyze_score_distribution(final_evals.data or [])
        
        # Tool recommendations analysis
        tool_recommendations = analyze_tool_recommendations(final_evals.data or [])
        
        return {
            "daily_trends": daily_data,
            "part_performance": part_performance,
            "score_distribution": score_distribution,
            "tool_recommendations": tool_recommendations
        }
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        return {
            "daily_trends": {},
            "part_performance": {},
            "score_distribution": {},
            "tool_recommendations": {}
        }

# Helper functions
def calculate_duration_minutes(created_at: str, last_activity: str) -> int:
    """Calculate duration in minutes between two timestamps"""
    try:
        start = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        end = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        return int((end - start).total_seconds() / 60)
    except:
        return 0

def organize_session_data(responses_data: List, evaluations_data: List) -> Dict:
    """Organize responses and evaluations by part"""
    parts_data = {}
    
    # Group responses by part
    for response in responses_data or []:
        part_id = response["part_id"]
        if part_id not in parts_data:
            parts_data[part_id] = {"responses": {}, "evaluation": None}
        parts_data[part_id]["responses"][response["question_id"]] = response
    
    # Add evaluations
    for evaluation in evaluations_data or []:
        part_id = evaluation["part_id"]
        if part_id not in parts_data:
            parts_data[part_id] = {"responses": {}, "evaluation": None}
        parts_data[part_id]["evaluation"] = evaluation
    
    return parts_data

def analyze_part_performance(part_evaluations: List) -> Dict:
    """Analyze performance across different parts"""
    part_stats = {}
    
    for eval in part_evaluations:
        part_id = eval["part_id"]
        if part_id not in part_stats:
            part_stats[part_id] = {"scores": [], "count": 0}
        
        part_stats[part_id]["scores"].append(eval.get("average_score", 0))
        part_stats[part_id]["count"] += 1
    
    # Calculate averages
    for part_id, stats in part_stats.items():
        if stats["scores"]:
            stats["average"] = round(sum(stats["scores"]) / len(stats["scores"]), 1)
        else:
            stats["average"] = 0
    
    return part_stats

def analyze_score_distribution(final_evaluations: List) -> Dict:
    """Analyze distribution of scores"""
    score_ranges = {
        "0-3": 0, "3-5": 0, "5-7": 0, "7-8.5": 0, "8.5-10": 0
    }
    
    skill_averages = {
        "analytical_thinking": [],
        "problem_solving": [],
        "systematic_approach": [],
        "practical_application": [],
        "communication_skills": []
    }
    
    for eval in final_evaluations:
        # Overall score distribution
        avg_score = eval.get("average_score", 0)
        if avg_score < 3:
            score_ranges["0-3"] += 1
        elif avg_score < 5:
            score_ranges["3-5"] += 1
        elif avg_score < 7:
            score_ranges["5-7"] += 1
        elif avg_score < 8.5:
            score_ranges["7-8.5"] += 1
        else:
            score_ranges["8.5-10"] += 1
        
        # Skill-specific averages
        overall_scores = eval.get("overall_scores", {})
        for skill, scores_list in skill_averages.items():
            if skill in overall_scores:
                scores_list.append(overall_scores[skill])
    
    # Calculate skill averages
    skill_avg_final = {}
    for skill, scores in skill_averages.items():
        if scores:
            skill_avg_final[skill] = round(sum(scores) / len(scores), 1)
        else:
            skill_avg_final[skill] = 0
    
    return {
        "score_ranges": score_ranges,
        "skill_averages": skill_avg_final
    }

def analyze_tool_recommendations(final_evaluations: List) -> Dict:
    """Analyze tool recommendations to identify common weaknesses"""
    tool_frequency = {}
    
    for eval in final_evaluations:
        recommendations = eval.get("tool_recommendations", {})
        for tool_name in recommendations.keys():
            tool_frequency[tool_name] = tool_frequency.get(tool_name, 0) + 1
    
    return tool_frequency 