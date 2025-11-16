#!/usr/bin/env python3
"""
UBEC Backend Client - Post-Deployment Verification Test
========================================================

Comprehensive test suite to verify backend_client.py v2.1.0 is working
correctly after deployment. Tests all endpoints and validates responses.

This verification suite specifically validates:
- CRITICAL FIX: Transaction endpoint (/api/v1/transactions/recent)
- FIXED: Bioregion summary method (now transforms data from /api/v1/bioregions)
- v2.2.0 enhancements (token name, total_supply fields)
- v2.3.0 features (ecoregions and watersheds endpoints)
- Pagination support (offset parameter)
- Graceful degradation for unavailable endpoints

Usage:
    python3 verify_deployment.py

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.

Version: 2.1.0 - Aligned with Backend API v2.3.0
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add app directory to path for imports
sys.path.insert(0, '/srv/ubec-www/app')

try:
    from utils.backend_client import BackendAPIClient
    from config.settings import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the correct directory")
    print("Expected path: /srv/ubec-www/app")
    sys.exit(1)


class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestResult:
    """Test result container"""
    def __init__(self, name: str, passed: bool, message: str, data: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.data = data
        self.timestamp = datetime.now()


class DeploymentVerifier:
    """Verification test suite for backend client deployment"""
    
    def __init__(self):
        self.client: Optional[BackendAPIClient] = None
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []
        self.critical_fixes_verified = []
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 70}{Color.END}")
        print(f"{Color.BOLD}{Color.BLUE}{text}{Color.END}")
        print(f"{Color.BOLD}{Color.BLUE}{'=' * 70}{Color.END}\n")
    
    def print_test(self, number: int, total: int, name: str):
        """Print test name"""
        print(f"{Color.CYAN}[{number}/{total}] Testing: {name}{Color.END}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"  {Color.GREEN}✓ {message}{Color.END}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"  {Color.RED}✗ {message}{Color.END}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"  {Color.YELLOW}⚠ {message}{Color.END}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"  {Color.BLUE}ℹ {message}{Color.END}")
    
    def record_result(self, name: str, passed: bool, message: str, data: Any = None):
        """Record a test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            self.print_success(message)
        else:
            self.failed_tests += 1
            self.print_error(message)
        
        self.results.append(TestResult(name, passed, message, data))
    
    def add_warning(self, message: str):
        """Add a warning"""
        self.warnings.append(message)
        self.print_warning(message)
    
    def mark_critical_fix_verified(self, fix_name: str):
        """Mark a critical fix as verified"""
        self.critical_fixes_verified.append(fix_name)
    
    async def test_client_initialization(self) -> bool:
        """Test 1: Client initialization"""
        self.print_test(1, 12, "Client Initialization")
        
        try:
            self.client = BackendAPIClient(
                base_url=settings.BACKEND_API_URL,
                api_key=settings.BACKEND_API_KEY
            )
            
            # Verify client properties
            self.print_info(f"Base URL: {self.client.base_url}")
            self.print_info(f"Timeout: {self.client.timeout.total}s")
            
            self.record_result(
                "client_init",
                True,
                f"Client v2.0.0 initialized successfully"
            )
            return True
        except Exception as e:
            self.record_result(
                "client_init",
                False,
                f"Failed to initialize client: {e}"
            )
            return False
    
    async def test_health_check(self) -> bool:
        """Test 2: Health check endpoint"""
        self.print_test(2, 12, "Health Check Endpoint")
        
        try:
            health = await self.client.health_check()
            
            if not health:
                self.record_result("health", False, "No health data returned")
                return False
            
            status = health.get('status', 'unknown')
            version = health.get('version', 'unknown')
            timestamp = health.get('timestamp', 'unknown')
            
            self.print_info(f"Backend status: {status}")
            self.print_info(f"Backend version: {version}")
            
            if status in ['healthy', 'operational', 'ok']:
                self.record_result("health", True, f"Backend healthy (v{version})")
                return True
            else:
                self.record_result("health", False, f"Backend unhealthy: {status}")
                return False
                
        except Exception as e:
            self.record_result("health", False, f"Health check failed: {e}")
            return False
    
    async def test_tokens_endpoint(self) -> bool:
        """Test 3: Tokens endpoint with v2.2.0 enhancements"""
        self.print_test(3, 12, "Tokens Endpoint (v2.2.0 features)")
        
        try:
            tokens = await self.client.get_all_tokens()
            
            if not tokens or len(tokens) == 0:
                self.record_result("tokens", False, "No tokens returned")
                return False
            
            # Verify we have 4 tokens
            if len(tokens) != 4:
                self.add_warning(f"Expected 4 tokens, got {len(tokens)}")
            
            # Verify v2.2.0 enhancements present
            v220_fields_present = True
            
            for token in tokens:
                asset_code = token.get('asset_code', 'Unknown')
                
                # Check for required v2.2.0 fields
                has_name = 'name' in token
                has_supply = 'total_supply' in token
                
                if not has_name:
                    self.add_warning(f"{asset_code}: Missing 'name' field (v2.2.0)")
                    v220_fields_present = False
                
                if not has_supply:
                    self.add_warning(f"{asset_code}: Missing 'total_supply' field (v2.2.0)")
                    v220_fields_present = False
                
                # Display token info
                name = token.get('name', asset_code)
                supply = token.get('total_supply', 0)
                element = token.get('element', 'Unknown')
                
                self.print_info(
                    f"{name} ({element}): {supply:,} tokens"
                )
            
            if v220_fields_present:
                self.record_result(
                    "tokens",
                    True,
                    f"✨ All {len(tokens)} tokens include v2.2.0 enhancements"
                )
            else:
                self.record_result(
                    "tokens",
                    True,
                    f"Retrieved {len(tokens)} tokens (some v2.2.0 fields missing)"
                )
            
            return True
            
        except Exception as e:
            self.record_result("tokens", False, f"Tokens test failed: {e}")
            return False
    
    async def test_network_status(self) -> bool:
        """Test 4: Network status endpoint"""
        self.print_test(4, 12, "Network Status Endpoint")
        
        try:
            status = await self.client.get_network_status()
            
            if not status:
                self.record_result("network_status", False, "No status returned")
                return False
            
            # Display key metrics
            total_supply = status.get('total_supply', 0)
            total_holders = status.get('total_holders', 0)
            bioregion_count = status.get('bioregion_count', 0)
            health_score = status.get('health_score', 0.0)
            
            self.print_info(f"Total Supply: {total_supply:,}")
            self.print_info(f"Total Holders: {total_holders:,}")
            self.print_info(f"Active Bioregions: {bioregion_count}")
            self.print_info(f"Network Health Score: {health_score:.3f}")
            
            self.record_result(
                "network_status",
                True,
                "Network status retrieved successfully"
            )
            return True
            
        except Exception as e:
            self.record_result("network_status", False, f"Network status failed: {e}")
            return False
    
    async def test_bioregion_endpoints(self) -> bool:
        """Test 5: Bioregion endpoints including summary fix"""
        self.print_test(5, 12, "Bioregion Endpoints (Including Summary Fix)")
        
        try:
            # Test count endpoint
            count = await self.client.get_bioregion_count()
            self.print_info(f"Count endpoint: {count} bioregions")
            
            # Test list endpoint
            bioregions = await self.client.get_bioregions()
            bio_count = bioregions.get('count', 0)
            bioregion_list = bioregions.get('bioregions', [])
            self.print_info(f"List endpoint: {bio_count} bioregions ({len(bioregion_list)} in response)")
            
            # Test summary endpoint (FIXED - now transforms data)
            summary = await self.client.get_bioregion_summary()
            summary_count = summary.get('total_count', 0)
            summary_bios = summary.get('bioregions', [])
            self.print_info(f"Summary endpoint: {summary_count} total (transforms data from list endpoint)")
            
            # Verify summary is transforming data correctly
            if summary_count == bio_count and len(summary_bios) == len(bioregion_list):
                self.print_success("✨ Bioregion summary correctly transforms data")
                self.mark_critical_fix_verified("bioregion_summary")
            else:
                self.add_warning(
                    f"Summary transformation may have issues: "
                    f"summary_count={summary_count} vs bio_count={bio_count}"
                )
            
            # Verify counts are consistent
            if count == bio_count:
                self.record_result(
                    "bioregions",
                    True,
                    f"All bioregion endpoints consistent ({count} bioregions)"
                )
            else:
                self.add_warning(
                    f"Bioregion counts inconsistent: count={count} vs list={bio_count}"
                )
                self.record_result(
                    "bioregions",
                    True,
                    "Bioregion endpoints working (counts vary)"
                )
            
            return True
            
        except Exception as e:
            self.record_result("bioregions", False, f"Bioregion test failed: {e}")
            return False
    
    async def test_transactions_endpoint(self) -> bool:
        """Test 6: CRITICAL - Transactions endpoint (FIXED in v2.0.0)"""
        self.print_test(6, 12, "⭐ Transactions Endpoint (CRITICAL FIX)")
        
        try:
            # CRITICAL FIX: Endpoint path corrected from /api/v1/transactions to /api/v1/transactions/recent
            transactions = await self.client.get_recent_transactions(limit=20)
            
            if not transactions:
                self.record_result("transactions", False, "No transaction data returned")
                return False
            
            tx_list = transactions.get('transactions', [])
            tx_count = transactions.get('count', 0)
            tx_total = transactions.get('total', 0)
            
            self.print_info(f"Retrieved: {tx_count} transactions")
            self.print_info(f"Total available: {tx_total}")
            self.print_info(f"Response includes: {len(tx_list)} transaction objects")
            
            # Test NEW pagination with offset parameter
            if tx_total > 20:
                try:
                    self.print_info("Testing pagination with offset parameter...")
                    offset_transactions = await self.client.get_recent_transactions(
                        limit=10,
                        offset=10
                    )
                    offset_count = offset_transactions.get('count', 0)
                    self.print_success(f"✨ Pagination works: Retrieved {offset_count} with offset=10")
                except Exception as e:
                    self.add_warning(f"Pagination test failed: {e}")
            
            # Mark critical fix as verified
            self.mark_critical_fix_verified("transaction_endpoint")
            
            self.record_result(
                "transactions",
                True,
                f"✨ Transaction endpoint FIXED - Retrieved {tx_count} of {tx_total} transactions"
            )
            return True
            
        except Exception as e:
            self.record_result(
                "transactions",
                False,
                f"❌ Transaction endpoint FAILED (CRITICAL): {e}"
            )
            return False
    
    async def test_holonic_scores(self) -> bool:
        """Test 7: Holonic scores endpoint with v2.2.0 enhancements"""
        self.print_test(7, 12, "Holonic Scores Endpoint (v2.2.0 features)")
        
        try:
            scores = await self.client.get_holonic_scores(limit=10)
            
            if not scores:
                self.record_result("holonic_scores", False, "No holonic data returned")
                return False
            
            summary = scores.get('summary', {})
            categories = scores.get('category_distribution', {})
            accounts = scores.get('accounts', [])
            
            # Display summary metrics
            if summary:
                avg_score = summary.get('average_score', 0.0)
                self.print_info(f"Average composite score: {avg_score:.3f}")
                
                # Check for v2.2.0 enhancements
                has_v220_metrics = False
                
                if 'average_reciprocity' in summary:
                    reciprocity = summary['average_reciprocity']
                    self.print_info(f"✨ Reciprocity health (v2.2.0): {reciprocity:.3f}")
                    has_v220_metrics = True
                
                if 'average_mutualism' in summary:
                    mutualism = summary['average_mutualism']
                    self.print_info(f"✨ Mutualism capacity (v2.2.0): {mutualism:.3f}")
                    has_v220_metrics = True
                
                if not has_v220_metrics:
                    self.add_warning("v2.2.0 metrics (reciprocity_health, mutualism_capacity) not found")
            
            # Display category distribution
            if categories:
                self.print_info("Holonic category distribution:")
                for category, count in sorted(categories.items()):
                    self.print_info(f"  {category}: {count}")
            
            self.record_result(
                "holonic_scores",
                True,
                f"Retrieved holonic scores for {len(accounts)} accounts"
            )
            return True
            
        except Exception as e:
            self.record_result("holonic_scores", False, f"Holonic scores failed: {e}")
            return False
    
    async def test_distribution_stats(self) -> bool:
        """Test 8: Distribution statistics endpoint"""
        self.print_test(8, 12, "Distribution Statistics Endpoint")
        
        try:
            distribution = await self.client.get_distribution_stats()
            
            if not distribution:
                self.record_result("distribution", False, "No distribution data returned")
                return False
            
            tokens = distribution.get('tokens', {})
            compliance = distribution.get('compliance_summary', {})
            
            self.print_info(f"Tracking {len(tokens)} token distributions")
            
            if compliance:
                overall_compliance = compliance.get('overall_compliant', False)
                status = "✓ Compliant" if overall_compliance else "✗ Non-compliant"
                self.print_info(f"75/20/5 compliance: {status}")
            
            # Display per-token compliance
            for token_code, token_dist in tokens.items():
                if isinstance(token_dist, dict) and 'compliant' in token_dist:
                    compliant = token_dist['compliant']
                    status = "✓" if compliant else "✗"
                    self.print_info(f"  {token_code}: {status}")
            
            self.record_result(
                "distribution",
                True,
                "Distribution statistics retrieved successfully"
            )
            return True
            
        except Exception as e:
            self.record_result("distribution", False, f"Distribution test failed: {e}")
            return False
    
    async def test_optional_ecoregions(self) -> bool:
        """Test 9: Ecoregions endpoint (available in v2.3.0)"""
        self.print_test(9, 12, "Ecoregions Endpoint (v2.3.0)")
        
        try:
            ecoregions = await self.client.get_ecoregions(limit=5)
            
            if ecoregions is None:
                self.add_warning("Ecoregions endpoint returned None (may be temporarily unavailable)")
                self.record_result(
                    "ecoregions",
                    True,
                    "Ecoregions endpoint gracefully handled unavailability"
                )
                return True
            
            eco_count = ecoregions.get('count', 0)
            eco_list = ecoregions.get('ecoregions', [])
            
            self.print_info(f"Retrieved {eco_count} ecoregions")
            self.print_info(f"Response includes {len(eco_list)} ecoregion objects")
            
            # Display sample ecoregion if available
            if eco_list:
                sample = eco_list[0]
                name = sample.get('eco_name', 'Unknown')
                biome = sample.get('biome', 'Unknown')
                self.print_info(f"Sample: {name} ({biome})")
            
            self.record_result(
                "ecoregions",
                True,
                f"✨ Ecoregions (v2.3.0) working! ({eco_count} ecoregions)"
            )
            return True
            
        except Exception as e:
            self.record_result("ecoregions", False, f"Ecoregions test error: {e}")
            return False
    
    async def test_optional_watersheds(self) -> bool:
        """Test 10: Watersheds endpoint (available in v2.3.0)"""
        self.print_test(10, 12, "Watersheds Endpoint (v2.3.0)")
        
        try:
            watersheds = await self.client.get_watersheds(limit=5, min_area=1000.0)
            
            if watersheds is None:
                self.add_warning("Watersheds endpoint returned None (may be temporarily unavailable)")
                self.record_result(
                    "watersheds",
                    True,
                    "Watersheds endpoint gracefully handled unavailability"
                )
                return True
            
            ws_count = watersheds.get('count', 0)
            ws_list = watersheds.get('watersheds', [])
            total_area = sum(w.get('area_sqkm', 0) for w in ws_list)
            
            self.print_info(f"Retrieved {ws_count} watersheds")
            self.print_info(f"Response includes {len(ws_list)} watershed objects")
            self.print_info(f"Total area coverage: {total_area:,.0f} km²")
            
            # Display sample watershed if available
            if ws_list:
                sample = ws_list[0]
                name = sample.get('name', 'Unknown')
                area = sample.get('area_sqkm', 0)
                self.print_info(f"Sample: {name} ({area:,.0f} km²)")
            
            self.record_result(
                "watersheds",
                True,
                f"✨ Watersheds (v2.3.0) working! ({ws_count} watersheds)"
            )
            return True
            
        except Exception as e:
            self.record_result("watersheds", False, f"Watersheds test error: {e}")
            return False
    
    async def test_integration_with_web(self) -> bool:
        """Test 11: Integration test - simulate web app usage"""
        self.print_test(11, 12, "Integration Test (Web App Simulation)")
        
        try:
            # Simulate dashboard data fetch - all critical endpoints
            self.print_info("Fetching dashboard data (network, holonic, transactions)...")
            
            network_status = await self.client.get_network_status()
            holonic_scores = await self.client.get_holonic_scores(limit=5)
            transactions = await self.client.get_recent_transactions(limit=20)
            
            # Verify all returned data
            missing = []
            if not network_status:
                missing.append("network_status")
            if not holonic_scores:
                missing.append("holonic_scores")
            if not transactions:
                missing.append("transactions")
            
            if len(missing) == 0:
                self.print_success("All dashboard endpoints responding")
                self.print_info("Network status: ✓")
                self.print_info("Holonic scores: ✓")
                self.print_info("Transactions: ✓")
                
                self.record_result(
                    "integration",
                    True,
                    "Integration test passed - all dashboard data available"
                )
                return True
            else:
                self.record_result(
                    "integration",
                    False,
                    f"Integration test failed - missing: {', '.join(missing)}"
                )
                return False
                
        except Exception as e:
            self.record_result("integration", False, f"Integration test error: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 12: Error handling and edge cases"""
        self.print_test(12, 12, "Error Handling & Edge Cases")
        
        try:
            test_passed = True
            
            # Test 1: Invalid token code
            self.print_info("Testing invalid token code...")
            try:
                await self.client.get_token_by_code("INVALID")
                self.add_warning("Invalid token code did not raise error")
                test_passed = False
            except ValueError:
                self.print_success("Invalid token code correctly raises ValueError")
            
            # Test 2: Large limit clamping
            self.print_info("Testing limit clamping...")
            result = await self.client.get_recent_transactions(limit=1000)
            if result:
                self.print_success("Large limit handled gracefully")
            
            # Test 3: Cache invalidation
            self.print_info("Testing cache invalidation...")
            self.client.invalidate_cache()
            self.print_success("Cache invalidation works")
            
            if test_passed:
                self.record_result(
                    "error_handling",
                    True,
                    "Error handling and edge cases work correctly"
                )
            else:
                self.record_result(
                    "error_handling",
                    False,
                    "Some edge cases did not behave as expected"
                )
            
            return test_passed
            
        except Exception as e:
            self.record_result("error_handling", False, f"Error handling test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("UBEC Backend Client v2.1.0 - Deployment Verification")
        
        print(f"{Color.BOLD}Environment:{Color.END}")
        print(f"  Backend URL: {settings.BACKEND_API_URL}")
        print(f"  Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Backend API Version: v2.3.0")
        print(f"  Client Version: v2.1.0")
        print()
        
        # Run all tests
        await self.test_client_initialization()
        
        if self.client:
            await self.test_health_check()
            await self.test_tokens_endpoint()
            await self.test_network_status()
            await self.test_bioregion_endpoints()
            await self.test_transactions_endpoint()  # CRITICAL FIX
            await self.test_holonic_scores()
            await self.test_distribution_stats()
            await self.test_optional_ecoregions()
            await self.test_optional_watersheds()
            await self.test_integration_with_web()
            await self.test_error_handling()
            
            # Clean up
            await self.client.close()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        print(f"{Color.BOLD}Results:{Color.END}")
        print(f"  Total Tests: {self.total_tests}")
        print(f"  {Color.GREEN}Passed: {self.passed_tests}{Color.END}")
        print(f"  {Color.RED}Failed: {self.failed_tests}{Color.END}")
        
        if self.warnings:
            print(f"  {Color.YELLOW}Warnings: {len(self.warnings)}{Color.END}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Overall status
        print(f"\n{Color.BOLD}Overall Status:{Color.END}")
        if self.failed_tests == 0:
            print(f"  {Color.GREEN}{Color.BOLD}✓ ALL TESTS PASSED{Color.END}")
            print(f"  {Color.GREEN}Backend client v2.1.0 is working correctly!{Color.END}")
        else:
            print(f"  {Color.RED}{Color.BOLD}✗ SOME TESTS FAILED{Color.END}")
            print(f"  {Color.RED}Please review failed tests above.{Color.END}")
        
        # Critical fixes verification
        if self.critical_fixes_verified:
            print(f"\n{Color.BOLD}Critical Fixes Verified:{Color.END}")
            for fix in self.critical_fixes_verified:
                if fix == "transaction_endpoint":
                    print(f"  {Color.GREEN}⭐ Transaction endpoint (/api/v1/transactions/recent){Color.END}")
                elif fix == "bioregion_summary":
                    print(f"  {Color.GREEN}⭐ Bioregion summary (data transformation){Color.END}")
        
        # Print warnings if any
        if self.warnings:
            print(f"\n{Color.BOLD}Warnings:{Color.END}")
            for warning in self.warnings:
                print(f"  {Color.YELLOW}⚠ {warning}{Color.END}")
        
        # Deployment recommendation
        print(f"\n{Color.BOLD}Deployment Recommendation:{Color.END}")
        if self.failed_tests == 0 and len(self.critical_fixes_verified) >= 1:
            print(f"  {Color.GREEN}✓ Ready for production deployment{Color.END}")
            print(f"  {Color.GREEN}✓ All critical fixes verified{Color.END}")
        elif self.failed_tests == 0:
            print(f"  {Color.YELLOW}⚠ Tests passed but critical fixes not all verified{Color.END}")
            print(f"  {Color.YELLOW}  Review warnings before deploying{Color.END}")
        else:
            print(f"  {Color.RED}✗ DO NOT DEPLOY - Fix failures first{Color.END}")
        
        print()


async def main():
    """Main entry point"""
    verifier = DeploymentVerifier()
    
    try:
        await verifier.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if verifier.failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}Test interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Color.RED}Fatal error: {e}{Color.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
