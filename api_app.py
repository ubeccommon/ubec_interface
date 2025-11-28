"""
UBEC DAO Protocol - API Gateway Service
====================================

Dedicated API gateway for api.ubec.network.

Security:
    - Public-facing API endpoint
    - Authenticates to backend using API key
    - Backend only accepts requests from this gateway

Clean URL structure:
    https://api.ubec.network/v1/tokens
    https://api.ubec.network/v1/network-status
    https://api.ubec.network/docs

Run:
    uvicorn api_app:app --host 0.0.0.0 --port 8002

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import os
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import settings

# ========================================================================
# LOGGING CONFIGURATION
# ========================================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================================================
# BACKEND CONFIGURATION
# ========================================================================

BACKEND_URL = "http://92.205.230.245:8000"
API_GATEWAY_KEY = os.getenv("API_GATEWAY_KEY", "")

if not API_GATEWAY_KEY:
    logger.warning("API_GATEWAY_KEY not set - backend requests may fail")

# ========================================================================
# BACKEND CLIENT
# ========================================================================

async def fetch_from_backend(endpoint: str, params: dict = None) -> Dict:
    """
    Fetch data from backend server with API key authentication.
    
    Args:
        endpoint: Backend API endpoint (e.g., "/api/v1/tokens")
        params: Query parameters
    
    Returns:
        JSON response from backend
    """
    url = f"{BACKEND_URL}{endpoint}"
    headers = {
        "X-API-Gateway-Key": API_GATEWAY_KEY,
        "X-Forwarded-For": "92.205.28.58",
        "User-Agent": "UBEC-API-Gateway/1.0"
    }
    
    logger.debug(f"Backend request: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 403:
                    logger.error("Backend rejected request - check API_GATEWAY_KEY")
                    raise HTTPException(status_code=503, detail="Backend authentication failed")
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        logger.error(f"Backend error for {url}: {e.status}")
        raise HTTPException(status_code=e.status, detail=str(e.message))
    except aiohttp.ClientError as e:
        logger.error(f"Backend connection error: {e}")
        raise HTTPException(status_code=503, detail="Backend service unavailable")

# ========================================================================
# APPLICATION SETUP
# ========================================================================

app = FastAPI(
    title="UBEC DAO Protocol API",
    description="""
## Ubuntu Bioregional Economic Commons DAO Protocol - Public API

### Base URL
`https://api.ubec.network`

### Endpoints
- `/v1/tokens` - All UBEC tokens
- `/v1/network-status` - Network health metrics
- `/v1/transactions/recent` - Recent blockchain activity
- `/v1/holonic-scores` - Ubuntu principle scores
- `/v1/distribution` - Token distribution compliance
- `/v1/bioregions` - Bioregion data
- `/v1/ecoregions` - Ecoregion data
- `/v1/watersheds` - Watershed data

### Documentation
Visit `/docs` for interactive Swagger UI or `/redoc` for ReDoc.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "UBEC DAO Protocol",
        "url": "https://bioregional.ubec.network",
    }
)

# ========================================================================
# MIDDLEWARE
# ========================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ========================================================================
# LIFECYCLE EVENTS
# ========================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting UBEC DAO Protocol API Gateway")
    logger.info(f"Backend: {BACKEND_URL}")
    logger.info(f"API Key configured: {'Yes' if API_GATEWAY_KEY else 'NO - WARNING!'}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API Gateway")

# ========================================================================
# ROOT & HEALTH
# ========================================================================

@app.get("/", response_class=JSONResponse, include_in_schema=False)
async def root():
    return {
        "service": "UBEC DAO Protocol API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_class=JSONResponse, tags=["System"])
async def health():
    return {"status": "healthy", "service": "ubec-api-gateway", "timestamp": datetime.now().isoformat()}


@app.get("/v1/health", response_class=JSONResponse, tags=["System"])
async def v1_health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ========================================================================
# TOKEN ENDPOINTS
# ========================================================================

@app.get("/v1/tokens", response_class=JSONResponse, tags=["Tokens"], summary="Get all tokens")
async def get_tokens():
    """Get all four UBEC tokens: UBEC, UBECrc, UBECgpi, UBECtt"""
    data = await fetch_from_backend("/api/v1/tokens")
    if isinstance(data, dict) and "tokens" in data:
        return data["tokens"]
    return data


@app.get("/v1/tokens/{token_code}", response_class=JSONResponse, tags=["Tokens"], summary="Get specific token")
async def get_token(token_code: str):
    """Get details for a specific token."""
    data = await fetch_from_backend("/api/v1/tokens")
    tokens = data.get("tokens", data) if isinstance(data, dict) else data
    for token in tokens:
        if token.get("code") == token_code.upper() or token.get("asset_code") == token_code.upper():
            return token
    raise HTTPException(status_code=404, detail=f"Token {token_code} not found")

# ========================================================================
# NETWORK ENDPOINTS
# ========================================================================

@app.get("/v1/network-status", response_class=JSONResponse, tags=["Network"], summary="Get network status")
async def get_network_status():
    """Get current network status and health metrics."""
    return await fetch_from_backend("/api/v1/network-status")

# ========================================================================
# TRANSACTION ENDPOINTS
# ========================================================================

@app.get("/v1/transactions/recent", response_class=JSONResponse, tags=["Transactions"], summary="Get recent transactions")
async def get_recent_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get recent blockchain transactions."""
    return await fetch_from_backend("/api/v1/transactions/recent", {"limit": limit, "offset": offset})

# ========================================================================
# HOLONIC ENDPOINTS
# ========================================================================

@app.get("/v1/holonic-scores", response_class=JSONResponse, tags=["Holonic"], summary="Get holonic scores")
async def get_holonic_scores(
    limit: int = Query(default=50, ge=1, le=500),
    category: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0, le=1)
):
    """Get Ubuntu principle evaluation scores."""
    params = {"limit": limit}
    if category:
        params["category"] = category
    if min_score is not None:
        params["min_score"] = min_score
    return await fetch_from_backend("/api/v1/holonic-scores", params)

# ========================================================================
# DISTRIBUTION ENDPOINTS
# ========================================================================

@app.get("/v1/distribution", response_class=JSONResponse, tags=["Distribution"], summary="Get distribution stats")
async def get_distribution():
    """Get token distribution statistics for 75/20/5 compliance."""
    return await fetch_from_backend("/api/v1/distribution")


@app.get("/v1/token-audit/{token_code}", response_class=JSONResponse, tags=["Distribution"], summary="Get token audit")
async def get_token_audit(token_code: str):
    """Get comprehensive token audit data."""
    return await fetch_from_backend(f"/api/v1/token-audit/{token_code.upper()}")


@app.get("/v1/liquidity-pools", response_class=JSONResponse, tags=["Distribution"], summary="Get liquidity pools")
async def get_liquidity_pools(token_code: Optional[str] = None):
    """Get liquidity pool information."""
    params = {"token_code": token_code.upper()} if token_code else None
    return await fetch_from_backend("/api/v1/liquidity-pools", params)

# ========================================================================
# BIOREGION ENDPOINTS
# ========================================================================

@app.get("/v1/bioregions", response_class=JSONResponse, tags=["Bioregions"], summary="Get bioregions")
async def get_bioregions(limit: int = Query(default=50, ge=1, le=500)):
    """Get bioregion data."""
    return await fetch_from_backend("/api/v1/bioregions", {"limit": limit})


@app.get("/v1/bioregions/count", response_class=JSONResponse, tags=["Bioregions"], summary="Get bioregion count")
async def get_bioregion_count():
    """Get total bioregion count."""
    return await fetch_from_backend("/api/v1/bioregions/count")


@app.get("/v1/bioregions/summary", response_class=JSONResponse, tags=["Bioregions"], summary="Get bioregion summary")
async def get_bioregion_summary():
    """Get bioregion summary statistics."""
    return await fetch_from_backend("/api/v1/bioregions/summary")

# ========================================================================
# GEOGRAPHIC ENDPOINTS
# ========================================================================

@app.get("/v1/ecoregions", response_class=JSONResponse, tags=["Geographic"], summary="Get ecoregions")
async def get_ecoregions(limit: int = Query(default=50, ge=1, le=500)):
    """Get ecoregion data from Ecoregions2017."""
    return await fetch_from_backend("/api/v1/ecoregions", {"limit": limit})


@app.get("/v1/watersheds", response_class=JSONResponse, tags=["Geographic"], summary="Get watersheds")
async def get_watersheds(limit: int = Query(default=50, ge=1, le=500)):
    """Get watershed data from FEOW HydroSHEDS."""
    return await fetch_from_backend("/api/v1/watersheds", {"limit": limit})

# ========================================================================
# SYSTEM ENDPOINTS
# ========================================================================

@app.get("/v1/system/info", response_class=JSONResponse, tags=["System"], summary="Get system info")
async def get_system_info():
    """Get API system information."""
    return {
        "name": "UBEC DAO Protocol API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/v1/system/health", response_class=JSONResponse, tags=["System"], summary="Get detailed health")
async def get_system_health():
    """Get detailed health including backend status."""
    health = {
        "api_gateway": "healthy",
        "backend": "unknown",
        "timestamp": datetime.now().isoformat()
    }
    try:
        backend_health = await fetch_from_backend("/api/v1/health")
        health["backend"] = "healthy"
        health["backend_status"] = backend_health
    except:
        health["backend"] = "unhealthy"
    return health
