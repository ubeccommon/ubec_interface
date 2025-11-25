"""
UBEC Protocol Web Interface - Main Application (CORRECTED)
============================================================

FIXED: Field mappings updated to match actual backend API response format
- Transactions: transaction_hash → hash, created_at → timestamp, operation_count → amount
- Watersheds: huc12 → feow_id, area_acres → area_sqkm (with conversion)
- Ecoregions: eco_code → eco_id, eco_name → name, biome_name → biome

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
    """Live Dashboard - FIXED field mappings"""
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
        
        try:
            raw_holonic_response = await client.get_holonic_scores(limit=5)
            if raw_holonic_response and isinstance(raw_holonic_response, dict):
                summary = raw_holonic_response.get('summary', {})
                evaluations = raw_holonic_response.get('evaluations', [])
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
        
        # TRANSACTIONS - FIXED FIELD MAPPING
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
            else:
                context["recent_transactions"] = []
        except Exception as e:
            logger.warning(f"Could not fetch transactions: {e}")
            context["recent_transactions"] = []
        
        try:
            raw_distribution = await client.get_distribution_stats()
            context["distribution_stats"] = raw_distribution
        except Exception as e:
            logger.warning(f"Could not fetch distribution stats: {e}")
        
        # ECOREGIONS - FIXED FIELD MAPPING
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
            else:
                context["ecoregions"] = None
        except Exception as e:
            logger.warning(f"Could not fetch ecoregions: {e}")
            context["ecoregions"] = None
        
        # WATERSHEDS - FIXED FIELD MAPPING AND UNIT CONVERSION
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
