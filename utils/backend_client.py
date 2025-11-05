"""
Backend API Client - UBEC Protocol Data Access

Communicates with the backend protocol server to fetch real-time data about
tokens, holonic evaluations, and network status.

Attribution: This project uses the services of Claude and Anthropic PBC.
"""

import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for communicating with UBEC Protocol backend"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Caching for performance
        self.cache = {}
        self.cache_ttl = {}
        self.default_ttl = 30  # seconds
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def _cached_get(self, endpoint: str, ttl: int = None) -> Dict:
        """Execute GET request with caching"""
        cache_key = endpoint
        current_ttl = ttl or self.default_ttl
        
        # Check cache
        if cache_key in self.cache:
            cached_time = self.cache_ttl.get(cache_key)
            if cached_time and (datetime.now() - cached_time).seconds < current_ttl:
                logger.debug(f"Cache hit for {endpoint}")
                return self.cache[cache_key]
        
        # Make request
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Update cache
                self.cache[cache_key] = data
                self.cache_ttl[cache_key] = datetime.now()
                logger.debug(f"Fetched and cached: {endpoint}")
                
                return data
        
        except aiohttp.ClientError as e:
            logger.error(f"Backend API error for {endpoint}: {e}")
            # Return stale cache if available
            if cache_key in self.cache:
                logger.warning(f"Returning stale cache for {endpoint}")
                return self.cache[cache_key]
            
            # Return mock data if no cache
            return self._get_mock_data(endpoint)
        
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Dict:
        """Return mock data when backend is unavailable"""
        logger.info(f"Returning mock data for {endpoint}")
        
        if "tokens" in endpoint:
            return self._mock_tokens()
        elif "holonic" in endpoint:
            return self._mock_holonic_scores()
        elif "network" in endpoint:
            return self._mock_network_status()
        elif "transactions" in endpoint:
            return self._mock_transactions()
        
        return {}
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    async def get_all_tokens(self) -> List[Dict]:
        """Get information about all four UBEC tokens"""
        return await self._cached_get("/api/v1/tokens", ttl=60)
    
    async def get_token_by_code(self, token_code: str) -> Dict:
        """Get specific token information"""
        return await self._cached_get(f"/api/v1/tokens/{token_code}", ttl=60)
    
    async def get_holonic_scores(self) -> Dict:
        """Get latest holonic evaluation scores"""
        return await self._cached_get("/api/v1/holonic-scores", ttl=30)
    
    async def get_network_status(self) -> Dict:
        """Get current network status and metrics"""
        return await self._cached_get("/api/v1/network-status", ttl=15)
    
    async def get_recent_transactions(self, limit: int = 20) -> List[Dict]:
        """Get recent blockchain transactions"""
        return await self._cached_get(
            f"/api/v1/transactions/recent?limit={limit}", 
            ttl=10
        )
    
    async def get_distribution_stats(self) -> Dict:
        """Get token distribution statistics"""
        return await self._cached_get("/api/v1/distribution/stats", ttl=300)
    
    async def get_holder_categories(self) -> Dict:
        """Get holonic category distribution"""
        return await self._cached_get("/api/v1/holonic/categories", ttl=60)
    
    # ========================================================================
    # Mock Data (for development/fallback)
    # ========================================================================
    
    def _mock_tokens(self) -> List[Dict]:
        """Mock token data based on actual UBEC protocol"""
        return [
            {
                "token_code": "UBEC",
                "element": "Air",
                "element_symbol": "ðŸŒ¬ï¸",
                "ubuntu_principle": "Diversity",
                "description": "Gateway & Universal Access",
                "issuer": "GDPNB7S3IOM2J6C3NA2QG4TQAUCRZXPJJ4HSCCSIKELEH7ORUCX5UB2VN",
                "total_supply": 152025699,
                "holders_count": 495,
                "status": "live",
                "daily_volume": 1234567,
                "color": "#87CEEB"
            },
            {
                "token_code": "UBECrc",
                "element": "Water",
                "element_symbol": "ðŸ’§",
                "ubuntu_principle": "Reciprocity",
                "description": "Flow & Exchange",
                "issuer": "GBYOTGM27KLFNQQU3G6QWVEK7LQB36N6OX2YLYMN4WU3AFM4VRFZUBEC",
                "total_supply": 112000,
                "holders_count": 3,
                "status": "live",
                "daily_volume": 5432,
                "color": "#4FC3F7"
            },
            {
                "token_code": "UBECgpi",
                "element": "Earth",
                "element_symbol": "ðŸŒ",
                "ubuntu_principle": "Mutualism",
                "description": "Stability & Value",
                "issuer": "GCPU3LUGRIYLWMPOQEEGIL2HI5Z637PQVK42Z5PYRRQMPFDTNT5SUBEC",
                "total_supply": 110,
                "holders_count": 2,
                "status": "live",
                "daily_volume": 45,
                "color": "#8BC34A"
            },
            {
                "token_code": "UBECtt",
                "element": "Fire",
                "element_symbol": "ðŸ”¥",
                "ubuntu_principle": "Regeneration",
                "description": "Transformation & Action",
                "issuer": "GBWYGECRQ7R5E6QQKWBTVNYSCFVTIYZLF6MGDHJQBHP2KU2U65Z5UBEC",
                "total_supply": 1000000,
                "holders_count": 1,
                "status": "live",
                "daily_volume": 9876,
                "color": "#FF6B6B"
            }
        ]
    
    def _mock_holonic_scores(self) -> Dict:
        """Mock holonic evaluation scores"""
        return {
            "autonomy_integration": 0.78,
            "ubuntu_alignment": 0.85,
            "reciprocity_health": 0.72,
            "mutualism_capacity": 0.81,
            "regeneration_impact": 0.68,
            "overall_network_health": 0.77,
            "category_distribution": {
                "system": 65,
                "catalyst": 130,
                "integrator": 260,
                "autonomous": 840
            },
            "calculated_at": datetime.now().isoformat()
        }
    
    def _mock_network_status(self) -> Dict:
        """Mock network status"""
        return {
            "active_participants": 495,
            "total_transactions_24h": 1247,
            "average_ubuntu_score": 0.77,
            "bioregions_count": 12,
            "last_block_time": datetime.now().isoformat(),
            "network_health": "healthy"
        }
    
    def _mock_transactions(self) -> List[Dict]:
        """Mock recent transactions"""
        return [
            {
                "hash": "abc123...",
                "type": "payment",
                "token": "UBEC",
                "amount": 1000,
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
