"""
UBEC Protocol Web Interface - Main Application
================================================

REFACTORED: UI-only frontend that fetches data from api.ubec.network

This module serves:
    - Public web pages (home, dashboard, about, protocol, stories)
    - Documentation guides
    - Static assets

Data is fetched from the dedicated API gateway at api.ubec.network,
NOT directly from the backend. This ensures:
    - Single source of truth for all API data
    - Clean separation between UI and API
    - External developers use the same API as the frontend

Architecture:
    bioregional.ubec.network (this service, port 8001)
        ↓ fetches data from
    api.ubec.network (API gateway, port 8002)
        ↓ proxies to
    Backend API (92.205.230.245:8000)

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import logging
import markdown
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import settings
from utils.backend_client import get_backend_client, close_backend_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================================================
# APPLICATION SETUP
# ========================================================================

app = FastAPI(
    title="UBEC Protocol Web Interface",
    description="Ubuntu Bioregional Economic Commons Protocol - Public Web Interface",
    version="1.0.0",
    # API docs disabled - use api.ubec.network for API documentation
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Directory where guide markdown files are stored
GUIDES_DIR = Path("static/docs/guides")

# ========================================================================
# LIFECYCLE EVENTS
# ========================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting UBEC Protocol Web Interface")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"API Source: {settings.BACKEND_API_URL}")
    logger.info("Web interface ready on port 8001")
    logger.info("NOTE: API moved to api.ubec.network")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down UBEC Protocol Web Interface...")
    await close_backend_client()
    logger.info("Shutdown complete")

# ========================================================================
# PUBLIC WEB PAGES
# ========================================================================

@app.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    """Home page with live token and network data."""
    context = {
        "request": request,
        "page": "home",
        "tokens": [],
        "network": {
            "participants": 0,
            "bioregions": 0,
            "transactions": 0,
            "health": "unknown"
        },
        "total_holders": 0
    }
    
    try:
        client = await get_backend_client()
        
        # Fetch token data
        try:
            tokens_response = await client.get_all_tokens()
            if tokens_response and isinstance(tokens_response, list):
                context["tokens"] = tokens_response
                context["total_holders"] = sum(
                    t.get('holder_count', 0) for t in context["tokens"]
                )
                logger.info(f"Loaded {len(context['tokens'])} tokens")
        except Exception as e:
            logger.warning(f"Could not fetch tokens: {e}")
        
        # Fetch network status
        try:
            network_response = await client.get_network_status()
            if network_response and isinstance(network_response, dict):
                context["network"] = network_response.get('network', context["network"])
                logger.info(f"Network: {context['network'].get('participants', 0)} participants")
        except Exception as e:
            logger.warning(f"Could not fetch network status: {e}")
            
    except Exception as e:
        logger.error(f"Error fetching home page data: {e}")
    
    return templates.TemplateResponse("home.html", context)


@app.get("/stories", response_class=HTMLResponse, name="stories")
async def stories(request: Request):
    """Community stories page."""
    return templates.TemplateResponse("stories.html", {"request": request, "page": "stories"})


@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    """About page."""
    return templates.TemplateResponse("about.html", {"request": request, "page": "about"})


@app.get("/protocol", response_class=HTMLResponse, name="protocol")
async def protocol(request: Request):
    """Protocol documentation page."""
    try:
        return templates.TemplateResponse("protocol.html", {"request": request, "page": "protocol"})
    except:
        return HTMLResponse(
            content="""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Protocol - UBEC</title></head>
            <body><h1>Protocol Overview Unavailable</h1><p><a href="/">Return to Home</a></p></body></html>""",
            status_code=500
        )


@app.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    """Live Dashboard with network metrics."""
    context = {
        "request": request,
        "network_status": {
            'active_participants': 0,
            'total_transactions_24h': 0,
            'bioregions_count': 0,
            'average_ubuntu_score': 0.0,
            'last_block_time': 'Unavailable'
        },
        "holonic_scores": None,
        "recent_transactions": [],
        "distribution_stats": None,
        "token_audit": None,
        "liquidity_pools": None,
        "ecoregions": None,
        "watersheds": None,
        "page": "dashboard"
    }
    
    try:
        client = await get_backend_client()
        
        # ============================================================
        # NETWORK STATUS
        # ============================================================
        try:
            raw_network_status = await client.get_network_status()
            if raw_network_status and isinstance(raw_network_status, dict):
                network_data = raw_network_status.get('network', {})
                
                context["network_status"] = {
                    'active_participants': network_data.get('participants', 0),
                    'total_transactions_24h': network_data.get('transactions', 0),
                    'bioregions_count': network_data.get('bioregions', 0),
                    'average_ubuntu_score': network_data.get('ubuntu_alignment', 0.0),
                    'last_block_time': raw_network_status.get('timestamp', 'Unavailable')
                }
                logger.info(f"Network status: {context['network_status']['active_participants']} participants")
        except Exception as e:
            logger.warning(f"Could not fetch network status: {e}")
        
        # ============================================================
        # HOLONIC SCORES
        # ============================================================
        try:
            raw_holonic_response = await client.get_holonic_scores(limit=50)
            if raw_holonic_response and isinstance(raw_holonic_response, dict):
                principles = raw_holonic_response.get('ubuntu_principles', {})
                
                diversity = principles.get('diversity', {}).get('average', 0) or 0
                reciprocity = principles.get('reciprocity', {}).get('average', 0) or 0
                mutualism = principles.get('mutualism', {}).get('average', 0) or 0
                regeneration = principles.get('regeneration', {}).get('average', 0) or 0
                
                overall = (diversity + reciprocity + mutualism + regeneration) / 4
                
                context["holonic_scores"] = {
                    "overall_network_health": overall,
                    "autonomy_integration": diversity,
                    "ubuntu_alignment": diversity,
                    "reciprocity_health": reciprocity,
                    "mutualism_capacity": mutualism,
                    "regeneration_impact": regeneration,
                    "account_count": raw_holonic_response.get('account_count', 0)
                }
                logger.info(f"Loaded holonic scores: overall={overall:.2%}")
            else:
                context["holonic_scores"] = None
        except Exception as e:
            logger.warning(f"Could not fetch holonic scores: {e}")
        
        # ============================================================
        # TRANSACTIONS
        # ============================================================
        try:
            raw_transactions_response = await client.get_recent_transactions(limit=20)
            if raw_transactions_response and isinstance(raw_transactions_response, dict):
                context["recent_transactions"] = raw_transactions_response
                tx_count = len(raw_transactions_response.get('transactions', []))
                logger.info(f"Loaded {tx_count} transactions with operations")
            else:
                context["recent_transactions"] = []
        except Exception as e:
            logger.warning(f"Could not fetch transactions: {e}")
            context["recent_transactions"] = []
        
        # ============================================================
        # DISTRIBUTION STATS
        # ============================================================
        try:
            raw_distribution = await client.get_distribution_stats()
            context["distribution_stats"] = raw_distribution
        except Exception as e:
            logger.warning(f"Could not fetch distribution stats: {e}")
        
        # ============================================================
        # TOKEN AUDIT
        # ============================================================
        try:
            raw_audit = await client.get_token_audit(token_code="UBEC")
            context["token_audit"] = raw_audit
            logger.info("Loaded token audit data")
        except Exception as e:
            logger.warning(f"Could not fetch token audit: {e}")
        
        # ============================================================
        # LIQUIDITY POOLS
        # ============================================================
        try:
            raw_lp_data = await client.get_liquidity_pools()
            context["liquidity_pools"] = raw_lp_data
            pool_count = len(raw_lp_data.get('pools', [])) if raw_lp_data else 0
            logger.info(f"Loaded {pool_count} liquidity pools")
        except Exception as e:
            logger.warning(f"Could not fetch liquidity pools: {e}")
            context["liquidity_pools"] = None
        
        # ============================================================
        # ECOREGIONS
        # ============================================================
        try:
            raw_ecoregions = await client.get_ecoregions(limit=10)
            if raw_ecoregions and isinstance(raw_ecoregions, dict):
                ecoregions_list = raw_ecoregions.get('ecoregions', [])
                total_ecoregions = raw_ecoregions.get('count', len(ecoregions_list))
                transformed_ecoregions = []
                for eco in ecoregions_list:
                    transformed_ecoregions.append({
                        'eco_id': eco.get('eco_code', ''),
                        'name': eco.get('eco_name', ''),
                        'biome': eco.get('biome_name', ''),
                        'realm': eco.get('realm', ''),
                        'biome_num': eco.get('biome_num', 0)
                    })
                biomes = set(e['biome'] for e in transformed_ecoregions if e['biome'])
                realms = set(e['realm'] for e in transformed_ecoregions if e['realm'])
                context["ecoregions"] = {
                    'total_ecoregions': total_ecoregions,
                    'biome_types': len(biomes),
                    'biogeographic_realms': len(realms),
                    'ecoregions': transformed_ecoregions,
                    'biomes': sorted(list(biomes))
                }
                logger.info(f"Loaded {len(transformed_ecoregions)} ecoregions")
            else:
                context["ecoregions"] = None
        except Exception as e:
            logger.warning(f"Could not fetch ecoregions: {e}")
            context["ecoregions"] = None
        
        # ============================================================
        # WATERSHEDS
        # ============================================================
        try:
            raw_watersheds = await client.get_watersheds(limit=10)
            if raw_watersheds and isinstance(raw_watersheds, dict):
                watersheds_list = raw_watersheds.get('watersheds', [])
                total_watersheds = raw_watersheds.get('count', len(watersheds_list))
                transformed_watersheds = []
                for ws in watersheds_list:
                    area_acres = ws.get('area_acres', 0) or 0
                    area_sqkm = area_acres * 0.00404686
                    transformed_watersheds.append({
                        'feow_id': ws.get('huc12', ''),
                        'name': ws.get('name', ''),
                        'area_sqkm': area_sqkm
                    })
                total_area = sum(w['area_sqkm'] for w in transformed_watersheds)
                context["watersheds"] = {
                    'total_count': total_watersheds,
                    'total_area_sqkm': total_area,
                    'major_watersheds': transformed_watersheds,
                    'average_area': total_area / len(transformed_watersheds) if transformed_watersheds else 0
                }
                logger.info(f"Loaded {len(transformed_watersheds)} watersheds")
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
                "status_code": 500,
                "error_message": "The backend service is unavailable at the moment. Please try again in a moment.",
                "page": "error"
            }
        )

# ========================================================================
# DOCUMENTATION PAGES
# ========================================================================

@app.get("/docs", response_class=HTMLResponse, name="docs")
async def docs(request: Request):
    """Documentation landing page."""
    return templates.TemplateResponse("docs.html", {"request": request, "page": "docs"})


@app.get("/docs/guides/", response_class=HTMLResponse, name="guides_index")
async def guides_index(request: Request):
    """Display index of all available guides."""
    try:
        guides = []
        if GUIDES_DIR.exists():
            for file in GUIDES_DIR.glob("*.md"):
                title = file.stem.replace("-", " ").replace("_", " ").title()
                slug = file.stem
                guides.append({
                    "title": title,
                    "slug": slug,
                    "filename": file.name
                })
        
        guides.sort(key=lambda x: x['title'])
        
        return templates.TemplateResponse(
            "guides_index.html",
            {
                "request": request,
                "guides": guides,
                "page": "guides"
            }
        )
    except Exception as e:
        logger.error(f"Error loading guides index: {e}")
        raise HTTPException(status_code=500, detail="Unable to load guides")


@app.get("/docs/guides/{guide_slug}", response_class=HTMLResponse, name="guide_detail")
async def guide_detail(request: Request, guide_slug: str):
    """Display a specific guide document."""
    try:
        guide_file = GUIDES_DIR / f"{guide_slug}.md"
        
        if not guide_file.exists():
            logger.warning(f"Guide not found: {guide_slug}")
            raise HTTPException(status_code=404, detail=f"Guide '{guide_slug}' not found")
        
        with open(guide_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'toc', 'codehilite', 'fenced_code']
        )
        
        title = guide_slug.replace("-", " ").title()
        if markdown_content.startswith('# '):
            title = markdown_content.split('\n')[0].replace('# ', '')
        
        return templates.TemplateResponse(
            "guide_detail.html",
            {
                "request": request,
                "title": title,
                "content": html_content,
                "guide_slug": guide_slug,
                "page": "guides"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading guide {guide_slug}: {e}")
        raise HTTPException(status_code=500, detail="Unable to load guide")


@app.get("/docs/guides/{guide_slug}/raw", response_class=FileResponse, name="guide_raw")
async def guide_raw(guide_slug: str):
    """Download raw markdown file."""
    try:
        guide_file = GUIDES_DIR / f"{guide_slug}.md"
        
        if not guide_file.exists():
            raise HTTPException(status_code=404, detail=f"Guide '{guide_slug}' not found")
        
        return FileResponse(
            path=guide_file,
            media_type='text/markdown',
            filename=f"{guide_slug}.md"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading guide {guide_slug}: {e}")
        raise HTTPException(status_code=500, detail="Unable to download guide")

# ========================================================================
# HEALTH CHECK
# ========================================================================

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ubec-web-interface",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "api_note": "API moved to api.ubec.network"
    }

# ========================================================================
# ERROR HANDLERS
# ========================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 404,
            "error_message": "The requested page could not be found.",
            "page": "error"
        },
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "error_message": "An internal server error occurred. Please try again later.",
            "page": "error"
        },
        status_code=500
    )
