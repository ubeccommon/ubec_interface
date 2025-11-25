#!/usr/bin/env python3
"""
Backend Endpoint Response Inspector
====================================

Checks what each backend endpoint is actually returning and compares
with what the frontend template expects.

Usage:
    python3 inspect_backend_responses.py
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BACKEND_URL = "http://92.205.230.245:8000"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.END}\n")


def print_json(data: Any, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


async def test_endpoint(session: aiohttp.ClientSession, endpoint: str, name: str) -> Dict:
    """Test an endpoint and return response."""
    url = f"{BACKEND_URL}{endpoint}"
    print(f"{Colors.CYAN}Testing:{Colors.END} {endpoint}")
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                data = await response.json()
                print(f"{Colors.GREEN}✓ Status: {response.status}{Colors.END}")
                return {"success": True, "data": data}
            else:
                text = await response.text()
                print(f"{Colors.RED}✗ Status: {response.status}{Colors.END}")
                print(f"{Colors.YELLOW}Response: {text[:200]}{Colors.END}")
                return {"success": False, "status": response.status, "text": text}
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        return {"success": False, "error": str(e)}


async def inspect():
    """Inspect all backend endpoints."""
    
    print_section("UBEC Backend Endpoint Inspector")
    print(f"Backend URL: {BACKEND_URL}\n")
    
    async with aiohttp.ClientSession() as session:
        
        # ================================================================
        # 1. NETWORK STATUS
        # ================================================================
        print_section("1. Network Status Endpoint")
        result = await test_endpoint(session, "/api/v1/network-status", "Network Status")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Raw Response Structure:{Colors.END}")
            print(f"Type: {type(data)}")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            print(f"\n{Colors.CYAN}Full Response:{Colors.END}")
            print_json(data)
            
            print(f"\n{Colors.YELLOW}Template Expects These Fields:{Colors.END}")
            expected = {
                "active_participants": "network_status.get('total_holders', 0)",
                "total_transactions_24h": "network_status.get('transactions_24h', 0)",
                "bioregions_count": "network_status.get('active_bioregions', 0)",
                "average_ubuntu_score": "network_status.get('overall_health_score', 0.0)",
                "last_block_time": "network_status.get('timestamp', 'Unavailable')"
            }
            
            print(f"\n{Colors.CYAN}Field Mapping Check:{Colors.END}")
            for template_field, backend_path in expected.items():
                # Extract backend field name
                backend_field = backend_path.split("'")[1] if "'" in backend_path else "unknown"
                value = data.get(backend_field, "MISSING")
                status = f"{Colors.GREEN}✓" if backend_field in data else f"{Colors.RED}✗"
                print(f"{status} {template_field:25} ← {backend_field:25} = {value}{Colors.END}")
        
        # ================================================================
        # 2. HOLONIC SCORES
        # ================================================================
        print_section("2. Holonic Scores Endpoint")
        result = await test_endpoint(session, "/api/v1/holonic-scores?limit=5", "Holonic Scores")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Raw Response Structure:{Colors.END}")
            print(f"Type: {type(data)}")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            if isinstance(data, dict):
                if "summary" in data:
                    print(f"\n{Colors.CYAN}Summary Keys:{Colors.END}")
                    print(list(data["summary"].keys()))
                    print(f"\n{Colors.CYAN}Summary Data:{Colors.END}")
                    print_json(data["summary"])
                
                if "evaluations" in data:
                    print(f"\n{Colors.CYAN}Evaluations Count:{Colors.END} {len(data['evaluations'])}")
                    if data["evaluations"]:
                        print(f"\n{Colors.CYAN}First Evaluation Structure:{Colors.END}")
                        print_json(data["evaluations"][0])
            
            print(f"\n{Colors.YELLOW}Template Expects These Summary Fields:{Colors.END}")
            expected_summary = [
                "average_composite_score",
                "average_diversity",
                "average_holism",
                "average_reciprocity",
                "average_mutualism",
                "average_regeneration"
            ]
            
            if isinstance(data, dict) and "summary" in data:
                summary = data["summary"]
                print(f"\n{Colors.CYAN}Summary Field Check:{Colors.END}")
                for field in expected_summary:
                    value = summary.get(field, "MISSING")
                    status = f"{Colors.GREEN}✓" if field in summary else f"{Colors.RED}✗"
                    print(f"{status} {field:30} = {value}{Colors.END}")
        
        # ================================================================
        # 3. TRANSACTIONS
        # ================================================================
        print_section("3. Recent Transactions Endpoint")
        result = await test_endpoint(session, "/api/v1/transactions?limit=10", "Transactions")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Raw Response Structure:{Colors.END}")
            print(f"Type: {type(data)}")
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            if isinstance(data, dict) and "transactions" in data:
                transactions = data["transactions"]
                print(f"\n{Colors.CYAN}Transaction Count:{Colors.END} {len(transactions)}")
                
                if transactions:
                    print(f"\n{Colors.CYAN}First Transaction Structure:{Colors.END}")
                    print_json(transactions[0])
                    
                    print(f"\n{Colors.YELLOW}Template Expects These Transaction Fields:{Colors.END}")
                    expected_tx = {
                        "hash": "tx.get('hash', 'Unknown')",
                        "type": "tx.get('element', 'transfer')",
                        "token": "tx.get('tokens', 'UBEC')",
                        "amount": "tx.get('operations', 0)",
                        "timestamp": "tx.get('timestamp', '')"
                    }
                    
                    print(f"\n{Colors.CYAN}Transaction Field Mapping:{Colors.END}")
                    first_tx = transactions[0]
                    for template_field, backend_path in expected_tx.items():
                        backend_field = backend_path.split("'")[1] if "'" in backend_path else "unknown"
                        value = first_tx.get(backend_field, "MISSING")
                        status = f"{Colors.GREEN}✓" if backend_field in first_tx else f"{Colors.RED}✗"
                        print(f"{status} {template_field:15} ← {backend_field:15} = {value}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}No transactions in response{Colors.END}")
        
        # ================================================================
        # 4. DISTRIBUTION STATS
        # ================================================================
        print_section("4. Distribution Stats Endpoint")
        result = await test_endpoint(session, "/api/v1/distribution", "Distribution")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Response Structure:{Colors.END}")
            print_json(data)
        
        # ================================================================
        # 5. ECOREGIONS
        # ================================================================
        print_section("5. Ecoregions Endpoint")
        result = await test_endpoint(session, "/api/v1/ecoregions?limit=3", "Ecoregions")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Response Structure:{Colors.END}")
            print(f"Type: {type(data)}")
            if isinstance(data, list) and data:
                print(f"Count: {len(data)}")
                print(f"\n{Colors.CYAN}First Ecoregion:{Colors.END}")
                print_json(data[0])
            else:
                print(f"{Colors.YELLOW}Empty or unexpected format{Colors.END}")
        
        # ================================================================
        # 6. WATERSHEDS
        # ================================================================
        print_section("6. Watersheds Endpoint")
        result = await test_endpoint(session, "/api/v1/watersheds?limit=3", "Watersheds")
        
        if result.get("success"):
            data = result["data"]
            print(f"\n{Colors.CYAN}Response Structure:{Colors.END}")
            print(f"Type: {type(data)}")
            if isinstance(data, list) and data:
                print(f"Count: {len(data)}")
                print(f"\n{Colors.CYAN}First Watershed:{Colors.END}")
                print_json(data[0])
            else:
                print(f"{Colors.YELLOW}Empty or unexpected format{Colors.END}")
    
    # ================================================================
    # SUMMARY
    # ================================================================
    print_section("Summary & Recommendations")
    
    print(f"{Colors.CYAN}Common Issues to Check:{Colors.END}\n")
    print("1. If Network Overview shows zeros:")
    print("   → Check if backend returns actual data in network-status endpoint")
    print("   → Verify field names match (total_holders, transactions_24h, etc.)")
    print("")
    print("2. If Holonic Scores are empty:")
    print("   → Check if 'summary' key exists in holonic-scores response")
    print("   → Verify summary has average_* fields")
    print("")
    print("3. If Transactions show 'Unknown' and 0.00:")
    print("   → Check if transactions array has actual data")
    print("   → Verify field names (hash, element, tokens, operations)")
    print("")
    print("4. Next steps:")
    print("   → Compare field names from this output with main_web.py")
    print("   → Update field mappings if they don't match")
    print("   → Check backend logs if endpoints return empty data")
    print("")


if __name__ == "__main__":
    asyncio.run(inspect())
