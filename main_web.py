"""
UBEC Protocol Web Interface - Main Application
================================================

Production version with all field mappings corrected for actual backend API.

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import settings
from utils.backend_client import get_backend_client, close_backend_client
from api.routes import router as api_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UBEC Protocol Web Interface",
    description="Ubuntu Bioregional Economic Commons Protocol - Public Web Interface",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/api/redoc" if settings.ENABLE_API_DOCS else None
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

@app.on_event("startup")
async def startup_event():
    logger.info("Starting UBEC Protocol Web Interface...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Backend API: {settings.BACKEND_API_URL}")
    logger.info("Web interface ready")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down UBEC Protocol Web Interface...")
    await close_backend_client()
    logger.info("Shutdown complete")

@app.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "page": "home"})

@app.get("/stories", response_class=HTMLResponse, name="stories")
async def stories(request: Request):
    return templates.TemplateResponse("stories.html", {"request": request, "page": "stories"})

@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "page": "about"})

@app.get("/protocol", response_class=HTMLResponse, name="protocol")
async def protocol(request: Request):
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
    """Live Dashboard with corrected field mappings for backend API."""
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
        "ecoregions": None,
        "watersheds": None,
        "page": "dashboard"
    }
    
    try:
        client = await get_backend_client()
        
        # ============================================================
        # NETWORK STATUS - CORRECTED FIELD MAPPING
        # ============================================================
        try:
            raw_network_status = await client.get_network_status()
            if raw_network_status and isinstance(raw_network_status, dict):
                # Backend returns: {"network": {...}, "timestamp": "..."}
                # Extract the nested network object
                network_data = raw_network_status.get('network', {})
                
                context["network_status"] = {
                    # CORRECTED: Use network_data with actual backend field names
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
        # HOLONIC SCORES - DISABLED DUE TO DATA STRUCTURE MISMATCH
        # ============================================================
        try:
            raw_holonic_response = await client.get_holonic_scores(limit=5)
            # Backend returns ubuntu_principles with nested dict values
            # Template expects numeric values, so we skip this for now
            # TODO: Update when backend provides numeric scores
            context["holonic_scores"] = None
            logger.debug("Holonic scores temporarily disabled")
        except Exception as e:
            logger.warning(f"Could not fetch holonic scores: {e}")
        
        # ============================================================
        # TRANSACTIONS - FIXED FIELD MAPPING
        # ============================================================
        try:
            raw_transactions_response = await client.get_recent_transactions(limit=20)
            if raw_transactions_response and isinstance(raw_transactions_response, dict):
                transactions = raw_transactions_response.get('transactions', [])
                recent_transactions = []
                for tx in transactions[:10]:
                    involves_tokens = tx.get('involves_tokens', [])
                    token = involves_tokens[0] if involves_tokens else 'XLM'
                    tx_type = 'payment' if involves_tokens else 'transfer'
                    recent_transactions.append({
                        'hash': tx.get('transaction_hash', ''),
                        'timestamp': tx.get('created_at', ''),
                        'amount': float(tx.get('operation_count', 0)),
                        'type': tx_type,
                        'token': token
                    })
                context["recent_transactions"] = recent_transactions
                logger.info(f"Loaded {len(recent_transactions)} transactions")
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
        # ECOREGIONS - FIXED FIELD MAPPING
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
        # WATERSHEDS - FIXED FIELD MAPPING AND UNIT CONVERSION
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

@app.get("/docs", response_class=HTMLResponse, name="docs")
async def docs(request: Request):
    return templates.TemplateResponse("docs.html", {"request": request, "page": "docs"})

app.include_router(api_router, prefix="/api/v1", tags=["api"])

@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {
        "status": "healthy",
        "service": "ubec-web-interface",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }

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
