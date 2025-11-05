"""
UBEC Protocol Website - API Routes
===================================

RESTful API endpoints for fetching UBEC Protocol data.

Implements:
    - Principle #5: Strict Async Operations
    - Principle #9: Integrated Rate Limiting
    - Principle #10: Clear Separation of Concerns

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from utils.backend_client import BackendAPIClient
from config.settings import settings

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()

# ========================================================================
# DEPENDENCY: Backend Client
# ========================================================================

async def get_backend_client() -> BackendAPIClient:
    """
    Dependency to get backend API client instance.
    
    Principle #4: Single source of truth - backend as data source
    """
    # This will be provided by the main app
    from main_web import get_backend_client as get_client
    return await get_client()

# ========================================================================
# TOKEN ENDPOINTS
# ========================================================================

@router.get("/tokens", response_class=JSONResponse, summary="Get all tokens")
async def get_all_tokens(
    client: BackendAPIClient = Depends(get_backend_client)
) -> List[Dict]:
    """
    Get information about all four UBEC tokens.
    
    Returns:
        List of token objects containing:
        - token_code: Token symbol (UBEC, UBECrc, UBECgpi, UBECtt)
        - element: Associated element (Air, Water, Earth, Fire)
        - ubuntu_principle: Ubuntu principle represented
        - total_supply: Current total supply
        - holders_count: Number of token holders
        - status: Token status (live, pending, etc.)
    """
    try:
        tokens = await client.get_all_tokens()
        return tokens
    except Exception as e:
        logger.error(f"Error fetching tokens: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch token data")


@router.get("/tokens/{token_code}", response_class=JSONResponse, summary="Get specific token")
async def get_token_by_code(
    token_code: str,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get detailed information about a specific token.
    
    Args:
        token_code: Token symbol (UBEC, UBECrc, UBECgpi, or UBECtt)
    
    Returns:
        Detailed token object with full information
    """
    try:
        token = await client.get_token_by_code(token_code.upper())
        return token
    except Exception as e:
        logger.error(f"Error fetching token {token_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch token {token_code}")

# ========================================================================
# NETWORK STATUS ENDPOINTS
# ========================================================================

@router.get("/network/status", response_class=JSONResponse, summary="Get network status")
async def get_network_status(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get current network status and metrics.
    
    Returns:
        Network status object containing:
        - active_participants: Current number of active participants
        - total_transactions_24h: Transaction count in last 24 hours
        - average_ubuntu_score: Network-wide Ubuntu alignment score
        - bioregions_count: Number of active bioregions
        - network_health: Overall health status
    """
    try:
        status = await client.get_network_status()
        return status
    except Exception as e:
        logger.error(f"Error fetching network status: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch network status")

# ========================================================================
# BIOREGION ENDPOINTS (NEW!)
# ========================================================================

@router.get("/bioregions", response_class=JSONResponse, summary="Get all bioregions")
async def get_all_bioregions(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get all bioregions with detailed information.
    
    Returns:
        Dictionary containing:
        - count: Total number of bioregions
        - summary: Summary statistics (total members, averages, etc.)
        - bioregions: List of bioregion objects with details
        - timestamp: When data was fetched
    """
    try:
        bioregions = await client.get_bioregions()
        return bioregions
    except Exception as e:
        logger.error(f"Error fetching bioregions: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch bioregions")


@router.get("/bioregions/count", response_class=JSONResponse, summary="Get bioregion count")
async def get_bioregion_count(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get total count of active bioregions.
    
    Returns:
        Dictionary with count field
    """
    try:
        count = await client.get_bioregion_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error fetching bioregion count: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch bioregion count")


@router.get("/bioregions/{bioregion_id}", response_class=JSONResponse, summary="Get specific bioregion")
async def get_bioregion(
    bioregion_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get detailed information about a specific bioregion.
    
    Args:
        bioregion_id: Unique identifier of the bioregion
    
    Returns:
        Detailed bioregion object containing:
        - id: Bioregion identifier
        - name: Bioregion name
        - member_count: Number of members
        - autonomy_score: Autonomy score (0-1)
        - integration_score: Integration score (0-1)
        - health_rating: Overall health rating
        - ubuntu_scores: Ubuntu principle alignment scores
        - emerged_at: When bioregion was established
        - status: Current status (active, dissolved, etc.)
    """
    try:
        bioregion = await client.get_bioregion(bioregion_id)
        return bioregion
    except Exception as e:
        logger.error(f"Error fetching bioregion {bioregion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch bioregion {bioregion_id}")

# ========================================================================
# HOLONIC EVALUATION ENDPOINTS
# ========================================================================

@router.get("/holonic/scores", response_class=JSONResponse, summary="Get holonic scores")
async def get_holonic_scores(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get latest holonic evaluation scores.
    
    Returns:
        Holonic scores object containing:
        - autonomy_integration: Autonomy integration score (0-1)
        - ubuntu_alignment: Ubuntu alignment score (0-1)
        - reciprocity_health: Reciprocity health score (0-1)
        - mutualism_capacity: Mutualism capacity score (0-1)
        - regeneration_impact: Regeneration impact score (0-1)
        - overall_network_health: Overall network health score (0-1)
        - category_distribution: Distribution across holonic categories
    """
    try:
        scores = await client.get_holonic_scores()
        return scores
    except Exception as e:
        logger.error(f"Error fetching holonic scores: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch holonic scores")


@router.get("/holonic/categories", response_class=JSONResponse, summary="Get holonic categories")
async def get_holder_categories(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get holonic category distribution.
    
    Returns:
        Distribution of participants across holonic categories:
        - system: System-level participants
        - catalyst: Catalyst participants
        - integrator: Integrator participants
        - autonomous: Autonomous participants
    """
    try:
        categories = await client.get_holder_categories()
        return categories
    except Exception as e:
        logger.error(f"Error fetching holonic categories: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch holonic categories")

# ========================================================================
# TRANSACTION ENDPOINTS
# ========================================================================

@router.get("/transactions/recent", response_class=JSONResponse, summary="Get recent transactions")
async def get_recent_transactions(
    limit: int = Query(default=20, ge=1, le=100, description="Number of transactions to return"),
    client: BackendAPIClient = Depends(get_backend_client)
) -> List[Dict]:
    """
    Get recent blockchain transactions.
    
    Args:
        limit: Maximum number of transactions to return (1-100)
    
    Returns:
        List of recent transaction objects
    """
    try:
        transactions = await client.get_recent_transactions(limit=limit)
        return transactions
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch recent transactions")

# ========================================================================
# DISTRIBUTION ENDPOINTS
# ========================================================================

@router.get("/distribution/stats", response_class=JSONResponse, summary="Get distribution statistics")
async def get_distribution_stats(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get token distribution statistics.
    
    Returns:
        Distribution statistics including:
        - Total tokens distributed
        - Distribution across categories
        - Compliance with 65/30/5 model
    """
    try:
        stats = await client.get_distribution_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching distribution stats: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch distribution statistics")

# ========================================================================
# SYSTEM ENDPOINTS
# ========================================================================

@router.get("/system/info", response_class=JSONResponse, summary="Get system information")
async def get_system_info() -> Dict:
    """
    Get website system information.
    
    Returns:
        System information including version, environment, and features
    """
    return {
        "name": "UBEC Protocol Website",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "features": {
            "api_docs": settings.ENABLE_API_DOCS,
            "metrics": settings.ENABLE_METRICS,
            "websockets": settings.ENABLE_WEBSOCKETS
        },
        "backend_url": settings.BACKEND_API_URL,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/system/health", response_class=JSONResponse, summary="Get system health")
async def get_system_health(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get detailed system health information.
    
    Returns:
        Health status of all components
    """
    try:
        # Test backend connectivity
        await client.get_network_status()
        backend_status = "operational"
    except Exception as e:
        logger.error(f"Backend health check failed: {e}")
        backend_status = "degraded"
    
    return {
        "status": "operational" if backend_status == "operational" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "web_server": "operational",
            "backend_api": backend_status,
            "cache": "operational"
        }
    }
