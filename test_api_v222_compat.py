#!/usr/bin/env python3
"""
UBEC API v2.2.2 Compatibility Test Suite

Comprehensive testing to verify frontend compatibility with backend API v2.2.2.
Tests all endpoints, data structures, and new features.

Usage:
    python test_api_v222_compat.py              # Run all tests
    python test_api_v222_compat.py --verbose    # Detailed output
    python test_api_v222_compat.py --quick      # Quick smoke test

Attribution: This project uses the services of Claude and Anthropic PBC to inform 
our decisions and recommendations. This project was made possible with the 
assistance of Claude and Anthropic PBC.
"""

import asyncio
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# Import the fixed client
sys.path.insert(0, '/home/claude')
from backend_client_fixed import BackendAPIClient


class APICompatibilityTester:
    """Test suite for API v2.2.2 compatibility."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.client = None
        self.results = []
        
    def print_header(self, message):
        """Print test section header."""
        print(f"\n{BLUE}{'=' * 70}")
        print(f"{message}")
        print(f"{'=' * 70}{NC}\n")
    
    def print_test(self, name):
        """Print test name."""
        if self.verbose:
            print(f"{CYAN}Testing: {name}{NC}")
    
    def print_pass(self, message):
        """Print pass message."""
        print(f"{GREEN}✓ PASS: {message}{NC}")
    
    def print_fail(self, message):
        """Print fail message."""
        print(f"{RED}✗ FAIL: {message}{NC}")
    
    def print_warning(self, message):
        """Print warning message."""
        print(f"{YELLOW}⚠ WARNING: {message}{NC}")
    
    def record_result(self, test_name: str, passed: bool, message: str = ""):
        """Record test result."""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def setup(self):
        """Initialize test environment."""
        self.print_header("Test Setup")
        try:
            self.client = BackendAPIClient()
            self.print_pass("Backend client initialized")
            return True
        except Exception as e:
            self.print_fail(f"Failed to initialize client: {e}")
            return False
    
    async def teardown(self):
        """Cleanup test environment."""
        if self.client:
            await self.client.close()
            self.print_pass("Client closed")
    
    # ========================================================================
    # ENDPOINT TESTS
    # ========================================================================
    
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        self.print_test("Health Check Endpoint")
        try:
            health = await self.client.health_check()
            
            if not isinstance(health, dict):
                self.print_fail("Health check returned non-dict")
                self.record_result("health_endpoint", False, "Invalid response type")
                return False
            
            # Should have status
            if 'status' not in health:
                self.print_warning("Health response missing 'status' field")
            
            self.print_pass("Health endpoint working")
            self.record_result("health_endpoint", True)
            return True
            
        except Exception as e:
            self.print_fail(f"Health check failed: {e}")
            self.record_result("health_endpoint", False, str(e))
            return False
    
    async def test_tokens_endpoint(self):
        """Test tokens endpoint with v2.2.0 enhancements."""
        self.print_test("Tokens Endpoint (v2.2.0 enhancements)")
        try:
            tokens = await self.client.get_all_tokens()
            
            if not isinstance(tokens, list):
                self.print_fail("Tokens returned non-list")
                self.record_result("tokens_endpoint", False, "Invalid response type")
                return False
            
            if len(tokens) != 4:
                self.print_warning(f"Expected 4 tokens, got {len(tokens)}")
            
            # Check for v2.2.0 enhancements
            checks_passed = 0
            checks_total = 0
            
            for token in tokens:
                # Check for 'name' field (NEW in v2.2.0)
                checks_total += 1
                if 'name' in token:
                    checks_passed += 1
                    if self.verbose:
                        self.print_pass(f"Token {token.get('asset_code')} has 'name': {token['name']}")
                else:
                    self.print_warning(f"Token {token.get('asset_code')} missing 'name' field")
                
                # Check for 'total_supply' field (NEW in v2.2.0)
                checks_total += 1
                if 'total_supply' in token:
                    checks_passed += 1
                    if self.verbose:
                        self.print_pass(f"Token {token.get('asset_code')} has 'total_supply': {token['total_supply']}")
                else:
                    self.print_warning(f"Token {token.get('asset_code')} missing 'total_supply' field")
            
            success = checks_passed == checks_total
            self.print_pass(f"Tokens endpoint working ({checks_passed}/{checks_total} v2.2.0 fields present)")
            self.record_result("tokens_endpoint", success, f"{checks_passed}/{checks_total} enhancements")
            return success
            
        except Exception as e:
            self.print_fail(f"Tokens endpoint failed: {e}")
            self.record_result("tokens_endpoint", False, str(e))
            return False
    
    async def test_network_status_endpoint(self):
        """Test network status endpoint."""
        self.print_test("Network Status Endpoint")
        try:
            status = await self.client.get_network_status()
            
            if not isinstance(status, dict):
                self.print_fail("Network status returned non-dict")
                self.record_result("network_status", False, "Invalid response type")
                return False
            
            # Check expected fields
            expected_fields = ['total_holders', 'active_bioregions', 'overall_health_score']
            missing = [f for f in expected_fields if f not in status]
            
            if missing:
                self.print_warning(f"Missing fields: {missing}")
            
            self.print_pass("Network status endpoint working")
            self.record_result("network_status", True)
            return True
            
        except Exception as e:
            self.print_fail(f"Network status failed: {e}")
            self.record_result("network_status", False, str(e))
            return False
    
    async def test_holonic_scores_endpoint(self):
        """Test holonic scores endpoint with v2.2.0 enhancements."""
        self.print_test("Holonic Scores Endpoint (v2.2.0 enhancements)")
        try:
            scores = await self.client.get_holonic_scores(limit=5)
            
            if not isinstance(scores, dict):
                self.print_fail("Holonic scores returned non-dict")
                self.record_result("holonic_scores", False, "Invalid response type")
                return False
            
            # Check response structure
            has_summary = 'summary' in scores
            has_accounts = 'accounts' in scores  # CRITICAL: Must be 'accounts' not 'evaluations'
            has_category_dist = 'category_distribution' in scores
            
            if not has_summary:
                self.print_fail("Missing 'summary' key in response")
                self.record_result("holonic_scores", False, "Missing summary")
                return False
            
            if not has_accounts:
                self.print_fail("Missing 'accounts' key in response (CRITICAL ERROR)")
                self.record_result("holonic_scores", False, "Missing accounts key")
                return False
            
            # Check for v2.2.0 Ubuntu metrics
            summary = scores['summary']
            checks_passed = 0
            checks_total = 0
            
            # Check for reciprocity_health (NEW in v2.2.0)
            checks_total += 1
            if 'average_reciprocity_health' in summary:
                checks_passed += 1
                if self.verbose:
                    self.print_pass(f"Has reciprocity_health: {summary['average_reciprocity_health']}")
            else:
                self.print_warning("Missing average_reciprocity_health field")
            
            # Check for mutualism_capacity (NEW in v2.2.0)
            checks_total += 1
            if 'average_mutualism_capacity' in summary:
                checks_passed += 1
                if self.verbose:
                    self.print_pass(f"Has mutualism_capacity: {summary['average_mutualism_capacity']}")
            else:
                self.print_warning("Missing average_mutualism_capacity field")
            
            success = checks_passed == checks_total and has_accounts
            self.print_pass(f"Holonic scores endpoint working ({checks_passed}/{checks_total} v2.2.0 metrics)")
            self.record_result("holonic_scores", success, f"{checks_passed}/{checks_total} enhancements")
            return success
            
        except Exception as e:
            self.print_fail(f"Holonic scores failed: {e}")
            self.record_result("holonic_scores", False, str(e))
            return False
    
    async def test_transactions_endpoint(self):
        """Test transactions endpoint with corrected URL."""
        self.print_test("Transactions Endpoint (corrected URL)")
        try:
            # Test without offset
            transactions = await self.client.get_recent_transactions(limit=5)
            
            if not isinstance(transactions, dict):
                self.print_fail("Transactions returned non-dict")
                self.record_result("transactions_endpoint", False, "Invalid response type")
                return False
            
            # Check expected fields
            if 'transactions' not in transactions:
                self.print_fail("Missing 'transactions' key")
                self.record_result("transactions_endpoint", False, "Missing transactions key")
                return False
            
            # Test with offset (pagination)
            try:
                transactions_page2 = await self.client.get_recent_transactions(limit=5, offset=5)
                if self.verbose:
                    self.print_pass("Pagination (offset) working")
            except Exception as e:
                self.print_warning(f"Pagination may not be working: {e}")
            
            self.print_pass("Transactions endpoint working with correct URL (/recent)")
            self.record_result("transactions_endpoint", True)
            return True
            
        except Exception as e:
            self.print_fail(f"Transactions failed: {e}")
            self.record_result("transactions_endpoint", False, str(e))
            return False
    
    async def test_distribution_endpoint(self):
        """Test distribution stats endpoint."""
        self.print_test("Distribution Stats Endpoint")
        try:
            distribution = await self.client.get_distribution_stats()
            
            if not isinstance(distribution, dict):
                self.print_fail("Distribution returned non-dict")
                self.record_result("distribution_endpoint", False, "Invalid response type")
                return False
            
            self.print_pass("Distribution endpoint working")
            self.record_result("distribution_endpoint", True)
            return True
            
        except Exception as e:
            self.print_fail(f"Distribution failed: {e}")
            self.record_result("distribution_endpoint", False, str(e))
            return False
    
    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================
    
    async def test_dashboard_data_structure(self):
        """Test that all dashboard data can be fetched and structured correctly."""
        self.print_test("Dashboard Data Integration")
        try:
            # Fetch all dashboard components
            network_status = await self.client.get_network_status()
            holonic_scores = await self.client.get_holonic_scores(limit=10)
            transactions = await self.client.get_recent_transactions(limit=20)
            distribution = await self.client.get_distribution_stats()
            
            # Verify structure matches dashboard expectations
            checks = []
            
            # Network status structure
            checks.append(('network_status_valid', isinstance(network_status, dict)))
            
            # Holonic scores structure (CRITICAL)
            if isinstance(holonic_scores, dict):
                checks.append(('holonic_has_summary', 'summary' in holonic_scores))
                checks.append(('holonic_has_accounts', 'accounts' in holonic_scores))  # Not 'evaluations'!
            else:
                checks.append(('holonic_structure', False))
            
            # Transactions structure
            if isinstance(transactions, dict):
                checks.append(('transactions_has_list', 'transactions' in transactions))
            else:
                checks.append(('transactions_structure', False))
            
            passed = sum(1 for _, result in checks if result)
            total = len(checks)
            
            if passed == total:
                self.print_pass(f"Dashboard data structure compatible ({passed}/{total})")
                self.record_result("dashboard_integration", True)
                return True
            else:
                self.print_fail(f"Dashboard data structure issues ({passed}/{total} checks passed)")
                if self.verbose:
                    for check_name, result in checks:
                        status = "✓" if result else "✗"
                        print(f"  {status} {check_name}")
                self.record_result("dashboard_integration", False, f"{passed}/{total} checks")
                return False
            
        except Exception as e:
            self.print_fail(f"Dashboard integration test failed: {e}")
            self.record_result("dashboard_integration", False, str(e))
            return False
    
    # ========================================================================
    # TEST RUNNER
    # ========================================================================
    
    async def run_all_tests(self, quick=False):
        """Run all compatibility tests."""
        self.print_header("UBEC API v2.2.2 Compatibility Test Suite")
        print(f"Testing backend at: {self.client.base_url if self.client else 'Not initialized'}")
        print(f"Test mode: {'Quick smoke test' if quick else 'Full test suite'}")
        
        # Setup
        if not await self.setup():
            return False
        
        # Run tests
        tests = [
            self.test_health_endpoint,
            self.test_tokens_endpoint,
            self.test_network_status_endpoint,
            self.test_holonic_scores_endpoint,
            self.test_transactions_endpoint,
            self.test_distribution_endpoint,
        ]
        
        if not quick:
            tests.append(self.test_dashboard_data_structure)
        
        for test_func in tests:
            await test_func()
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Cleanup
        await self.teardown()
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results summary."""
        self.print_header("Test Results Summary")
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests passed: {passed}/{total} ({percentage:.1f}%)")
        print()
        
        # Critical failures
        critical_tests = ['holonic_scores', 'transactions_endpoint', 'dashboard_integration']
        critical_failures = [
            r for r in self.results 
            if not r['passed'] and any(ct in r['test'] for ct in critical_tests)
        ]
        
        if critical_failures:
            self.print_fail("CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"  - {failure['test']}: {failure['message']}")
            print()
        
        # Overall status
        if passed == total:
            self.print_pass("✓ ALL TESTS PASSED - API v2.2.2 COMPATIBLE")
            return True
        elif percentage >= 80 and not critical_failures:
            self.print_warning(f"⚠ MOSTLY COMPATIBLE ({percentage:.1f}%) - Minor issues only")
            return True
        else:
            self.print_fail("✗ COMPATIBILITY ISSUES DETECTED - Review failures above")
            return False


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test API v2.2.2 compatibility")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick smoke test")
    args = parser.parse_args()
    
    tester = APICompatibilityTester(verbose=args.verbose)
    await tester.run_all_tests(quick=args.quick)
    
    # Exit with appropriate code
    passed = sum(1 for r in tester.results if r['passed'])
    total = len(tester.results)
    
    if passed == total:
        return 0
    elif passed / total >= 0.8:
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
