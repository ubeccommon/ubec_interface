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
        
        Returns:
            List of token objects with details about UBEC, UBECrc, UBECgpi, UBECtt
        """
        data = await self._cached_get("/api/v1/tokens", ttl=60)
        return data if isinstance(data, list) else data.get("tokens", [])
    
    async def get_token_by_code(self, code: str) -> Dict:
        """
        Get specific token details by code.
        
        Args:
            code: Token code (UBEC, UBECrc, UBECgpi, or UBECtt)
        
        Returns:
            Token object with details
        """
        tokens = await self.get_all_tokens()
        for token in tokens:
            if token.get("code") == code:
                return token
        raise ValueError(f"Token not found: {code}")
    
    # ========================================================================
    # NETWORK ENDPOINTS
    # ========================================================================
    
    async def get_network_status(self) -> Dict:
        """
        Get current network status and statistics.
        
        Returns:
            Network status object with:
            - bioregion_count: Number of active bioregions
            - total_participants: Total network participants
            - active_transactions: Recent transaction count
            - network_health: Overall health score
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
        
        Returns:
            Dictionary with summary statistics including:
            - total_count: Number of bioregions
            - total_members: Total member count
            - average_scores: Average metrics
            - geographic_metrics: Geographic distribution
        """
        return await self._cached_get("/api/v1/bioregions/summary", ttl=60)
    
    async def get_bioregions(self) -> Dict:
        """
        Get all bioregions with details.
        
        Returns:
            Dictionary with bioregion data
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
    # ECOREGION ENDPOINTS
    # ========================================================================
    
    async def get_ecoregions(
        self,
        limit: int = 50,
        biome: Optional[str] = None,
        realm: Optional[str] = None
    ) -> Dict:
        """
        Get ecoregion data from Ecoregions2017 dataset.
        
        Args:
            limit: Number of results (max: 200)
            biome: Filter by biome name
            realm: Filter by realm
        
        Returns:
            Dictionary with ecoregion data
        """
        params = {"limit": limit}
        if biome:
            params["biome"] = biome
        if realm:
            params["realm"] = realm
        return await self._cached_get("/api/v1/ecoregions", ttl=300, params=params)
    
    async def get_ecoregion(self, eco_id: int) -> Dict:
        """
        Get detailed information about a specific ecoregion.
        
        Args:
            eco_id: Ecoregion ID
        
        Returns:
            Ecoregion details with geographic and ecological data
        """
        return await self._cached_get(f"/api/v1/ecoregions/{eco_id}", ttl=300)
    
    # ========================================================================
    # WATERSHED ENDPOINTS
    # ========================================================================
    
    async def get_watersheds(
        self,
        limit: int = 50,
        min_area: Optional[float] = None
    ) -> Dict:
        """
        Get watershed data from FEOW HydroSHEDS dataset.
        
        Args:
            limit: Number of results (max: 200)
            min_area: Minimum area in square kilometers
        
        Returns:
            Dictionary with watershed data
        """
        params = {"limit": limit}
        if min_area is not None:
            params["min_area"] = min_area
        return await self._cached_get("/api/v1/watersheds", ttl=300, params=params)
    
    async def get_watershed(self, feow_id: int) -> Dict:
        """
        Get specific watershed by FEOW ID.
        
        Args:
            feow_id: FEOW watershed identifier
        
        Returns:
            Watershed details with geographic data
        """
        return await self._cached_get(f"/api/v1/watersheds/{feow_id}", ttl=300)
    
    # ========================================================================
    # HOLONIC EVALUATION ENDPOINTS
    # ========================================================================
    
    async def get_holonic_scores(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        min_score: float = 0.0
    ) -> Dict:
        """
        Get holonic evaluation scores for accounts.
        
        Args:
            category: Filter by holonic category (observer, participant, 
                     contributor, integrator, exemplar)
            limit: Number of results (max: 200)
            min_score: Minimum composite score threshold (0.0-1.0)
        
        Returns:
            Dictionary with summary statistics and list of account evaluations
        """
        params = {"limit": limit, "min_score": min_score}
        if category:
            params["category"] = category
        return await self._cached_get("/api/v1/holonic-scores", ttl=60, params=params)
    
    # ========================================================================
    # TRANSACTION ENDPOINTS
    # ========================================================================
    
    async def get_recent_transactions(self, limit: int = 20) -> Dict:
        """
        Get recent blockchain transactions.
        
        Args:
            limit: Maximum number of transactions to return (max: 100)
        
        Returns:
            Dictionary with list of recent transaction operations
        """
        params = {"limit": min(limit, 100)}
        return await self._cached_get("/api/v1/transactions", ttl=15, params=params)
    
    # ========================================================================
    # DISTRIBUTION ENDPOINTS
    # ========================================================================
    
    async def get_distribution_stats(self) -> Dict:
        """
        Get token distribution statistics for 75/20/5 compliance.
        
        Returns:
            Distribution statistics including:
            - total_distributed: Total tokens distributed
            - distribution_by_category: Breakdown by category
            - compliance_status: Compliance with distribution model
        """
        return await self._cached_get("/api/v1/distribution", ttl=60)
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    async def health_check(self) -> Dict:
        """
        Check backend API health.
        
        Returns:
            Health status object
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
    """Test the backend client."""
    print("=" * 70)
    print("Backend API Client Test")
    print("=" * 70)
    
    client = BackendAPIClient()
    
    try:
        # Test health
        print("\n[1/10] Testing health check...")
        health = await client.health_check()
        print(f"✓ Health: {health.get('status', 'unknown')}")
        
        # Test tokens
        print("\n[2/10] Testing tokens...")
        tokens = await client.get_all_tokens()
        print(f"✓ Found {len(tokens)} tokens")
        
        # Test network status
        print("\n[3/10] Testing network status...")
        network = await client.get_network_status()
        print(f"✓ Bioregions: {network.get('bioregion_count', 0)}")
        
        # Test bioregion count
        print("\n[4/10] Testing bioregion count...")
        count = await client.get_bioregion_count()
        print(f"✓ Bioregion count: {count}")
        
        # Test bioregion summary
        print("\n[5/10] Testing bioregion summary...")
        summary = await client.get_bioregion_summary()
        print(f"✓ Got bioregion summary")
        
        # Test holonic scores
        print("\n[6/10] Testing holonic scores...")
        scores = await client.get_holonic_scores(limit=5)
        print(f"✓ Got holonic scores")
        
        # Test transactions
        print("\n[7/10] Testing transactions...")
        transactions = await client.get_recent_transactions(limit=5)
        print(f"✓ Got recent transactions")
        
        # Test distribution
        print("\n[8/10] Testing distribution stats...")
        distribution = await client.get_distribution_stats()
        print(f"✓ Got distribution stats")
        
        # Test ecoregions
        print("\n[9/10] Testing ecoregions...")
        ecoregions = await client.get_ecoregions(limit=5)
        print(f"✓ Got ecoregions")
        
        # Test watersheds
        print("\n[10/10] Testing watersheds...")
        watersheds = await client.get_watersheds(limit=5)
        print(f"✓ Got watersheds")
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
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
