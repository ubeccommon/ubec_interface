#!/usr/bin/env python3
"""
UBEC Protocol Website - Main Web Application
==============================================

Public-facing website for the Ubuntu Bioregional Economic Commons Protocol.
Showcases the four-element token ecosystem, live blockchain data, and holonic
evaluation framework.

This module implements:
    - Principle #2: Service Pattern with centralized execution
    - Principle #5: Strict Async Operations (100% async/await)
    - Principle #10: Clear Separation of Concerns (passive web layer)
    - Principle #11: Comprehensive Documentation

Architecture:
    - FastAPI async web framework
    - Jinja2 templates for HTML rendering
    - RESTful API endpoints for data fetching
    - WebSocket support for real-time updates (future)
    
Security:
    - Read-only database access
    - Rate limiting on all endpoints
    - CORS configuration for API
    - Input validation on all endpoints

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.

Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Local imports
from config.settings import Settings
from api.routes import router as api_router
from utils.backend_client import BackendAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================================================
# APPLICATION INITIALIZATION
# ========================================================================

# Load settings
settings = Settings()

# Create FastAPI application
app = FastAPI(
    title="UBEC Protocol Network",
    description="Ubuntu Bioregional Economic Commons - Four Element Token Ecosystem",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/api/redoc" if settings.ENABLE_API_DOCS else None
)

# ========================================================================
# MIDDLEWARE CONFIGURATION
# ========================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ========================================================================
# STATIC FILES AND TEMPLATES
# ========================================================================

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# ========================================================================
# BACKEND CLIENT INITIALIZATION
# ========================================================================

backend_client: Optional[BackendAPIClient] = None

async def get_backend_client() -> BackendAPIClient:
    """
    Get or create backend API client.
    
    Principle #4: Single Source of Truth - backend as data source
    Principle #5: Strict Async Operations
    """
    global backend_client
    
    if backend_client is None:
        backend_client = BackendAPIClient(
            base_url=settings.BACKEND_API_URL,
            api_key=settings.BACKEND_API_KEY
        )
    
    return backend_client

# ========================================================================
# LIFECYCLE EVENTS
# ========================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("=" * 70)
    logger.info("UBEC PROTOCOL WEBSITE STARTING")
    logger.info("=" * 70)
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Backend API: {settings.BACKEND_API_URL}")
    logger.info(f"Host: {settings.APP_HOST}:{settings.APP_PORT}")
    logger.info("=" * 70)
    
    # Initialize backend client
    client = await get_backend_client()
    logger.info("✓ Backend client initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("=" * 70)
    logger.info("UBEC PROTOCOL WEBSITE SHUTTING DOWN")
    logger.info("=" * 70)
    
    # Close backend client
    if backend_client:
        await backend_client.close()
        logger.info("✓ Backend client closed")

# ========================================================================
# PAGE ROUTES
# ========================================================================

@app.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    """
    Home page - Four Elements Overview
    
    Displays interactive visualization of the four-element token ecosystem:
    - Air (UBEC): Diversity & Gateway
    - Water (UBECrc): Reciprocity & Flow
    - Earth (UBECgpi): Mutualism & Stability
    - Fire (UBECtt): Regeneration & Transformation
    """
    try:
        client = await get_backend_client()
        
        # Fetch token data for home page
        tokens = await client.get_all_tokens()
        network_status = await client.get_network_status()
        
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "tokens": tokens,
                "network_status": network_status,
                "page": "home"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unable to load home page. Please try again later."
            },
            status_code=500
        )


@app.get("/protocol", response_class=HTMLResponse, name="protocol")
async def protocol(request: Request):
    """
    Protocol Overview page
    
    Deep dive into:
    - Token ecosystem architecture
    - Holonic evaluation framework (5 dimensions)
    - Smart contract documentation
    - Ubuntu philosophy integration
    """
    try:
        client = await get_backend_client()
        
        # Fetch protocol details
        tokens = await client.get_all_tokens()
        holonic_scores = await client.get_holonic_scores()
        
        return templates.TemplateResponse(
            "protocol.html",
            {
                "request": request,
                "tokens": tokens,
                "holonic_scores": holonic_scores,
                "page": "protocol"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering protocol page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unable to load protocol information."
            },
            status_code=500
        )


@app.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    """
    Live Dashboard page
    
    Real-time network visualization:
    - Current network participants
    - Transaction flows
    - Ubuntu alignment scores
    - Regeneration impact metrics
    - Holonic category distribution
    """
    try:
        client = await get_backend_client()
        
        # Fetch dashboard data
        network_status = await client.get_network_status()
        holonic_scores = await client.get_holonic_scores()
        recent_transactions = await client.get_recent_transactions(limit=20)
        distribution_stats = await client.get_distribution_stats()
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "network_status": network_status,
                "holonic_scores": holonic_scores,
                "recent_transactions": recent_transactions,
                "distribution_stats": distribution_stats,
                "page": "dashboard"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unable to load dashboard data."
            },
            status_code=500
        )


@app.get("/stories", response_class=HTMLResponse, name="stories")
async def stories(request: Request):
    """
    Token Stories page
    
    The narrative of the four UBEC tokens:
    - Philosophical foundation and Ubuntu principles
    - Each token's design, purpose, and symbolism
    - Current deployment status and community adoption
    - The journey from vision to reality
    - Phased deployment strategy
    """
    try:
        client = await get_backend_client()
        
        # Fetch token data for stories page
        tokens = await client.get_all_tokens()
        
        return templates.TemplateResponse(
            "stories.html",
            {
                "request": request,
                "tokens": tokens,
                "page": "stories"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering stories page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unable to load token stories."
            },
            status_code=500
        )


@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    """
    About page
    
    Information about:
    - Ubuntu philosophy and principles
    - Project mission and vision
    - Team and contributors
    - Roadmap and milestones
    """
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "page": "about"
        }
    )


@app.get("/docs", response_class=HTMLResponse, name="documentation")
async def documentation(request: Request):
    """
    Documentation portal
    
    Resources for:
    - Developers (API docs, SDK)
    - Communities (participation guides)
    - Integration partners
    """
    return templates.TemplateResponse(
        "docs.html",
        {
            "request": request,
            "page": "docs"
        }
    )

# ========================================================================
# API ROUTES
# ========================================================================

# Include API router
app.include_router(api_router, prefix="/api/v1", tags=["api"])

# ========================================================================
# HEALTH CHECK
# ========================================================================

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns system status and backend connectivity
    """
    try:
        client = await get_backend_client()
        
        # Quick ping to backend
        network_status = await client.get_network_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "backend_connected": True,
            "services": {
                "web": "operational",
                "backend": "operational"
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "backend_connected": False,
            "error": str(e)
        }

# ========================================================================
# ERROR HANDLERS
# ========================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": "Page not found",
            "status_code": 404
        },
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors"""
    logger.error(f"Server error: {exc}")
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": "Internal server error",
            "status_code": 500
        },
        status_code=500
    )

# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Principle #2: This file can only be run as main entry point
    # No standalone execution for service modules
    
    uvicorn.run(
        "main_web:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
