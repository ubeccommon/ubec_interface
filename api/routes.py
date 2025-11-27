"""
API Routes v1.3.0 - Liquidity Pools Endpoint (Backend API v2.5.6)
=================================================================

Frontend API routes that proxy to backend protocol server.

NEW IN v1.3.0 - LIQUIDITY POOLS:
- /liquidity-pools - Get all UBEC liquidity pools
- /liquidity-pools?token_code=UBEC - Filter by specific token

MAINTAINED v1.2.0 - TOKEN AUDIT:
- /token-audit - Get UBEC token audit (default)
- /token-audit/{token_code} - Get specific token audit (UBEC, UBECrc, UBECgpi, UBECtt)

UPDATED v1.1.1 - TRANSACTIONS v2.5.2:
- /transactions/recent now returns operation-level details
- Includes trade_summary for DEX operations
- Full operation array per transaction

NEW IN v1.1.0 - BBOX ENDPOINTS:
- /bioregions/{bioregion_id}/bbox - Get bioregion bounding box for map zoom
- /ecoregions/{eco_id}/bbox - Get ecoregion bounding box for map zoom
- /watersheds/{feow_id}/bbox - Get watershed bounding box for map zoom

This module implements:
    - Principle #3: Service pattern with centralized execution
    - Principle #5: Strict async operations
    - Principle #8: No duplicate configuration

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from utils.backend_client import BackendAPIClient, get_backend_client
from config.settings import settings

logger = logging.getLogger(__name__)

# Create API router (prefix is added in main_web.py)
router = APIRouter(tags=["api"])

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
        List of token objects for UBEC, UBECrc, UBECgpi, and UBECtt
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
        token = await client.get_token_by_code(token_code)
        return token
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
# BIOREGION ENDPOINTS
# ========================================================================

@router.get("/bioregions/count", response_class=JSONResponse, summary="Get bioregion count")
async def get_bioregion_count(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get total count of active bioregions.
    
    Returns:
        Dictionary with bioregion count
    """
    try:
        count = await client.get_bioregion_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error fetching bioregion count: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch bioregion count")


@router.get("/bioregions/summary", response_class=JSONResponse, summary="Get bioregion summary")
async def get_bioregion_summary(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get summary statistics for all bioregions.
    
    Returns:
        Dictionary with summary statistics including:
        - total_count: Number of bioregions
        - total_members: Total member count
        - average_scores: Average metrics
        - geographic_metrics: Geographic distribution
    """
    try:
        summary = await client.get_bioregion_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching bioregion summary: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch bioregion summary")


@router.get("/bioregions", response_class=JSONResponse, summary="Get all bioregions")
async def get_all_bioregions(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get all bioregions with detailed information.
    
    Returns:
        Dictionary containing:
        - count: Total number of bioregions
        - summary: Summary statistics
        - bioregions: List of bioregion objects
    """
    try:
        bioregions = await client.get_bioregions()
        return bioregions
    except Exception as e:
        logger.error(f"Error fetching bioregions: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch bioregions")


@router.get("/bioregions/{bioregion_id}", response_class=JSONResponse, summary="Get bioregion details")
async def get_bioregion(
    bioregion_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get detailed information about a specific bioregion.
    
    Args:
        bioregion_id: Bioregion identifier
        
    Returns:
        Bioregion object with detailed information
    """
    try:
        bioregion = await client.get_bioregion(bioregion_id)
        return bioregion
    except Exception as e:
        logger.error(f"Error fetching bioregion {bioregion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch bioregion {bioregion_id}")


@router.get("/bioregions/{bioregion_id}/health", response_class=JSONResponse, summary="Get bioregion health")
async def get_bioregion_health(
    bioregion_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get health assessment for a specific bioregion.
    
    Args:
        bioregion_id: Bioregion identifier
        
    Returns:
        Health assessment with rating and component scores
    """
    try:
        health = await client.get_bioregion_health(bioregion_id)
        return health
    except Exception as e:
        logger.error(f"Error fetching bioregion health {bioregion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch bioregion health")


@router.get("/bioregions/{bioregion_id}/bbox", response_class=JSONResponse, summary="Get bioregion bounding box")
async def get_bioregion_bbox(
    bioregion_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get bounding box coordinates for a specific bioregion.
    
    Useful for map centering and zoom calculations.
    
    Args:
        bioregion_id: Bioregion GID identifier
        
    Returns:
        Dictionary containing:
        - gid: Bioregion identifier
        - bioregion_name: Name of the bioregion
        - bioregion_code: Bioregion code
        - bbox: Bounding box with min_lon, min_lat, max_lon, max_lat
        - centroid: Center point coordinates (lon, lat)
        - area_sqkm: Area in square kilometers
        - srid: Spatial Reference ID (4326 = WGS84)
    """
    try:
        bbox_data = await client.get_bioregion_bbox(bioregion_id)
        return bbox_data
    except Exception as e:
        logger.error(f"Error fetching bioregion bbox {bioregion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch bioregion bounding box")

# ========================================================================
# ECOREGION ENDPOINTS
# ========================================================================

@router.get("/ecoregions", response_class=JSONResponse, summary="Get ecoregions")
async def get_ecoregions(
    limit: int = Query(50, ge=1, le=200),
    biome: Optional[str] = None,
    realm: Optional[str] = None,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get ecoregion data from Ecoregions2017 dataset.
    
    Query Parameters:
        - limit: Number of results (default: 50, max: 200)
        - biome: Filter by biome name
        - realm: Filter by realm
    
    Returns:
        Dictionary with ecoregion data
    """
    try:
        ecoregions = await client.get_ecoregions(limit=limit, biome=biome, realm=realm)
        return ecoregions
    except Exception as e:
        logger.error(f"Error fetching ecoregions: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch ecoregions")


@router.get("/ecoregions/{eco_id}", response_class=JSONResponse, summary="Get ecoregion details")
async def get_ecoregion(
    eco_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get detailed information about a specific ecoregion.
    
    Args:
        eco_id: Ecoregion ID
        
    Returns:
        Ecoregion details with geographic and ecological data
    """
    try:
        ecoregion = await client.get_ecoregion(eco_id)
        return ecoregion
    except Exception as e:
        logger.error(f"Error fetching ecoregion {eco_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch ecoregion {eco_id}")


@router.get("/ecoregions/{eco_id}/bbox", response_class=JSONResponse, summary="Get ecoregion bounding box")
async def get_ecoregion_bbox(
    eco_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get bounding box coordinates for a specific ecoregion.
    
    Useful for map centering and zoom calculations.
    
    Args:
        eco_id: Ecoregion eco_id from WWF Ecoregions 2017 dataset
        
    Returns:
        Dictionary containing:
        - eco_id: Ecoregion identifier
        - eco_name: Name of the ecoregion
        - biome_name: Associated biome name
        - realm: Biogeographic realm
        - bbox: Bounding box with min_lon, min_lat, max_lon, max_lat
        - centroid: Center point coordinates (lon, lat)
        - shape_area: Area from source dataset
        - srid: Spatial Reference ID (4326 = WGS84)
    """
    try:
        bbox_data = await client.get_ecoregion_bbox(eco_id)
        return bbox_data
    except Exception as e:
        logger.error(f"Error fetching ecoregion bbox {eco_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch ecoregion bounding box")

# ========================================================================
# WATERSHED ENDPOINTS
# ========================================================================

@router.get("/watersheds", response_class=JSONResponse, summary="Get watersheds")
async def get_watersheds(
    limit: int = Query(50, ge=1, le=200),
    min_area: Optional[float] = None,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get watershed data from FEOW HydroSHEDS dataset.
    
    Query Parameters:
        - limit: Number of results (default: 50, max: 200)
        - min_area: Minimum area in square kilometers
    
    Returns:
        Dictionary with watershed data
    """
    try:
        watersheds = await client.get_watersheds(limit=limit, min_area=min_area)
        return watersheds
    except Exception as e:
        logger.error(f"Error fetching watersheds: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch watersheds")


@router.get("/watersheds/{feow_id}", response_class=JSONResponse, summary="Get watershed details")
async def get_watershed(
    feow_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get specific watershed by FEOW ID.
    
    Args:
        feow_id: FEOW watershed identifier
        
    Returns:
        Watershed details with geographic data
    """
    try:
        watershed = await client.get_watershed(feow_id)
        return watershed
    except Exception as e:
        logger.error(f"Error fetching watershed {feow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch watershed {feow_id}")


@router.get("/watersheds/{feow_id}/bbox", response_class=JSONResponse, summary="Get watershed bounding box")
async def get_watershed_bbox(
    feow_id: int,
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get bounding box coordinates for a specific watershed.
    
    Useful for map centering and zoom calculations.
    
    Args:
        feow_id: FEOW watershed identifier from HydroSHEDS dataset
        
    Returns:
        Dictionary containing:
        - feow_id: Watershed identifier
        - name: Generated watershed name
        - bbox: Bounding box with min_lon, min_lat, max_lon, max_lat
        - centroid: Center point coordinates (lon, lat)
        - area_sqkm: Area in square kilometers
        - srid: Spatial Reference ID (4326 = WGS84)
    """
    try:
        bbox_data = await client.get_watershed_bbox(feow_id)
        return bbox_data
    except Exception as e:
        logger.error(f"Error fetching watershed bbox {feow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch watershed bounding box")

# ========================================================================
# HOLONIC EVALUATION ENDPOINTS
# ========================================================================

@router.get("/holonic/scores", response_class=JSONResponse, summary="Get holonic scores")
async def get_holonic_scores(
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get holonic evaluation scores for accounts.
    
    Query Parameters:
        - category: Filter by holonic category (observer, participant, contributor, integrator, exemplar)
        - limit: Number of results (default: 50, max: 200)
        - min_score: Minimum composite score threshold (0.0-1.0)
    
    Returns:
        Dictionary with summary statistics and list of account evaluations
    """
    try:
        scores = await client.get_holonic_scores(
            category=category,
            limit=limit,
            min_score=min_score
        )
        return scores
    except Exception as e:
        logger.error(f"Error fetching holonic scores: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch holonic scores")

# ========================================================================
# TRANSACTION ENDPOINTS
# ========================================================================

@router.get("/transactions/recent", response_class=JSONResponse, summary="Get recent transactions")
async def get_recent_transactions(
    limit: int = Query(20, ge=1, le=100),
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get recent blockchain transactions with full operation details.
    
    UPDATED v2.5.2: Now returns operation-level details including
    trade summaries for DEX operations.
    
    Query Parameters:
        - limit: Maximum number of transactions to return (default: 20, max: 100)
    
    Returns:
        Dictionary with:
        - transactions: List of transactions with operations array
        - pagination: Limit, total, and returned counts
        - valid_tokens: List of valid UBEC tokens
        - filter: Applied filters (if any)
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

@router.get("/distributions/stats", response_class=JSONResponse, summary="Get distribution statistics")
async def get_distribution_stats(
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get token distribution statistics for 75/20/5 compliance.
    
    Returns:
        Distribution statistics including:
        - total_distributed: Total tokens distributed
        - distribution_by_category: Breakdown by category
        - compliance_status: Compliance with distribution model
    """
    try:
        stats = await client.get_distribution_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching distribution stats: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch distribution statistics")

@router.get("/token-audit", response_class=JSONResponse, summary="Get token audit (default UBEC)")
@router.get("/token-audit/{token_code}", response_class=JSONResponse, summary="Get token audit")
async def get_token_audit(
    token_code: str = "UBEC",
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get comprehensive token audit data for transparency reporting.
    
    NEW v2.5.5: Full token audit endpoint for dashboard display
    
    Path Parameters:
        - token_code: Token to audit (UBEC, UBECrc, UBECgpi, UBECtt) - default UBEC
    
    Returns:
        Comprehensive audit data including:
        - token: Token info (code, element, ubuntu_principle, issuer)
        - summary: Totals and percentages
        - general_distribution: 65% category with accounts and projects
        - token_ecosystem_stewardship: 30% category with accounts and LP breakdown
        - administration: 5% category with accounts
        - compliance: Compliance status indicators
        - disclaimer: Legal disclaimer text
    """
    try:
        audit = await client.get_token_audit(token_code=token_code)
        return audit
    except Exception as e:
        logger.error(f"Error fetching token audit: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch token audit")

@router.get("/liquidity-pools", response_class=JSONResponse, summary="Get liquidity pools")
async def get_liquidity_pools(
    token_code: Optional[str] = Query(None, description="Filter by token (UBEC, UBECrc, UBECgpi, UBECtt)"),
    client: BackendAPIClient = Depends(get_backend_client)
) -> Dict:
    """
    Get UBEC liquidity pool details from Stellar DEX.
    
    NEW v2.5.6: Comprehensive liquidity pool endpoint
    
    Query Parameters:
        - token_code: Optional filter by token (UBEC, UBECrc, UBECgpi, UBECtt)
    
    Returns:
        Liquidity pool data including:
        - pools: Array of pool objects with pair, reserves, participants, fees
        - summary: Aggregate stats (total_pools, total_value_locked, pools_by_token)
        - filter_applied: Which token filter was used (if any)
        - timestamp: Response timestamp
    """
    try:
        pools = await client.get_liquidity_pools(token_code=token_code)
        return pools
    except Exception as e:
        logger.error(f"Error fetching liquidity pools: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch liquidity pools")

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
        await client.health_check()
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
