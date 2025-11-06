"""
FastAPI Main Application

Entry point for SpendSense API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SpendSense Operator API",
    description="API for operator dashboard - recommendation review and approval",
    version="1.0.0"
)

# Load config
config_path = Path(__file__).parent.parent.parent / "config.json"
with open(config_path) as f:
    config = json.load(f)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # FastAPI default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SpendSense Operator API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SpendSense Operator API",
        "docs": "/docs",
        "health": "/api/health"
    }


# Import and include operator routes
from .operator import router as operator_router
app.include_router(operator_router, prefix="/api/operator", tags=["operator"])

# Import and include user routes (Epic 6)
from .user import router as user_router
app.include_router(user_router, prefix="/api", tags=["users"])


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "status_code": 500
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
