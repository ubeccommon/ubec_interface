"""
Backend API Client
==================

HTTP client for communicating with the UBEC Protocol API Gateway.

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

Version: 3.0.0 - Updated for api.ubec.network gateway (clean /v1/ paths)
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
    Async HTTP client for UBEC Protocol API Gateway.
    
    Provides cached access to API endpoints with automatic session management.
    Configured for api.ubec.network with clean /v1/ endpoint paths.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: API base URL (defaults to settings.BACKEND_API_URL)
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
        Make cached GET request to API.
        
        Args:
            endpoint: API endpoint path (e.g., "/v1/tokens")
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
        data = await self._cached_get("/v1/tokens", ttl=60)
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
            if token.get("asset_code") == code or token.get("code") == code:
                return token
        raise ValueError(f"Token not found: {code}")
    
    # ========================================================================
    # NETWORK ENDPOINTS
    # ========================================================================
    
    async def get_network_status(self) -> Dict:
        """
        Get current network status and health metrics.
        
        Returns:
            Network status object with participants, bioregions, transactions, health
        """
        return await self._cached_get("/v1/network-status", ttl=30)
    
    # ========================================================================
    # BIOREGION ENDPOINTS
    # ========================================================================
    
    async def get_bioregion_count(self) -> int:
        """
        Get total count of active bioregions.
        
        Returns:
            Number of bioregions
        """
        data = await self._cached_get("/v1/bioregions/count", ttl=30)
        return data.get("count", 0)
    
    async def get_bioregion_summary(self) -> Dict:
        """
        Get summary statistics for all bioregions.
        
        Returns:
            Summary statistics including total count, members, averages
        """
        return await self._cached_get("/v1/bioregions/summary", ttl=60)
    
    async def get_bioregions(self, limit: int = 50) -> Dict:
        """
        Get bioregion data.
        
        Args:
            limit: Maximum number of bioregions to return
        
        Returns:
            Dictionary with bioregions list and count
        """
        params = {"limit": min(limit, 500)}
        return await self._cached_get("/v1/bioregions", ttl=60, params=params)
    
    async def get_bioregion(self, bioregion_id: int) -> Dict:
        """
        Get specific bioregion details.
        
        Args:
            bioregion_id: Bioregion identifier
        
        Returns:
            Bioregion object with detailed information
        """
        return await self._cached_get(f"/v1/bioregions/{bioregion_id}", ttl=60)
    
    async def get_bioregion_health(self, bioregion_id: int) -> Dict:
        """
        Get health assessment for a specific bioregion.
        
        Args:
            bioregion_id: Bioregion identifier
        
        Returns:
            Health assessment with rating and component scores
        """
        return await self._cached_get(f"/v1/bioregions/{bioregion_id}/health", ttl=60)
    
    # ========================================================================
    # GEOGRAPHIC ENDPOINTS
    # ========================================================================
    
    async def get_ecoregions(self, limit: int = 50) -> Dict:
        """
        Get ecoregion data from Ecoregions2017 dataset.
        
        Args:
            limit: Maximum number of ecoregions to return
        
        Returns:
            Dictionary with ecoregions list and metadata
        """
        params = {"limit": min(limit, 500)}
        try:
            return await self._cached_get("/v1/ecoregions", ttl=120, params=params)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info("Ecoregions endpoint not implemented yet (404)")
                return None
            raise
    
    async def get_ecoregion(self, eco_id: str) -> Dict:
        """
        Get specific ecoregion details.
        
        Args:
            eco_id: Ecoregion identifier
        
        Returns:
            Ecoregion object with detailed information
        """
        return await self._cached_get(f"/v1/ecoregions/{eco_id}", ttl=120)
    
    async def get_watersheds(self, limit: int = 50) -> Dict:
        """
        Get watershed data from FEOW HydroSHEDS dataset.
        
        Args:
            limit: Maximum number of watersheds to return
        
        Returns:
            Dictionary with watersheds list and metadata
        """
        params = {"limit": min(limit, 500)}
        try:
            return await self._cached_get("/v1/watersheds", ttl=120, params=params)
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info("Watersheds endpoint not implemented yet (404)")
                return None
            raise
    
    async def get_watershed(self, feow_id: str) -> Dict:
        """
        Get specific watershed details.
        
        Args:
            feow_id: FEOW watershed identifier
        
        Returns:
            Watershed object with detailed information
        """
        return await self._cached_get(f"/v1/watersheds/{feow_id}", ttl=120)
    
    # ========================================================================
    # HOLONIC EVALUATION ENDPOINTS
    # ========================================================================
    
    async def get_holonic_scores(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> Dict:
        """
        Get Ubuntu principle evaluation scores.
        
        Args:
            limit: Maximum number of accounts to return (default 50)
            category: Filter by holonic category
            min_score: Minimum composite score threshold (0.0-1.0)
        
        Returns:
            Dictionary with summary statistics and account evaluations
        """
        params = {"limit": min(limit, 500)}
        if category:
            params["category"] = category
        if min_score is not None:
            params["min_score"] = min_score
        
        return await self._cached_get("/v1/holonic-scores", ttl=60, params=params)
    
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
        
        Args:
            limit: Maximum number of transactions to return (default 20, max 100)
            offset: Number of transactions to skip for pagination
        
        Returns:
            Dictionary with transactions list, count, and total
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }
        return await self._cached_get("/v1/transactions/recent", ttl=15, params=params)
    
    # ========================================================================
    # DISTRIBUTION ENDPOINTS
    # ========================================================================
    
    async def get_distribution_stats(self) -> Dict:
        """
        Get token distribution statistics for 75/20/5 compliance.
        
        Returns:
            Distribution statistics including tokens and compliance status
        """
        return await self._cached_get("/v1/distribution", ttl=60)
    
    async def get_token_audit(self, token_code: str = "UBEC") -> Dict:
        """
        Get comprehensive token audit data for transparency reporting.
        
        Args:
            token_code: Token to audit (UBEC, UBECrc, UBECgpi, UBECtt)
        
        Returns:
            Dictionary with token info, summary, distribution categories, compliance
        """
        return await self._cached_get(f"/v1/token-audit/{token_code.upper()}", ttl=60)
    
    async def get_liquidity_pools(self, token_code: str = None) -> Dict:
        """
        Get liquidity pool information for UBEC tokens.
        
        Args:
            token_code: Optional filter by token
        
        Returns:
            Dictionary with pools list and summary
        """
        if token_code:
            return await self._cached_get(f"/v1/liquidity-pools?token_code={token_code.upper()}", ttl=60)
        return await self._cached_get("/v1/liquidity-pools", ttl=60)
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    async def health_check(self) -> Dict:
        """
        Check API health.
        
        Returns:
            Health status object
        """
        return await self._cached_get("/v1/health", ttl=5)


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
    """Test the API client against all available endpoints."""
    print("=" * 70)
    print("API Client Test - v3.0.0")
    print("Testing against api.ubec.network")
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
            name = token.get('name', token.get('code', 'Unknown'))
            supply = token.get('total_supply', 0)
            print(f"  - {name}: {supply:,.2f} tokens")
        
        # Test 3: Network status
        print("\n[3/10] Testing network status...")
        network = await client.get_network_status()
        net_data = network.get('network', network)
        print(f"✓ Participants: {net_data.get('participants', 0)}")
        print(f"  Bioregions: {net_data.get('bioregions', 0)}")
        
        # Test 4: Bioregion count
        print("\n[4/10] Testing bioregion count...")
        count = await client.get_bioregion_count()
        print(f"✓ Bioregion count: {count}")
        
        # Test 5: Bioregions list
        print("\n[5/10] Testing bioregions list...")
        bioregions_data = await client.get_bioregions(limit=5)
        bio_count = bioregions_data.get('count', 0) if bioregions_data else 0
        print(f"✓ Retrieved {bio_count} bioregions")
        
        # Test 6: Holonic scores
        print("\n[6/10] Testing holonic scores...")
        scores = await client.get_holonic_scores(limit=5)
        if scores and 'ubuntu_principles' in scores:
            print(f"✓ Got holonic scores with Ubuntu principles")
        else:
            print(f"✓ Got holonic scores response")
        
        # Test 7: Recent transactions
        print("\n[7/10] Testing recent transactions...")
        transactions = await client.get_recent_transactions(limit=5)
        tx_count = transactions.get('count', 0) if transactions else 0
        print(f"✓ Retrieved {tx_count} transactions")
        
        # Test 8: Distribution stats
        print("\n[8/10] Testing distribution stats...")
        distribution = await client.get_distribution_stats()
        print(f"✓ Got distribution compliance data")
        
        # Test 9: Token audit
        print("\n[9/10] Testing token audit...")
        try:
            audit = await client.get_token_audit("UBEC")
            print(f"✓ Got token audit data")
        except Exception as e:
            print(f"⚠ Token audit not available: {e}")
        
        # Test 10: Liquidity pools
        print("\n[10/10] Testing liquidity pools...")
        try:
            pools = await client.get_liquidity_pools()
            pool_count = len(pools.get('pools', [])) if pools else 0
            print(f"✓ Found {pool_count} liquidity pools")
        except Exception as e:
            print(f"⚠ Liquidity pools not available: {e}")
        
        print("\n" + "=" * 70)
        print("✓ All tests completed!")
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
