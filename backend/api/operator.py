"""
Operator API Endpoints

Endpoints for operator dashboard: user management, recommendation review, approval
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

from backend.guardrails.consent import (
    check_consent,
    get_consented_users,
    grant_consent,
    revoke_consent,
    ConsentError
)
from backend.guardrails.metrics import (
    compute_operator_metrics,
    get_user_metrics,
    get_user_list_with_status
)
from backend.recommend.approval import (
    approve_recommendation,
    flag_recommendation,
    get_user_recommendations,
    get_recommendation_with_items
)
from backend.recommend.management import (
    generate_recommendation_for_user,
    soft_delete_recommendation
)
from backend.recommend.traces import get_traces, get_latest_persona_traces
from backend.storage.database import get_db_path

router = APIRouter()

# Get database path
DB_PATH = get_db_path()


# Pydantic models for request/response validation
class ApprovalRequest(BaseModel):
    reviewer_notes: Optional[str] = None


class FlagRequest(BaseModel):
    reviewer_notes: str


class ConsentRequest(BaseModel):
    user_id: str


# ========== User Endpoints ==========

@router.get("/users")
async def get_users(
    persona: Optional[int] = Query(None, description="Filter by primary persona ID"),
    status: Optional[str] = Query(None, description="Filter by recommendation status"),
    sort: str = Query("name", description="Sort by: name, date, persona")
):
    """
    Get list of all consented users with recommendation status
    
    Query Parameters:
    - persona: Filter by primary persona ID (30d window)
    - status: Filter by recommendation status (PENDING_REVIEW, APPROVED, FLAGGED)
    - sort: Sort order (name, date, persona)
    
    Returns list of users with metadata
    """
    try:
        users = get_user_list_with_status(
            db_path=DB_PATH,
            persona_filter=persona,
            status_filter=status,
            sort_by=sort
        )
        
        return {
            "users": users,
            "count": len(users),
            "filters_applied": {
                "persona": persona,
                "status": status,
                "sort": sort
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.get("/users/{user_id}")
async def get_user_detail(user_id: str):
    """
    Get detailed information for a specific user
    
    Includes:
    - Persona assignments (30d and 180d windows)
    - Account information
    - Feature metrics
    - Recommendation counts
    
    Returns 403 if user has not consented
    """
    try:
        # Check consent
        check_consent(user_id, DB_PATH)
        
        # Get user metrics
        metrics = get_user_metrics(user_id, DB_PATH)
        
        return metrics
        
    except ConsentError:
        raise HTTPException(
            status_code=403,
            detail=f"User {user_id} has not consented to data processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user detail: {str(e)}")


@router.get("/users/{user_id}/recommendations")
async def get_user_recs(user_id: str):
    """
    Get all recommendations for a specific user (all statuses)
    
    Returns full recommendations with all items (educational, actionable, partner offers)
    
    Returns 403 if user has not consented
    """
    try:
        # Check consent
        check_consent(user_id, DB_PATH)
        
        # Get recommendations (parent records only)
        recommendations = get_user_recommendations(user_id, DB_PATH)
        
        # Fetch full details with items for each recommendation
        full_recommendations = []
        for rec in recommendations:
            try:
                full_rec = get_recommendation_with_items(rec['recommendation_id'], DB_PATH)
                full_recommendations.append(full_rec)
            except Exception as e:
                # If fetching items fails, include the parent record anyway
                print(f"Warning: Could not fetch items for {rec['recommendation_id']}: {e}")
                full_recommendations.append(rec)
        
        return {
            "user_id": user_id,
            "recommendations": full_recommendations,
            "count": len(full_recommendations)
        }
        
    except ConsentError:
        raise HTTPException(
            status_code=403,
            detail=f"User {user_id} has not consented to data processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")


# ========== Recommendation Endpoints ==========

@router.get("/recommendations/{rec_id}")
async def get_recommendation(rec_id: str):
    """
    Get full recommendation with all items
    
    Includes:
    - Educational content items
    - Actionable items with rationales
    - Partner offers with eligibility details
    """
    try:
        recommendation = get_recommendation_with_items(rec_id, DB_PATH)
        return recommendation
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendation: {str(e)}")


@router.post("/recommendations/{rec_id}/approve")
async def approve_rec(rec_id: str, request: ApprovalRequest):
    """
    Approve a recommendation for delivery to user
    
    Body:
    - reviewer_notes: Optional notes from operator
    
    Updates recommendation status to APPROVED
    """
    try:
        updated_rec = approve_recommendation(
            rec_id=rec_id,
            db_path=DB_PATH,
            reviewer_notes=request.reviewer_notes
        )
        
        return {
            "message": "Recommendation approved successfully",
            "recommendation": updated_rec
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve recommendation: {str(e)}")


@router.post("/recommendations/{rec_id}/flag")
async def flag_rec(rec_id: str, request: FlagRequest):
    """
    Flag a recommendation as problematic (blocked from delivery)
    
    Body:
    - reviewer_notes: Required notes explaining why flagged
    
    Updates recommendation status to FLAGGED
    """
    try:
        updated_rec = flag_recommendation(
            rec_id=rec_id,
            db_path=DB_PATH,
            reviewer_notes=request.reviewer_notes
        )
        
        return {
            "message": "Recommendation flagged successfully",
            "recommendation": updated_rec
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to flag recommendation: {str(e)}")


# ========== Decision Traces Endpoints ==========

@router.get("/traces/{user_id}")
async def get_user_traces(
    user_id: str,
    recommendation_id: Optional[str] = Query(None, description="Filter by recommendation ID")
):
    """
    Get decision traces for a user
    
    Shows why personas were assigned and why content was selected
    
    Query Parameters:
    - recommendation_id: Optional filter by specific recommendation
    
    Returns 403 if user has not consented
    """
    try:
        # Check consent
        check_consent(user_id, DB_PATH)
        
        # Get traces
        traces = get_traces(user_id, DB_PATH, recommendation_id)
        
        # Also get latest persona traces for convenience
        persona_traces = get_latest_persona_traces(user_id, DB_PATH)
        
        return {
            "user_id": user_id,
            "traces": traces,
            "latest_persona_traces": persona_traces,
            "count": len(traces)
        }
        
    except ConsentError:
        raise HTTPException(
            status_code=403,
            detail=f"User {user_id} has not consented to data processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve traces: {str(e)}")


# ========== Metrics Endpoints ==========

@router.get("/metrics")
async def get_metrics(force_refresh: bool = Query(False, description="Bypass cache and recompute")):
    """
    Get aggregate metrics for operator dashboard
    
    Includes:
    - Total consented users
    - Pending/approved/flagged recommendation counts
    - Approval rate
    - Coverage percentage
    - Average recommendations per user
    
    Cached for 60 seconds by default
    """
    try:
        metrics = compute_operator_metrics(DB_PATH, force_refresh=force_refresh)
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute metrics: {str(e)}")


# ========== Consent Management Endpoints (Epic 6) ==========

@router.post("/consent/grant")
async def grant_user_consent(request: ConsentRequest):
    """
    Grant consent for a user
    
    Updates user consent status to true and triggers recommendation generation.
    Returns 202 Accepted as generation happens asynchronously.
    
    Body:
    - user_id: User identifier
    """
    try:
        # Grant consent
        grant_consent(request.user_id, DB_PATH)
        
        # Trigger recommendation generation
        # Note: In production, this would be async/background task
        # For demo, we'll trigger it but return immediately
        try:
            config_path = Path(__file__).parent.parent.parent / "config.json"
            recommendation = generate_recommendation_for_user(
                user_id=request.user_id,
                db_path=DB_PATH,
                config_path=str(config_path)
            )
            
            return {
                "message": "Consent granted and recommendation generation initiated",
                "user_id": request.user_id,
                "recommendation_id": recommendation.get('recommendation_id')
            }
            
        except Exception as gen_error:
            # Consent was granted, but generation failed
            # This is acceptable - operator can manually generate later
            logger.error(f"Failed to generate recommendation after consent grant: {gen_error}")
            return {
                "message": "Consent granted successfully, but recommendation generation failed",
                "user_id": request.user_id,
                "error": str(gen_error)
            }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grant consent: {str(e)}")


@router.post("/consent/revoke")
async def revoke_user_consent(request: ConsentRequest):
    """
    Revoke consent for a user
    
    Updates user consent status to false and soft deletes all recommendations.
    
    Body:
    - user_id: User identifier
    """
    try:
        revoke_consent(request.user_id, DB_PATH)
        
        return {
            "message": "Consent revoked successfully",
            "user_id": request.user_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke consent: {str(e)}")


# ========== Recommendation Management Endpoints (Epic 6) ==========

@router.post("/users/{user_id}/generate")
async def generate_recommendation(user_id: str):
    """
    Generate a new recommendation for a user on-demand
    
    Triggers the full recommendation generation pipeline.
    New recommendation will have PENDING_REVIEW status.
    
    Returns 201 Created with the new recommendation
    """
    try:
        config_path = Path(__file__).parent.parent.parent / "config.json"
        recommendation = generate_recommendation_for_user(
            user_id=user_id,
            db_path=DB_PATH,
            config_path=str(config_path)
        )
        
        return {
            "message": "Recommendation generated successfully",
            "recommendation": recommendation
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")


@router.delete("/recommendations/{rec_id}")
async def delete_recommendation(rec_id: str):
    """
    Soft delete a recommendation
    
    Sets recommendation status to DELETED, preserving it for audit trail
    but filtering it out from all queries.
    
    Returns 204 No Content on success
    """
    try:
        soft_delete_recommendation(rec_id, DB_PATH)
        
        return {
            "message": "Recommendation deleted successfully",
            "recommendation_id": rec_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete recommendation: {str(e)}")


# ========== Health Check ==========

@router.get("/health")
async def operator_health():
    """Operator API health check"""
    try:
        # Quick database connectivity check
        users = get_consented_users(DB_PATH)
        
        return {
            "status": "healthy",
            "database": "connected",
            "consented_users": len(users)
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

