"""
UBEC Protocol Web Interface - Main Application
================================================

Production version with all field mappings corrected for actual backend API.

FIXED v2.5.2: Transactions now pass raw API response with operations array
- Template handles operations directly (type, asset_code, amount, from/to)
- Previously was using operation_count as amount (bug)

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

# Directory where guide markdown files are stored
GUIDES_DIR = Path("static/docs/guides")

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
    """Home page with live token and network data from backend API."""
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
            # get_all_tokens() returns a list directly (extracts from {"tokens": [...]})
            if tokens_response and isinstance(tokens_response, list):
                context["tokens"] = tokens_response
                # Calculate total unique holders across all tokens
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
        "token_audit": None,
        "liquidity_pools": None,
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
        # HOLONIC SCORES - Transform backend response to template format
        # Backend: ubuntu_principles.{diversity,reciprocity,mutualism,regeneration}.average
        # Template: flat structure with percentage-ready values
        # ============================================================
        try:
            raw_holonic_response = await client.get_holonic_scores(limit=50)
            if raw_holonic_response and isinstance(raw_holonic_response, dict):
                principles = raw_holonic_response.get('ubuntu_principles', {})
                
                # Extract averages from nested structure
                diversity = principles.get('diversity', {}).get('average', 0) or 0
                reciprocity = principles.get('reciprocity', {}).get('average', 0) or 0
                mutualism = principles.get('mutualism', {}).get('average', 0) or 0
                regeneration = principles.get('regeneration', {}).get('average', 0) or 0
                
                # Calculate overall health as weighted average
                overall = (diversity + reciprocity + mutualism + regeneration) / 4
                
                # Transform to template-expected format
                context["holonic_scores"] = {
                    "overall_network_health": overall,
                    "autonomy_integration": diversity,      # Diversity maps to autonomy
                    "ubuntu_alignment": diversity,          # Use diversity as ubuntu alignment
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
        # TRANSACTIONS - Pass raw API response for v2.5.2 format
        # Template handles the operations array directly
        # ============================================================
        try:
            raw_transactions_response = await client.get_recent_transactions(limit=20)
            if raw_transactions_response and isinstance(raw_transactions_response, dict):
                # Pass the full response - template handles transactions array with operations
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
        # TOKEN AUDIT - Real wallet balances for transparency
        # Backend endpoint /api/v1/token-audit (v2.5.5+)
        # ============================================================
        try:
            raw_audit = await client.get_token_audit(token_code="UBEC")
            context["token_audit"] = raw_audit
            logger.info("Loaded token audit data")
        except Exception as e:
            logger.warning(f"Could not fetch token audit: {e}")
        
        # ============================================================
        # LIQUIDITY POOLS - DEX pool information
        # Backend endpoint /api/v1/liquidity-pools (v2.5.6+)
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

# ========================================================================
# DOCUMENTATION GUIDES ROUTES
# ========================================================================

@app.get("/docs/guides/", response_class=HTMLResponse, name="guides_index")
async def guides_index(request: Request):
    """
    Display an index of all available guides.
    
    Returns:
        HTML page listing all available documentation guides
    """
    try:
        guides = []
        if GUIDES_DIR.exists():
            for file in GUIDES_DIR.glob("*.md"):
                # Parse filename to create friendly title
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
    """
    Display a specific guide document.
    
    Args:
        guide_slug: URL-friendly guide identifier (e.g., 'participation-guide')
    
    Returns:
        Rendered HTML page with guide content
    """
    try:
        # Construct file path
        guide_file = GUIDES_DIR / f"{guide_slug}.md"
        
        if not guide_file.exists():
            logger.warning(f"Guide not found: {guide_slug}")
            raise HTTPException(status_code=404, detail=f"Guide '{guide_slug}' not found")
        
        # Read and convert markdown to HTML
        with open(guide_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'toc', 'codehilite', 'fenced_code']
        )
        
        # Extract title from first heading or use slug
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
    """
    Download raw markdown file.
    
    Args:
        guide_slug: URL-friendly guide identifier
    
    Returns:
        Raw markdown file for download
    """
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
# DOCUMENTATION SEARCH API
# ========================================================================

@app.get("/api/v1/docs/search", response_class=JSONResponse, name="docs_search")
async def docs_search(q: str = "", limit: int = 10):
    """
    Search through documentation guides.
    
    Args:
        q: Search query string
        limit: Maximum number of results (default 10)
    
    Returns:
        JSON array of matching documents with title, excerpt, and URL
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "query": q, "message": "Query must be at least 2 characters"}
    
    query = q.lower().strip()
    results = []
    
    try:
        if not GUIDES_DIR.exists():
            return {"results": [], "query": q, "message": "Guides directory not found"}
        
        for file in GUIDES_DIR.glob("*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content_lower = content.lower()
                
                # Check if query matches
                if query in content_lower:
                    # Extract title from first heading
                    lines = content.split('\n')
                    title = file.stem.replace("-", " ").replace("_", " ").title()
                    for line in lines:
                        if line.startswith('# '):
                            title = line.replace('# ', '').strip()
                            break
                    
                    # Find excerpt with context around the match
                    excerpt = ""
                    match_pos = content_lower.find(query)
                    if match_pos != -1:
                        # Get surrounding context (100 chars before and 150 after)
                        start = max(0, match_pos - 100)
                        end = min(len(content), match_pos + len(query) + 150)
                        
                        # Find word boundaries
                        if start > 0:
                            while start > 0 and content[start] not in ' \n\t':
                                start -= 1
                            start += 1
                        
                        if end < len(content):
                            while end < len(content) and content[end] not in ' \n\t':
                                end += 1
                        
                        excerpt = content[start:end].strip()
                        excerpt = ' '.join(excerpt.split())  # Normalize whitespace
                        excerpt = excerpt.replace('#', '').strip()
                        
                        if start > 0:
                            excerpt = "..." + excerpt
                        if end < len(content):
                            excerpt = excerpt + "..."
                    
                    # Count occurrences for relevance scoring
                    occurrences = content_lower.count(query)
                    
                    # Check if match is in title (higher relevance)
                    title_match = query in title.lower()
                    
                    results.append({
                        "title": title,
                        "slug": file.stem,
                        "url": f"/docs/guides/{file.stem}",
                        "excerpt": excerpt[:300] if excerpt else "",
                        "relevance": occurrences + (10 if title_match else 0)
                    })
                    
            except Exception as e:
                logger.warning(f"Error reading guide {file.name}: {e}")
                continue
        
        # Sort by relevance (title matches first, then by occurrence count)
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Limit results
        results = results[:limit]
        
        # Remove relevance score from output
        for r in results:
            del r["relevance"]
        
        return {
            "results": results,
            "query": q,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"results": [], "query": q, "error": str(e)}

# ========================================================================
# API ROUTES AND SYSTEM ENDPOINTS
# ========================================================================

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
