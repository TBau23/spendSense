"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str
    database: str
    user_count: int


class UserResponse(BaseModel):
    """Response model for user data"""
    user_id: str
    name: str
    email: str
    persona: Optional[str] = None
    consent_status: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConsentRequest(BaseModel):
    """Request model for recording consent"""
    user_id: str
    consent_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ConsentResponse(BaseModel):
    """Response model for consent data"""
    user_id: str
    consent_status: bool
    consent_date: Optional[datetime] = None
    revoked_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Response model for user profile (TODO: Epic 3)"""
    user_id: str
    primary_persona: Optional[str] = None
    secondary_persona: Optional[str] = None
    # Will add more fields in Epic 3


class SignalsResponse(BaseModel):
    """Response model for behavioral signals (TODO: Epic 2)"""
    user_id: str
    window_days: int
    # Will add signal fields in Epic 2


class RecommendationResponse(BaseModel):
    """Response model for recommendations (TODO: Epic 4)"""
    user_id: str
    recommendations: list
    # Will add recommendation fields in Epic 4

