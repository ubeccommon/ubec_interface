#!/usr/bin/env python3
"""
UBEC Interface API Endpoint Test Suite
======================================

Tests all frontend API endpoints to ensure proper data flow:
Backend API → Client → Routes → Response

Usage:
    python3 test_endpoints.py
    python3 test_endpoints.py --verbose
    python3 test_endpoints.py --backend-only
"""

import sys
import json
import time
import argparse
from typing import Dict, List, Tuple
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

# Configuration
BACKEND_URL = "http://92.205.230.245:8000"
FRONTEND_URL = "http://localhost:8001"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}{text:^70}{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓{NC} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗{NC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠{NC} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{CYAN}ℹ{NC} {text}")


def test_endpoint(url: str, name: str, verbose: bool = False) -> Tuple[bool, Dict]:
    """
    Test a single endpoint
    
    Args:
        url: Full URL to test
        name: Display name for the endpoint
        verbose: Show response data
        
    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    try:
        req = Request(url, headers={'Accept': 'application/json'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Check if response is valid JSON
            if isinstance(data, (dict, list)):
                print_success(f"{name}")
                
                if verbose:
                    print(f"  {CYAN}Response:{NC} {json.dumps(data, indent=2)[:200]}...")
                
                return True, data
            else:
                print_error(f"{name} - Invalid response type")
                return False, {}
                
    except HTTPError as e:
        print_error(f"{name} - HTTP {e.code}: {e.reason}")
        if verbose:
            try:
                error_body = e.read().decode('utf-8')[:200]
                print(f"  {CYAN}Error body:{NC} {error_body}...")
            except:
                pass
        return False, {}
        
    except URLError as e:
        print_error(f"{name} - Connection error: {e.reason}")
        return False, {}
        
    except json.JSONDecodeError as e:
        print_error(f"{name} - Invalid JSON response: {e}")
        return False, {}
        
    except Exception as e:
        print_error(f"{name} - Unexpected error: {e}")
        return False, {}


def test_backend_endpoints(verbose: bool = False) -> Dict[str, bool]:
    """Test all backend API endpoints"""
    print_header("Testing Backend API Endpoints")
    print_info(f"Backend URL: {BACKEND_URL}")
    
    results = {}
    
    # Core endpoints
    tests = [
        ("/api/v1/health", "Health Check"),
        ("/api/v1/tokens", "Token List"),
        ("/api/v1/network-status", "Network Status"),
        ("/api/v1/bioregions/count", "Bioregion Count"),
        ("/api/v1/bioregions/summary", "Bioregion Summary"),
        ("/api/v1/bioregions", "Bioregions List"),
        ("/api/v1/ecoregions?limit=5", "Ecoregions (limit 5)"),
        ("/api/v1/watersheds?limit=5", "Watersheds (limit 5)"),
        ("/api/v1/holonic-scores?limit=5", "Holonic Scores (limit 5)"),
        ("/api/v1/transactions?limit=5", "Transactions (limit 5)"),
        ("/api/v1/distribution", "Distribution Stats"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{BACKEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)  # Rate limiting
    
    return results


def test_frontend_endpoints(verbose: bool = False) -> Dict[str, bool]:
    """Test all frontend API endpoints"""
    print_header("Testing Frontend API Endpoints")
    print_info(f"Frontend URL: {FRONTEND_URL}")
    
    results = {}
    
    # System endpoints
    print(f"\n{MAGENTA}System Endpoints:{NC}")
    tests = [
        ("/api/v1/system/info", "System Info"),
        ("/api/v1/system/health", "System Health"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Token endpoints
    print(f"\n{MAGENTA}Token Endpoints:{NC}")
    tests = [
        ("/api/v1/tokens", "All Tokens"),
        ("/api/v1/tokens/UBEC", "Token: UBEC (Air)"),
        ("/api/v1/tokens/UBECrc", "Token: UBECrc (Water)"),
        ("/api/v1/tokens/UBECgpi", "Token: UBECgpi (Earth)"),
        ("/api/v1/tokens/UBECtt", "Token: UBECtt (Fire)"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Network endpoints
    print(f"\n{MAGENTA}Network Endpoints:{NC}")
    tests = [
        ("/api/v1/network/status", "Network Status"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Bioregion endpoints
    print(f"\n{MAGENTA}Bioregion Endpoints:{NC}")
    tests = [
        ("/api/v1/bioregions/count", "Bioregion Count"),
        ("/api/v1/bioregions/summary", "Bioregion Summary"),
        ("/api/v1/bioregions", "Bioregions List"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Ecoregion endpoints
    print(f"\n{MAGENTA}Ecoregion Endpoints:{NC}")
    tests = [
        ("/api/v1/ecoregions?limit=5", "Ecoregions (limit 5)"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Watershed endpoints
    print(f"\n{MAGENTA}Watershed Endpoints:{NC}")
    tests = [
        ("/api/v1/watersheds?limit=5", "Watersheds (limit 5)"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Holonic evaluation endpoints
    print(f"\n{MAGENTA}Holonic Evaluation Endpoints:{NC}")
    tests = [
        ("/api/v1/holonic/scores?limit=5", "Holonic Scores (limit 5)"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Transaction endpoints
    print(f"\n{MAGENTA}Transaction Endpoints:{NC}")
    tests = [
        ("/api/v1/transactions/recent?limit=5", "Recent Transactions"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    # Distribution endpoints
    print(f"\n{MAGENTA}Distribution Endpoints:{NC}")
    tests = [
        ("/api/v1/distributions/stats", "Distribution Stats"),
    ]
    
    for endpoint, name in tests:
        success, data = test_endpoint(f"{FRONTEND_URL}{endpoint}", name, verbose)
        results[name] = success
        time.sleep(0.1)
    
    return results


def print_summary(backend_results: Dict[str, bool], frontend_results: Dict[str, bool]):
    """Print test summary"""
    print_header("Test Summary")
    
    backend_passed = sum(1 for v in backend_results.values() if v)
    backend_total = len(backend_results)
    backend_pct = (backend_passed / backend_total * 100) if backend_total > 0 else 0
    
    frontend_passed = sum(1 for v in frontend_results.values() if v)
    frontend_total = len(frontend_results)
    frontend_pct = (frontend_passed / frontend_total * 100) if frontend_total > 0 else 0
    
    print(f"Backend API:  {backend_passed}/{backend_total} tests passed ({backend_pct:.1f}%)")
    print(f"Frontend API: {frontend_passed}/{frontend_total} tests passed ({frontend_pct:.1f}%)")
    
    total_passed = backend_passed + frontend_passed
    total_tests = backend_total + frontend_total
    total_pct = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nOverall:      {total_passed}/{total_tests} tests passed ({total_pct:.1f}%)")
    
    if total_pct == 100:
        print(f"\n{GREEN}{'=' * 70}{NC}")
        print(f"{GREEN}{'✓ ALL TESTS PASSED!':^70}{NC}")
        print(f"{GREEN}{'=' * 70}{NC}")
        return 0
    elif total_pct >= 80:
        print(f"\n{YELLOW}⚠ Some tests failed, but most endpoints are working{NC}")
        return 1
    else:
        print(f"\n{RED}✗ Many tests failed - check configuration{NC}")
        return 2


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Test UBEC API endpoints')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed response data')
    parser.add_argument('--backend-only', '-b', action='store_true',
                       help='Test only backend endpoints')
    parser.add_argument('--frontend-only', '-f', action='store_true',
                       help='Test only frontend endpoints')
    
    args = parser.parse_args()
    
    print(f"{CYAN}╔═══════════════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║          UBEC Interface API Endpoint Test Suite                  ║{NC}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════════════╝{NC}")
    
    backend_results = {}
    frontend_results = {}
    
    if not args.frontend_only:
        backend_results = test_backend_endpoints(args.verbose)
    
    if not args.backend_only:
        frontend_results = test_frontend_endpoints(args.verbose)
    
    return print_summary(backend_results, frontend_results)


if __name__ == "__main__":
    sys.exit(main())
