"""
FastAPI main application
Entry point for SpendSense backend
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os

from storage import get_db, init_db
from storage.models import User, Consent
from .schemas import (
    UserResponse, 
    HealthResponse,
    ConsentResponse,
    ConsentRequest
)

# Initialize FastAPI app
app = FastAPI(
    title="SpendSense API",
    description="Behavioral pattern detection and personalized financial education",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        os.getenv("FRONTEND_URL", "http://localhost:5173")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup
    """
    init_db()
    print("✅ Database initialized")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "SpendSense API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Verifies database connection and returns system status
    """
    try:
        # Test database connection
        user_count = db.query(User).count()
        
        return HealthResponse(
            status="healthy",
            database="connected",
            user_count=user_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@app.get("/users", response_model=List[UserResponse], tags=["Users"])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all users with basic information
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    """
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Enrich with consent status
    user_responses = []
    for user in users:
        consent = db.query(Consent).filter(Consent.user_id == user.user_id).first()
        user_responses.append(
            UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                persona=user.primary_persona,
                consent_status=consent.consent_status if consent else False,
                created_at=user.created_at
            )
        )
    
    return user_responses


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific user
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    consent = db.query(Consent).filter(Consent.user_id == user_id).first()
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        persona=user.primary_persona,
        consent_status=consent.consent_status if consent else False,
        created_at=user.created_at
    )


@app.get("/consent/{user_id}", response_model=ConsentResponse, tags=["Consent"])
async def get_consent_status(user_id: str, db: Session = Depends(get_db)):
    """
    Get consent status for a user
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    consent = db.query(Consent).filter(Consent.user_id == user_id).first()
    
    if not consent:
        # Return default no-consent response
        return ConsentResponse(
            user_id=user_id,
            consent_status=False,
            consent_date=None,
            revoked_date=None
        )
    
    return ConsentResponse(
        user_id=consent.user_id,
        consent_status=consent.consent_status,
        consent_date=consent.consent_date,
        revoked_date=consent.revoked_date
    )


@app.post("/consent", response_model=ConsentResponse, tags=["Consent"])
async def record_consent(
    consent_data: ConsentRequest,
    db: Session = Depends(get_db)
):
    """
    Record or update user consent
    """
    user = db.query(User).filter(User.user_id == consent_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    consent = db.query(Consent).filter(Consent.user_id == consent_data.user_id).first()
    
    if consent:
        # Update existing consent
        consent.consent_status = True
        consent.consent_date = consent_data.consent_date
        consent.revoked_date = None
    else:
        # Create new consent record
        consent = Consent(
            user_id=consent_data.user_id,
            consent_status=True,
            consent_date=consent_data.consent_date
        )
        db.add(consent)
    
    db.commit()
    db.refresh(consent)
    
    return ConsentResponse(
        user_id=consent.user_id,
        consent_status=consent.consent_status,
        consent_date=consent.consent_date,
        revoked_date=consent.revoked_date
    )


@app.delete("/consent/{user_id}", response_model=ConsentResponse, tags=["Consent"])
async def revoke_consent(user_id: str, db: Session = Depends(get_db)):
    """
    Revoke user consent
    """
    consent = db.query(Consent).filter(Consent.user_id == user_id).first()
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    
    from datetime import datetime
    consent.consent_status = False
    consent.revoked_date = datetime.utcnow()
    
    db.commit()
    db.refresh(consent)
    
    return ConsentResponse(
        user_id=consent.user_id,
        consent_status=consent.consent_status,
        consent_date=consent.consent_date,
        revoked_date=consent.revoked_date
    )


# Placeholder endpoints for future implementation
@app.get("/profile/{user_id}", tags=["Profile"])
async def get_user_profile(user_id: str):
    """
    Get user profile with persona assignment
    TODO: Implement in Epic 3
    """
    return {
        "user_id": user_id,
        "message": "Profile endpoint - to be implemented in Epic 3"
    }


@app.get("/signals/{user_id}", tags=["Signals"])
async def get_user_signals(user_id: str):
    """
    Get behavioral signals for user
    TODO: Implement in Epic 2
    """
    return {
        "user_id": user_id,
        "message": "Signals endpoint - to be implemented in Epic 2"
    }


@app.get("/recommendations/{user_id}", tags=["Recommendations"])
async def get_recommendations(user_id: str):
    """
    Get personalized recommendations
    TODO: Implement in Epic 4
    """
    return {
        "user_id": user_id,
        "message": "Recommendations endpoint - to be implemented in Epic 4"
    }

