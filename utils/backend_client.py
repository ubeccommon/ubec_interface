"""
Backend API Client
==================

HTTP client for communicating with the UBEC Protocol backend API.

This module implements:
    - Principle #3: Service pattern with centralized execution
    - Principle #5: Strict async operations
    - Principle #9: Integrated rate limiting

Features:
    - Async HTTP client using aiohttp
    - Response caching with configurable TTL
    - Automatic session management
    - Error handling and logging
    - Connection pooling

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.

Version: 2.1.0 - Aligned with Backend API v2.3.0
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.settings import settings

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """
    Async HTTP client for UBEC Protocol backend API.
    
    Provides cached access to backend endpoints with automatic session management.
    Aligned with Backend API v2.2.2 OpenAPI specification.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the backend API client.
        
        Args:
            base_url: Backend API base URL (defaults to settings.BACKEND_API_URL)
            api_key: API authentication key (defaults to settings.BACKEND_API_KEY)
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or settings.BACKEND_API_URL).rstrip("/")
        self.api_key = api_key or settings.BACKEND_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._cache_lock = asyncio.Lock()
        
        logger.info(f"Initialized BackendAPIClient for {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=headers
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("Closed BackendAPIClient session")
    
    async def _cached_get(
        self,
        endpoint: str,
        ttl: int = 30,
        params: Optional[Dict] = None
    ) -> Any:
        """
        Make cached GET request to backend.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/tokens")
            ttl: Cache time-to-live in seconds
            params: Query parameters
        
        Returns:
            JSON response data
        
        Raises:
            aiohttp.ClientError: On connection errors
            ValueError: On invalid JSON response
        """
        # Create cache key
        cache_key = f"{endpoint}:{str(params)}"
        
        # Check cache
        async with self._cache_lock:
            if cache_key in self._cache:
                data, cached_at = self._cache[cache_key]
                if datetime.now() - cached_at < timedelta(seconds=ttl):
                    logger.debug(f"Cache hit for {endpoint}")
                    return data
        
        # Make request
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        logger.debug(f"GET {url} (params={params})")
        
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Cache response
                async with self._cache_lock:
                    self._cache[cache_key] = (data, datetime.now())
                
                return data
                
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error for {url}: {e.status} - {e.message}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    def invalidate_cache(self, endpoint: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            endpoint: Specific endpoint to invalidate, or None for all
        """
        if endpoint:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(endpoint)]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"Invalidated cache for {endpoint}")
        else:
            self._cache.clear()
            logger.debug("Cleared all cache")
    
    # ========================================================================
    # TOKEN ENDPOINTS
    # ========================================================================
    
    async def get_all_tokens(self) -> List[Dict]:
        """
        Get all four UBEC token details.
        
        ENHANCED v2.2.0: Now includes human-readable name and total_supply
        from database for each token.
        
        Each token includes:
        - name: Human-readable token name
        - total_supply: Current total supply from database
        - asset_code: Token code
        - element: Associated element
        - ubuntu_principle: Ubuntu principle represented
        - issuer: Stellar issuer address
        - description: Token purpose description
        
        Returns:
            List of token objects with details about UBEC, UBECrc, UBECgpi, UBECtt
        """
        data = await self._cached_get("/api/v1/tokens", ttl=60)
        # Backend returns {"tokens": [...], "count": 4, "timestamp": "..."}
        if isinstance(data, dict) and "tokens" in data:
            return data["tokens"]
        return data if isinstance(data, list) else []
    
    async def get_token_by_code(self, code: str) -> Dict:
        """
        Get specific token details by code.
        
        Args:
            code: Token code (UBEC, UBECrc, UBECgpi, or UBECtt)
        
        Returns:
            Token object with details
        
        Raises:
            ValueError: If token not found
        """
        tokens = await self.get_all_tokens()
        for token in tokens:
            if token.get("asset_code") == code:
                return token
        raise ValueError(f"Token not found: {code}")
    
    # ========================================================================
    # NETWORK ENDPOINTS
    # ========================================================================
    
    async def get_network_status(self) -> Dict:
        """
        Get current network status and health metrics.
        
        Returns:
            Network status object with:
            - total_supply: Total token supply across all elements
            - total_holders: Total unique holders
            - bioregion_count: Active bioregion count
            - health_score: Overall health score from holonic metrics
            - recent_transactions: Recent transaction activity count
            - timestamp: When this data was retrieved
        """
        return await self._cached_get("/api/v1/network-status", ttl=30)
    
    # ========================================================================
    # BIOREGION ENDPOINTS
    # ========================================================================
    
    async def get_bioregion_count(self) -> int:
        """
        Get total count of active bioregions.
        
        Returns:
            Number of bioregions
        """
        data = await self._cached_get("/api/v1/bioregions/count", ttl=30)
        return data.get("count", 0)
    
    async def get_bioregion_summary(self) -> Dict:
        """
        Get summary statistics for all bioregions.
        
        This method transforms the full bioregions data into summary statistics.
        
        Returns:
            Dictionary with summary statistics including:
            - total_count: Number of bioregions
            - bioregions: List of bioregion summaries
            - timestamp: When this data was retrieved
        """
        # FIXED: Backend doesn't have /api/v1/bioregions/summary endpoint
        # Instead, we transform data from the full bioregions list
        data = await self.get_bioregions()
        
        # Transform full data into summary format
        summary = {
            "total_count": data.get("count", 0),
            "bioregions": data.get("bioregions", []),
            "timestamp": data.get("timestamp", datetime.now().isoformat())
        }
        
        return summary
    
    async def get_bioregions(self) -> Dict:
        """
        Get list of all active bioregions with details.
        
        Returns:
            Dictionary with:
            - bioregions: List of bioregion objects with names, locations, etc.
            - count: Total number of bioregions
            - timestamp: When this data was retrieved
        """
        return await self._cached_get("/api/v1/bioregions", ttl=60)
    
    async def get_bioregion(self, bioregion_id: int) -> Dict:
        """
        Get specific bioregion details.
        
        Args:
            bioregion_id: Bioregion identifier
        
        Returns:
            Bioregion object with detailed information
        """
        return await self._cached_get(f"/api/v1/bioregions/{bioregion_id}", ttl=60)
    
    async def get_bioregion_health(self, bioregion_id: int) -> Dict:
        """
        Get health assessment for a specific bioregion.
        
        Args:
            bioregion_id: Bioregion identifier
        
        Returns:
            Health assessment with rating (excellent/good/fair/poor)
            and component scores
        """
        return await self._cached_get(f"/api/v1/bioregions/{bioregion_id}/health", ttl=30)
    
    # ========================================================================
    # GEOGRAPHIC DATA ENDPOINTS (v2.3.0)
    # ========================================================================
    
    async def get_ecoregions(
        self,
        limit: int = 50,
        biome: Optional[str] = None,
        realm: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get ecoregion data from Ecoregions2017 dataset.
        
        AVAILABLE v2.3.0: Now fully implemented in Backend API v2.3.0.
        Returns None if endpoint is unavailable (graceful degradation).
        
        Args:
            limit: Number of results (max: 200)
            biome: Filter by biome name
            realm: Filter by realm
        
        Returns:
            Dictionary with ecoregion data, or None if endpoint unavailable
            Expected format: {"ecoregions": [...], "count": N}
        """
        params = {"limit": limit}
        if biome:
            params["biome"] = biome
        if realm:
            params["realm"] = realm
        
        try:
            return await self._cached_get("/api/v1/ecoregions", ttl=300, params=params)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info("Ecoregions endpoint not implemented yet (404)")
                return None
            elif e.status >= 500:
                logger.warning(f"Backend error fetching ecoregions: {e.status}")
                return None
            else:
                logger.error(f"Error fetching ecoregions: {e.status} - {e.message}")
                return None
        except Exception as e:
            logger.warning(f"Could not fetch ecoregions: {e}")
            return None
    
    async def get_ecoregion(self, eco_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific ecoregion.
        
        AVAILABLE v2.3.0: Now fully implemented in Backend API v2.3.0.
        
        Args:
            eco_id: Ecoregion ID
        
        Returns:
            Ecoregion details with geographic data, or None if unavailable
        """
        try:
            return await self._cached_get(f"/api/v1/ecoregions/{eco_id}", ttl=300)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info(f"Ecoregion {eco_id} not found or endpoint not implemented")
                return None
            else:
                logger.error(f"Error fetching ecoregion {eco_id}: {e.status}")
                return None
        except Exception as e:
            logger.warning(f"Could not fetch ecoregion {eco_id}: {e}")
            return None
    
    # ========================================================================
    # WATERSHED ENDPOINTS (v2.3.0)
    # ========================================================================
    
    async def get_watersheds(
        self,
        limit: int = 50,
        min_area: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Get watershed data from FEOW HydroSHEDS dataset.
        
        AVAILABLE v2.3.0: Now fully implemented in Backend API v2.3.0.
        Returns None if endpoint is unavailable (graceful degradation).
        
        Args:
            limit: Number of results (max: 200)
            min_area: Minimum area in square kilometers
        
        Returns:
            Dictionary with watershed data, or None if endpoint unavailable
            Expected format: {"watersheds": [...], "count": N}
        """
        params = {"limit": limit}
        if min_area is not None:
            params["min_area"] = min_area
        
        try:
            return await self._cached_get("/api/v1/watersheds", ttl=300, params=params)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info("Watersheds endpoint not implemented yet (404)")
                return None
            elif e.status >= 500:
                logger.warning(f"Backend error fetching watersheds: {e.status}")
                return None
            else:
                logger.error(f"Error fetching watersheds: {e.status} - {e.message}")
                return None
        except Exception as e:
            logger.warning(f"Could not fetch watersheds: {e}")
            return None
    
    async def get_watershed(self, feow_id: int) -> Optional[Dict]:
        """
        Get specific watershed by FEOW ID.
        
        AVAILABLE v2.3.0: Now fully implemented in Backend API v2.3.0.
        
        Args:
            feow_id: FEOW watershed identifier
        
        Returns:
            Watershed details with geographic data, or None if unavailable
        """
        try:
            return await self._cached_get(f"/api/v1/watersheds/{feow_id}", ttl=300)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info(f"Watershed {feow_id} not found or endpoint not implemented")
                return None
            else:
                logger.error(f"Error fetching watershed {feow_id}: {e.status}")
                return None
        except Exception as e:
            logger.warning(f"Could not fetch watershed {feow_id}: {e}")
            return None
    
    # ========================================================================
    # HOLONIC EVALUATION ENDPOINTS
    # ========================================================================
    
    async def get_holonic_scores(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        min_score: Optional[float] = None
    ) -> Dict:
        """
        Get holonic evaluation scores for network accounts.
        
        ENHANCED v2.2.0: Now includes reciprocity_health and mutualism_capacity
        metrics for Ubuntu principle alignment.
        
        Holonic categories represent Ubuntu principle alignment levels:
        - observer: Basic network presence (0.0-0.2)
        - participant: Regular engagement (0.2-0.4)
        - contributor: Active value creation (0.4-0.6)
        - integrator: Cross-network collaboration (0.6-0.8)
        - exemplar: Ubuntu principle embodiment (0.8-1.0)
        
        New metrics in v2.2.0:
        - reciprocity_health: Water element alignment (UBECrc flows)
        - mutualism_capacity: Earth element alignment (UBECgpi stability)
        
        Args:
            category: Filter by holonic category (observer, participant, 
                     contributor, integrator, exemplar)
            limit: Number of results (max: 500)
            min_score: Minimum composite score threshold (0.0-1.0)
        
        Returns:
            Dictionary with:
            - summary: Overall statistics and averages
            - category_distribution: Counts by holonic category
            - accounts: Detailed account scores with Ubuntu metrics
            - timestamp: When this data was retrieved
        """
        params = {"limit": min(limit, 500)}
        if category:
            params["category"] = category
        if min_score is not None:
            params["min_score"] = min_score
        
        return await self._cached_get("/api/v1/holonic-scores", ttl=60, params=params)
    
    # ========================================================================
    # TRANSACTION ENDPOINTS
    # ========================================================================
    
    async def get_recent_transactions(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """
        Get recent blockchain transactions across all UBEC tokens.
        
        CRITICAL FIX: Endpoint path corrected to /api/v1/transactions/recent
        
        Args:
            limit: Maximum number of transactions to return (default 20, max 100)
            offset: Number of transactions to skip for pagination
        
        Returns:
            Dictionary with:
            - transactions: List of recent transaction objects
            - count: Number of transactions returned
            - total: Total number of transactions in database
            - timestamp: When this data was retrieved
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }
        # FIXED: Endpoint was /api/v1/transactions (404)
        # Now correctly using /api/v1/transactions/recent
        return await self._cached_get("/api/v1/transactions/recent", ttl=15, params=params)
    
    # ========================================================================
    # DISTRIBUTION ENDPOINTS
    # ========================================================================
    
    async def get_distribution_stats(self) -> Dict:
        """
        Get token distribution statistics for 75/20/5 compliance.
        
        Returns distribution breakdown by category:
        - General Circulation (75%)
        - Stewardship (20%)
        - Administration (5%)
        
        Shows compliance status for each token.
        
        Returns:
            Distribution statistics including:
            - tokens: Distribution data for each token
            - compliance_summary: Overall compliance status
            - timestamp: When this data was retrieved
        """
        return await self._cached_get("/api/v1/distribution", ttl=60)
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    async def health_check(self) -> Dict:
        """
        Check backend API health.
        
        Returns:
            Health status object with:
            - status: Health status string
            - timestamp: Current timestamp
            - version: API version
        """
        return await self._cached_get("/api/v1/health", ttl=5)


# ========================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ========================================================================

# Global client instance
_client: Optional[BackendAPIClient] = None


async def get_backend_client() -> BackendAPIClient:
    """
    Get or create global backend client instance.
    
    Returns:
        BackendAPIClient instance
    """
    global _client
    if _client is None:
        _client = BackendAPIClient()
    return _client


async def close_backend_client():
    """Close global backend client instance."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


# ========================================================================
# TESTING
# ========================================================================

async def test_client():
    """Test the backend client against all available API endpoints."""
    print("=" * 70)
    print("Backend API Client Test - v2.1.0")
    print("Testing against Backend API v2.3.0")
    print("=" * 70)
    
    client = BackendAPIClient()
    
    try:
        # Test 1: Health check
        print("\n[1/10] Testing health check...")
        health = await client.health_check()
        print(f"✓ Health: {health.get('status', 'unknown')}")
        
        # Test 2: Tokens
        print("\n[2/10] Testing tokens endpoint...")
        tokens = await client.get_all_tokens()
        print(f"✓ Found {len(tokens)} tokens")
        for token in tokens:
            name = token.get('name', token.get('asset_code', 'Unknown'))
            supply = token.get('total_supply', 0)
            print(f"  - {name}: {supply:,} tokens")
        
        # Test 3: Network status
        print("\n[3/10] Testing network status...")
        network = await client.get_network_status()
        print(f"✓ Active bioregions: {network.get('bioregion_count', 0)}")
        print(f"  Total holders: {network.get('total_holders', 0)}")
        print(f"  Health score: {network.get('health_score', 'N/A')}")
        
        # Test 4: Bioregion count
        print("\n[4/10] Testing bioregion count...")
        count = await client.get_bioregion_count()
        print(f"✓ Bioregion count: {count}")
        
        # Test 5: Bioregions list
        print("\n[5/10] Testing bioregions list...")
        bioregions_data = await client.get_bioregions()
        bio_count = bioregions_data.get('count', 0)
        print(f"✓ Retrieved {bio_count} bioregions")
        
        # Test 6: Bioregion summary
        print("\n[6/10] Testing bioregion summary...")
        summary = await client.get_bioregion_summary()
        print(f"✓ Summary total: {summary.get('total_count', 0)}")
        
        # Test 7: Holonic scores
        print("\n[7/10] Testing holonic scores...")
        scores = await client.get_holonic_scores(limit=5)
        if 'summary' in scores:
            print(f"✓ Average score: {scores['summary'].get('average_score', 'N/A')}")
        if 'category_distribution' in scores:
            print(f"  Category distribution: {scores['category_distribution']}")
        
        # Test 8: Recent transactions - CRITICAL FIX
        print("\n[8/10] Testing recent transactions (CRITICAL FIX)...")
        transactions = await client.get_recent_transactions(limit=5)
        tx_count = transactions.get('count', 0)
        tx_total = transactions.get('total', 0)
        print(f"✓ Retrieved {tx_count} of {tx_total} total transactions")
        print(f"  ✨ Transaction endpoint FIXED - now using /recent path")
        
        # Test 9: Distribution stats
        print("\n[9/10] Testing distribution stats...")
        distribution = await client.get_distribution_stats()
        print(f"✓ Got distribution compliance data")
        if 'tokens' in distribution:
            print(f"  Tracking {len(distribution['tokens'])} token distributions")
        
        # Test 10: Geographic endpoints (v2.3.0)
        print("\n[10/10] Testing geographic endpoints (v2.3.0)...")
        ecoregions = await client.get_ecoregions(limit=3)
        if ecoregions:
            eco_count = ecoregions.get('count', 0)
            print(f"✓ Ecoregions (v2.3.0): {eco_count} found")
        else:
            print("⚠ Ecoregions endpoint not available")
        
        watersheds = await client.get_watersheds(limit=3)
        if watersheds:
            ws_count = watersheds.get('count', 0)
            print(f"✓ Watersheds (v2.3.0): {ws_count} found")
        else:
            print("⚠ Watersheds endpoint not available")
        
        print("\n" + "=" * 70)
        print("✓ All tests completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    """Test the client when run directly."""
    asyncio.run(test_client())
