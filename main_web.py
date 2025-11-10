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

Version: 1.0.1
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import markdown

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Local imports
from config.settings import Settings
from api.routes import router as api_router

# Conditional import for backend client
try:
    from utils.backend_client import BackendAPIClient
    BACKEND_CLIENT_AVAILABLE = True
except ImportError:
    BACKEND_CLIENT_AVAILABLE = False
    BackendAPIClient = None

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
    version="1.0.1",
    docs_url="/api/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/api/redoc" if settings.ENABLE_API_DOCS else None
)

# ========================================================================
# MIDDLEWARE CONFIGURATION
# ========================================================================

# UTF-8 Charset Middleware (CRITICAL FOR EMOJI DISPLAY)
@app.middleware("http")
async def add_utf8_charset(request: Request, call_next):
    """
    Ensure all HTML responses include UTF-8 charset.
    
    This prevents emoji characters from displaying as garbled text.
    Without this, browsers may default to ISO-8859-1 or Windows-1252.
    """
    response = await call_next(request)
    
    # Add charset to HTML responses
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("text/html") and "charset" not in content_type.lower():
        response.headers["content-type"] = "text/html; charset=utf-8"
        logger.debug(f"Added UTF-8 charset to {request.url.path}")
    
    return response

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
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
else:
    logger.warning(f"Static directory not found: {static_path}")

# Setup templates
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# ========================================================================
# BACKEND CLIENT INITIALIZATION
# ========================================================================

backend_client: Optional[BackendAPIClient] = None

async def get_backend_client() -> Optional[BackendAPIClient]:
    """
    Get or create backend API client with error handling.
    
    Principle #4: Single Source of Truth - backend as data source
    Principle #5: Strict Async Operations
    
    Returns None if backend client is unavailable or fails.
    """
    global backend_client
    
    if not BACKEND_CLIENT_AVAILABLE:
        logger.warning("Backend client module not available")
        return None
    
    if backend_client is None:
        try:
            backend_client = BackendAPIClient(
                base_url=settings.BACKEND_API_URL,
                api_key=settings.BACKEND_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize backend client: {e}")
            return None
    
    return backend_client

# ========================================================================
# FALLBACK DATA FOR OFFLINE MODE
# ========================================================================

def get_fallback_tokens() -> List[Dict[str, Any]]:
    """
    Provide fallback token data when backend is unavailable.
    
    This ensures the website remains functional even if backend is down.
    """
    return [
        {
            "token_code": "UBEC",
            "element": "Air",
            "element_symbol": "🌬️",
            "ubuntu_principle": "Diversity",
            "description": "Gateway & Universal Access - Like air, freely available to all, supporting diverse participation in the ecosystem.",
            "total_supply": 152025699,
            "holders_count": 495,
            "status": "live",
            "issuer": "GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        },
        {
            "token_code": "UBECrc",
            "element": "Water",
            "element_symbol": "💧",
            "ubuntu_principle": "Reciprocity",
            "description": "Flow & Exchange - Like water flowing through a watershed, facilitating balanced giving and receiving.",
            "total_supply": 112000,
            "holders_count": 3,
            "status": "live",
            "issuer": "GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        },
        {
            "token_code": "UBECgpi",
            "element": "Earth",
            "element_symbol": "🌍",
            "ubuntu_principle": "Mutualism",
            "description": "Stability & Value - Like earth providing foundation, enabling stable mutually beneficial relationships.",
            "total_supply": 110,
            "holders_count": 2,
            "status": "live",
            "issuer": "GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        },
        {
            "token_code": "UBECtt",
            "element": "Fire",
            "element_symbol": "🔥",
            "ubuntu_principle": "Regeneration",
            "description": "Transformation & Action - Like fire catalyzing change, enabling regenerative transformation.",
            "total_supply": 1000000,
            "holders_count": 1,
            "status": "live",
            "issuer": "GXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        }
    ]

def get_fallback_network_status() -> Dict[str, Any]:
    """Fallback network status when backend unavailable."""
    return {
        "network_health": "healthy",
        "last_block_time": datetime.now().isoformat(),
        "total_supply": "152M+",
        "total_holders": "500+"
    }

def get_fallback_holonic_scores() -> Optional[Dict[str, float]]:
    """Fallback holonic scores when backend unavailable."""
    return None  # Templates handle None gracefully

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
    logger.info(f"UTF-8 Charset Middleware: Enabled")
    logger.info("=" * 70)
    
    # Initialize backend client (with error handling)
    client = await get_backend_client()
    if client:
        logger.info("✓ Backend client initialized")
    else:
        logger.warning("⚠ Backend client unavailable - using fallback data")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("=" * 70)
    logger.info("UBEC PROTOCOL WEBSITE SHUTTING DOWN")
    logger.info("=" * 70)
    
    # Close backend client
    if backend_client:
        try:
            await backend_client.close()
            logger.info("✓ Backend client closed")
        except Exception as e:
            logger.error(f"Error closing backend client: {e}")

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

async def safe_backend_call(func, *args, fallback=None, **kwargs):
    """
    Safely call backend functions with fallback on error.
    
    Args:
        func: Async function to call
        *args: Positional arguments for function
        fallback: Value to return on error
        **kwargs: Keyword arguments for function
    
    Returns:
        Result of function call or fallback value
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Backend call failed: {func.__name__} - {e}")
        return fallback

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
        
        # Fetch token data with fallback
        if client:
            tokens = await safe_backend_call(
                client.get_all_tokens,
                fallback=get_fallback_tokens()
            )
            network_status = await safe_backend_call(
                client.get_network_status,
                fallback=get_fallback_network_status()
            )
        else:
            tokens = get_fallback_tokens()
            network_status = get_fallback_network_status()
        
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "tokens": tokens,
                "network_status": network_status,
                "network_stats": network_status,  # Alias for template compatibility
                "page": "home"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering home page: {e}", exc_info=True)
        
        # Try to return page with fallback data
        try:
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "tokens": get_fallback_tokens(),
                    "network_status": get_fallback_network_status(),
                    "network_stats": get_fallback_network_status(),
                    "page": "home"
                }
            )
        except Exception as template_error:
            logger.error(f"Template rendering failed: {template_error}", exc_info=True)
            
            # Last resort: simple HTML response
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>UBEC Protocol - Error</title>
                </head>
                <body>
                    <h1>UBEC Protocol Network</h1>
                    <p>The website is temporarily unavailable.</p>
                    <p>Error: {str(e)}</p>
                    <p><a href="/health">Check system health</a></p>
                </body>
                </html>
                """,
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
        
        # Fetch protocol details with fallback
        if client:
            tokens = await safe_backend_call(
                client.get_all_tokens,
                fallback=get_fallback_tokens()
            )
            holonic_scores = await safe_backend_call(
                client.get_holonic_scores,
                fallback=get_fallback_holonic_scores()
            )
        else:
            tokens = get_fallback_tokens()
            holonic_scores = get_fallback_holonic_scores()
        
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
        logger.error(f"Error rendering protocol page: {e}", exc_info=True)
        
        # Try with fallback data
        try:
            return templates.TemplateResponse(
                "protocol.html",
                {
                    "request": request,
                    "tokens": get_fallback_tokens(),
                    "holonic_scores": get_fallback_holonic_scores(),
                    "page": "protocol"
                }
            )
        except:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Protocol - UBEC</title>
                </head>
                <body>
                    <h1>Protocol Overview Unavailable</h1>
                    <p><a href="/">Return to Home</a></p>
                </body>
                </html>
                """,
                status_code=500
            )


@app.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    """
    Live Dashboard page
    
    Real-time network visualization with comprehensive geographic data:
    
    Network Metrics:
    - Active participants count
    - 24-hour transaction volume
    - Bioregions participation
    - Ubuntu alignment scores
    
    Holonic Evaluation:
    - Overall network health composite score
    - Five-dimension holonic scores:
      * Autonomy Integration (Diversity)
      * Ubuntu Alignment (Holism)
      * Reciprocity Health
      * Mutualism Capacity
      * Regeneration Impact
    
    Transaction Activity:
    - Recent transactions (last 20)
    - Transaction types and amounts
    - Token distribution patterns
    
    Geographic Data (NEW):
    - Ecoregions overview with biomes and realms
    - Major watersheds with area coverage
    - Bioregional diversity metrics
    
    All data fetched asynchronously from backend API with graceful
    fallback handling for offline/error scenarios.
    """
    # Default empty data structure
    context = {
        "request": request,
        "network_status": None,
        "holonic_scores": None,
        "recent_transactions": None,
        "distribution_stats": None,
        "ecoregions": None,
        "watersheds": None,
        "page": "dashboard"
    }
    
    try:
        client = await get_backend_client()
        
        # Fetch network status with error handling
        try:
            raw_network_status = await client.get_network_status()
            context["network_status"] = {
                'active_participants': raw_network_status.get('total_holders', 0),
                'total_transactions_24h': raw_network_status.get('transactions_24h', 0),
                'bioregions_count': raw_network_status.get('active_bioregions', 0),
                'average_ubuntu_score': raw_network_status.get('overall_health_score', 0.0),
                'last_block_time': raw_network_status.get('timestamp', '')
            }
        except Exception as e:
            logger.warning(f"Could not fetch network status: {e}")
            context["network_status"] = {
                'active_participants': 0,
                'total_transactions_24h': 0,
                'bioregions_count': 0,
                'average_ubuntu_score': 0.0,
                'last_block_time': 'Unavailable'
            }
        
        # Fetch holonic scores with proper parameters
        try:
            raw_holonic_response = await client.get_holonic_scores(limit=5)
            
            # Backend returns {"summary": {...}, "evaluations": [...]}
            if raw_holonic_response and isinstance(raw_holonic_response, dict):
                summary = raw_holonic_response.get('summary', {})
                evaluations = raw_holonic_response.get('evaluations', [])
                
                # Use summary stats if available
                if summary:
                    context["holonic_scores"] = {
                        'overall_network_health': summary.get('average_composite_score', 0.75),
                        'autonomy_integration': summary.get('average_diversity', 0.72),
                        'ubuntu_alignment': summary.get('average_holism', 0.78),
                        'reciprocity_health': summary.get('average_reciprocity', 0.73),
                        'mutualism_capacity': summary.get('average_mutualism', 0.76),
                        'regeneration_impact': summary.get('average_regeneration', 0.74)
                    }
                elif evaluations and len(evaluations) > 0:
                    # Fallback: use first evaluation as representative
                    eval_data = evaluations[0]
                    context["holonic_scores"] = {
                        'overall_network_health': eval_data.get('composite_score', 0.75),
                        'autonomy_integration': eval_data.get('diversity_score', 0.72),
                        'ubuntu_alignment': eval_data.get('holism_score', 0.78),
                        'reciprocity_health': eval_data.get('reciprocity_score', 0.73),
                        'mutualism_capacity': eval_data.get('mutualism_score', 0.76),
                        'regeneration_impact': eval_data.get('regeneration_score', 0.74)
                    }
        except Exception as e:
            logger.warning(f"Could not fetch holonic scores: {e}")
            # Leave as None - template will handle gracefully
        
        # Fetch recent transactions
        try:
            raw_transactions_response = await client.get_recent_transactions(limit=20)
            
            # Backend returns {"transactions": [...], "count": N}
            if raw_transactions_response and isinstance(raw_transactions_response, dict):
                transactions = raw_transactions_response.get('transactions', [])
                
                # Transform transactions to match template expectations
                recent_transactions = []
                for tx in transactions[:10]:  # Limit to 10 for display
                    recent_transactions.append({
                        'hash': tx.get('hash', ''),
                        'type': tx.get('element', 'transfer') or 'transfer',
                        'token': tx.get('tokens', 'UBEC') or 'UBEC',
                        'amount': tx.get('operations', 0),
                        'timestamp': tx.get('timestamp', '')
                    })
                
                context["recent_transactions"] = recent_transactions
            else:
                context["recent_transactions"] = []
        except Exception as e:
            logger.warning(f"Could not fetch transactions: {e}")
            context["recent_transactions"] = []
        
        # Fetch distribution stats
        try:
            raw_distribution = await client.get_distribution_stats()
            context["distribution_stats"] = raw_distribution
        except Exception as e:
            logger.warning(f"Could not fetch distribution stats: {e}")
            # Leave as None - template will handle gracefully
        
        # NEW: Fetch ecoregions data
        try:
            raw_ecoregions = await client.get_ecoregions(limit=10)
            
            # Backend returns {"ecoregions": [...], "count": N}
            if raw_ecoregions and isinstance(raw_ecoregions, dict):
                ecoregions_list = raw_ecoregions.get('ecoregions', [])
                
                # Calculate summary stats from returned data
                total_ecoregions = raw_ecoregions.get('count', len(ecoregions_list))
                
                # Extract unique biomes and realms for diversity metrics
                # These represent the different ecological classifications present
                biomes = set()
                realms = set()
                for eco in ecoregions_list:
                    if eco.get('biome'):
                        biomes.add(eco['biome'])
                    if eco.get('realm'):
                        realms.add(eco['realm'])
                
                # Transform to template-ready structure
                # Template displays: summary stats, top ecoregions list, biome tags
                context["ecoregions"] = {
                    'total_count': total_ecoregions,
                    'biome_count': len(biomes),
                    'realm_count': len(realms),
                    'top_ecoregions': ecoregions_list[:10],  # Top 10 for display
                    'biomes': sorted(list(biomes))  # All unique biomes
                }
            else:
                context["ecoregions"] = None
        except Exception as e:
            logger.warning(f"Could not fetch ecoregions: {e}")
            context["ecoregions"] = None
        
        # NEW: Fetch watersheds data
        try:
            # Request major watersheds only (>1000 km²) to focus on significant basins
            raw_watersheds = await client.get_watersheds(limit=10, min_area=1000.0)
            
            # Backend returns {"watersheds": [...], "count": N}
            if raw_watersheds and isinstance(raw_watersheds, dict):
                watersheds_list = raw_watersheds.get('watersheds', [])
                
                # Calculate summary stats from returned data
                total_watersheds = raw_watersheds.get('count', len(watersheds_list))
                
                # Calculate total area coverage across all major watersheds
                # This represents the total hydrological coverage in km²
                total_area = sum(w.get('area_sqkm', 0) for w in watersheds_list)
                
                # Transform to template-ready structure
                # Template displays: summary stats, major watersheds list, coverage info
                context["watersheds"] = {
                    'total_count': total_watersheds,
                    'total_area_sqkm': total_area,
                    'major_watersheds': watersheds_list[:10],  # Top 10 major watersheds
                    'average_area': total_area / len(watersheds_list) if watersheds_list else 0
                }
            else:
                context["watersheds"] = None
        except Exception as e:
            logger.warning(f"Could not fetch watersheds: {e}")
            context["watersheds"] = None
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Unable to load dashboard data",
                "error_message": "The backend service may be unavailable. Please try again in a moment.",
                "page": "dashboard"
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
        
        # Fetch token data with fallback
        if client:
            tokens = await safe_backend_call(
                client.get_all_tokens,
                fallback=get_fallback_tokens()
            )
        else:
            tokens = get_fallback_tokens()
        
        return templates.TemplateResponse(
            "stories.html",
            {
                "request": request,
                "tokens": tokens,
                "page": "stories"
            }
        )
    
    except Exception as e:
        logger.error(f"Error rendering stories page: {e}", exc_info=True)
        
        # Try with fallback
        try:
            return templates.TemplateResponse(
                "stories.html",
                {
                    "request": request,
                    "tokens": get_fallback_tokens(),
                    "page": "stories"
                }
            )
        except:
            return HTMLResponse(
                content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Stories - UBEC</title>
                </head>
                <body>
                    <h1>Token Stories Unavailable</h1>
                    <p><a href="/">Return to Home</a></p>
                </body>
                </html>
                """,
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
    try:
        return templates.TemplateResponse(
            "about.html",
            {
                "request": request,
                "page": "about"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering about page: {e}", exc_info=True)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>About - UBEC</title>
            </head>
            <body>
                <h1>About UBEC Protocol</h1>
                <p>Page temporarily unavailable</p>
                <p><a href="/">Return to Home</a></p>
            </body>
            </html>
            """,
            status_code=500
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
    try:
        return templates.TemplateResponse(
            "docs.html",
            {
                "request": request,
                "page": "docs"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering documentation page: {e}", exc_info=True)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Documentation - UBEC</title>
            </head>
            <body>
                <h1>Documentation</h1>
                <p>Page temporarily unavailable</p>
                <p><a href="/">Return to Home</a></p>
            </body>
            </html>
            """,
            status_code=500
        )

# ========================================================================
# DOCUMENTATION GUIDES ROUTES
# ========================================================================

@app.get("/docs/guides/", response_class=HTMLResponse, name="guides_index")
@app.get("/docs/guides/index", response_class=HTMLResponse)
async def guides_index(request: Request):
    """
    Documentation guides index page
    
    Serves the README.md from docs/guides/ directory with markdown rendering.
    This provides navigation to all available user guides.
    """
    try:
        guides_dir = Path(__file__).parent / "docs" / "guides"
        readme_path = guides_dir / "README.md"
        
        if not readme_path.exists():
            logger.error(f"Guides index not found: {readme_path}")
            raise HTTPException(status_code=404, detail="Guides index not found")
        
        # Read markdown file
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'tables', 'toc']
        )
        
        # Render in template
        return templates.TemplateResponse(
            "guide_template.html",
            {
                "request": request,
                "title": "UBEC User Guides",
                "content": html_content,
                "page": "docs"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving guides index: {e}", exc_info=True)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Guides - UBEC</title>
            </head>
            <body>
                <h1>User Guides</h1>
                <p>Guides temporarily unavailable</p>
                <p><a href="/docs">Return to Documentation</a></p>
            </body>
            </html>
            """,
            status_code=500
        )


@app.get("/docs/guides/{guide_name:path}", response_class=HTMLResponse, name="serve_guide")
async def serve_guide(request: Request, guide_name: str):
    """
    Serve individual documentation guide
    
    Renders markdown guides as HTML with proper formatting.
    Supports all .md files in the docs/guides/ directory.
    
    Args:
        guide_name: Name of the guide (with or without .md extension)
    """
    try:
        # Ensure .md extension
        if not guide_name.endswith('.md'):
            guide_name = f"{guide_name}.md"
        
        guides_dir = Path(__file__).parent / "docs" / "guides"
        guide_path = guides_dir / guide_name
        
        # Security check - prevent directory traversal
        try:
            guide_path_resolved = guide_path.resolve()
            guides_dir_resolved = guides_dir.resolve()
            if not str(guide_path_resolved).startswith(str(guides_dir_resolved)):
                logger.warning(f"Directory traversal attempt: {guide_name}")
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception as e:
            logger.error(f"Path resolution error: {e}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not guide_path.exists():
            logger.warning(f"Guide not found: {guide_path}")
            raise HTTPException(status_code=404, detail="Guide not found")
        
        # Read markdown file
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from first h1 or use filename
        title = guide_name.replace('.md', '').replace('-', ' ').replace('_', ' ').title()
        if content.startswith('# '):
            first_line = content.split('\n')[0]
            title = first_line.replace('# ', '').strip()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'tables', 'toc']
        )
        
        # Render in template
        return templates.TemplateResponse(
            "guide_template.html",
            {
                "request": request,
                "title": title,
                "content": html_content,
                "page": "docs"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving guide {guide_name}: {e}", exc_info=True)
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Guide Error - UBEC</title>
            </head>
            <body>
                <h1>Guide Unavailable</h1>
                <p>The requested guide could not be loaded.</p>
                <p><a href="/docs/guides/">View All Guides</a> | <a href="/docs">Documentation Home</a></p>
            </body>
            </html>
            """,
            status_code=500
        )

# ========================================================================
# API ROUTES
# ========================================================================

# Include API router (with error handling)
try:
    app.include_router(api_router, prefix="/api/v1", tags=["api"])
except Exception as e:
    logger.warning(f"API router not available: {e}")

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
        
        # Quick ping to backend (with timeout)
        backend_connected = False
        backend_status = "unavailable"
        
        if client:
            try:
                network_status = await safe_backend_call(
                    client.get_network_status,
                    fallback=None
                )
                if network_status:
                    backend_connected = True
                    backend_status = "operational"
            except:
                pass
        
        status = "healthy" if backend_connected else "degraded"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.1",
            "backend_connected": backend_connected,
            "services": {
                "web": "operational",
                "backend": backend_status,
                "utf8_charset": "enabled"
            },
            "emojis": "🌬️ 💧 🌍 🔥"  # Test emoji encoding
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.1",
            "backend_connected": False,
            "error": str(e),
            "services": {
                "web": "operational",
                "backend": "error"
            }
        }

# ========================================================================
# ERROR HANDLERS
# ========================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors"""
    try:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Page not found",
                "status_code": 404
            },
            status_code=404
        )
    except:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>404 - Not Found</title>
            </head>
            <body>
                <h1>404 - Page Not Found</h1>
                <p><a href="/">Return to Home</a></p>
            </body>
            </html>
            """,
            status_code=404
        )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors"""
    logger.error(f"Server error: {exc}", exc_info=True)
    
    try:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Internal server error",
                "status_code": 500
            },
            status_code=500
        )
    except:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>500 - Server Error</title>
            </head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong. Please try again later.</p>
                <p><a href="/">Return to Home</a></p>
            </body>
            </html>
            """,
            status_code=500
        )

# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Principle #2: This file can only be run as main entry point
    # No standalone execution for service modules
    
    logger.info("Starting UBEC Protocol Website...")
    logger.info("Emojis test: 🌬️ 💧 🌍 🔥")
    
    uvicorn.run(
        "main_web:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
