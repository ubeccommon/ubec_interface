#!/usr/bin/env python3
"""
Dashboard Data Diagnostic Tool
===============================

Diagnoses data mapping issues between backend API and frontend dashboard.

This tool:
1. Calls backend API endpoints directly
2. Shows the actual data structure returned
3. Compares with what the dashboard template expects
4. Identifies mismatches and missing fields

Usage:
    python3 diagnose_dashboard_data.py

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime


class DashboardDiagnostic:
    """Diagnose dashboard data issues"""
    
    def __init__(self, backend_url: str = "http://92.205.230.245:8000"):
        self.backend_url = backend_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{'='*80}")
        print(f"  {text}")
        print(f"{'='*80}\n")
    
    def print_section(self, text: str):
        """Print a formatted section"""
        print(f"\n{'-'*80}")
        print(f"  {text}")
        print(f"{'-'*80}\n")
    
    async def get_endpoint(self, path: str) -> Dict[str, Any]:
        """Get data from backend endpoint"""
        url = f"{self.backend_url}{path}"
        print(f"📡 Calling: {url}")
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Success (Status: {response.status})")
                    return {"success": True, "data": data, "status": response.status}
                else:
                    text = await response.text()
                    print(f"❌ Failed (Status: {response.status})")
                    print(f"   Response: {text[:200]}")
                    return {"success": False, "error": text, "status": response.status}
        except asyncio.TimeoutError:
            print(f"⏱️  Timeout after 10 seconds")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    async def diagnose_network_status(self):
        """Diagnose network status endpoint"""
        self.print_section("Network Status Data")
        
        result = await self.get_endpoint("/api/v1/network/status")
        
        if result["success"]:
            data = result["data"]
            print("📊 Returned fields:")
            for key, value in data.items():
                print(f"   • {key}: {value} ({type(value).__name__})")
            
            # Check expected fields
            print("\n🔍 Dashboard template expects:")
            expected_fields = [
                "active_participants",
                "total_transactions_24h",
                "bioregions_count",
                "average_ubuntu_score"
            ]
            
            for field in expected_fields:
                if field in data:
                    print(f"   ✅ {field}: {data[field]}")
                else:
                    print(f"   ❌ MISSING: {field}")
            
            self.results["network_status"] = result
        else:
            print(f"❌ Failed to fetch network status: {result.get('error')}")
            self.results["network_status"] = result
    
    async def diagnose_recent_transactions(self):
        """Diagnose recent transactions endpoint"""
        self.print_section("Recent Transactions Data")
        
        result = await self.get_endpoint("/api/v1/transactions/recent?limit=5")
        
        if result["success"]:
            data = result["data"]
            print(f"📊 Response structure: {list(data.keys())}")
            
            if "transactions" in data:
                transactions = data["transactions"]
                print(f"\n📝 Number of transactions: {len(transactions)}")
                
                if transactions:
                    print("\n🔍 First transaction structure:")
                    tx = transactions[0]
                    for key, value in tx.items():
                        print(f"   • {key}: {value} ({type(value).__name__})")
                    
                    print("\n🔍 Dashboard template expects for each transaction:")
                    expected_fields = {
                        "hash": "Transaction hash",
                        "element": "Transaction type (maps to 'type')",
                        "tokens": "Token type (maps to 'token')",
                        "operations": "Amount (maps to 'amount')",
                        "timestamp": "Timestamp"
                    }
                    
                    for field, desc in expected_fields.items():
                        if field in tx:
                            val = tx[field]
                            print(f"   ✅ {field}: {val} - {desc}")
                        else:
                            print(f"   ❌ MISSING: {field} - {desc}")
                    
                    # Check for zero amounts
                    if "operations" in tx and tx["operations"] == 0:
                        print(f"\n⚠️  WARNING: 'operations' field is 0!")
                        print(f"   This will show as 0.00 in the dashboard")
                else:
                    print("⚠️  No transactions returned")
            else:
                print("❌ 'transactions' key not in response")
            
            self.results["transactions"] = result
        else:
            print(f"❌ Failed to fetch transactions: {result.get('error')}")
            self.results["transactions"] = result
    
    async def diagnose_watersheds(self):
        """Diagnose watersheds endpoint"""
        self.print_section("Watersheds Data")
        
        result = await self.get_endpoint("/api/v1/watersheds?limit=5")
        
        if result["success"]:
            data = result["data"]
            print(f"📊 Response structure: {list(data.keys())}")
            
            if "watersheds" in data:
                watersheds = data["watersheds"]
                print(f"\n📝 Number of watersheds: {len(watersheds)}")
                
                if watersheds:
                    print("\n🔍 First watershed structure:")
                    ws = watersheds[0]
                    for key, value in ws.items():
                        # Skip geometry field as it's too long
                        if key != "geometry":
                            print(f"   • {key}: {value} ({type(value).__name__})")
                        else:
                            print(f"   • {key}: [geometry data] ({type(value).__name__})")
                    
                    print("\n🔍 Dashboard template expects:")
                    expected_fields = {
                        "feow_id": "Watershed ID",
                        "name": "Watershed name",
                        "area_sqkm": "Area in square kilometers"
                    }
                    
                    for field, desc in expected_fields.items():
                        if field in ws:
                            val = ws[field]
                            if field == "area_sqkm":
                                print(f"   ✅ {field}: {val} km² - {desc}")
                            else:
                                print(f"   ✅ {field}: {val} - {desc}")
                        else:
                            print(f"   ❌ MISSING: {field} - {desc}")
                    
                    # Check for zero or missing area
                    if "area_sqkm" in ws:
                        if ws["area_sqkm"] == 0 or ws["area_sqkm"] is None:
                            print(f"\n⚠️  WARNING: area_sqkm is {ws['area_sqkm']}!")
                    
                    # Check for generic names
                    if "name" in ws:
                        if "Watershed #" in str(ws["name"]):
                            print(f"\n⚠️  WARNING: Generic watershed name detected!")
                else:
                    print("⚠️  No watersheds returned")
            else:
                print("❌ 'watersheds' key not in response")
            
            self.results["watersheds"] = result
        else:
            print(f"❌ Failed to fetch watersheds: {result.get('error')}")
            self.results["watersheds"] = result
    
    async def diagnose_ecoregions(self):
        """Diagnose ecoregions endpoint"""
        self.print_section("Ecoregions Data")
        
        result = await self.get_endpoint("/api/v1/ecoregions?limit=5")
        
        if result["success"]:
            data = result["data"]
            print(f"📊 Response structure: {list(data.keys())}")
            
            if "ecoregions" in data:
                ecoregions = data["ecoregions"]
                print(f"\n📝 Number of ecoregions: {len(ecoregions)}")
                
                if ecoregions:
                    print("\n🔍 First ecoregion structure:")
                    eco = ecoregions[0]
                    for key, value in eco.items():
                        if key != "geometry":
                            print(f"   • {key}: {value} ({type(value).__name__})")
                        else:
                            print(f"   • {key}: [geometry data] ({type(value).__name__})")
                    
                    print("\n🔍 Dashboard template expects:")
                    expected_fields = {
                        "eco_id": "Ecoregion ID",
                        "name": "Ecoregion name",
                        "biome": "Biome type",
                        "realm": "Biogeographic realm"
                    }
                    
                    for field, desc in expected_fields.items():
                        if field in eco:
                            print(f"   ✅ {field}: {eco[field]} - {desc}")
                        else:
                            print(f"   ❌ MISSING: {field} - {desc}")
                else:
                    print("⚠️  No ecoregions returned")
            else:
                print("❌ 'ecoregions' key not in response")
            
            self.results["ecoregions"] = result
        else:
            print(f"❌ Failed to fetch ecoregions: {result.get('error')}")
            self.results["ecoregions"] = result
    
    async def diagnose_holonic_scores(self):
        """Diagnose holonic scores endpoint"""
        self.print_section("Holonic Scores Data")
        
        result = await self.get_endpoint("/api/v1/holonic/scores?limit=5")
        
        if result["success"]:
            data = result["data"]
            print(f"📊 Response structure: {list(data.keys())}")
            
            # Check for evaluations or summary
            if "evaluations" in data:
                evals = data["evaluations"]
                print(f"\n📝 Number of evaluations: {len(evals)}")
                
                if evals:
                    print("\n🔍 First evaluation structure:")
                    eval_data = evals[0]
                    for key, value in eval_data.items():
                        print(f"   • {key}: {value} ({type(value).__name__})")
            
            if "summary" in data:
                print("\n📊 Summary statistics:")
                summary = data["summary"]
                for key, value in summary.items():
                    print(f"   • {key}: {value}")
            
            self.results["holonic_scores"] = result
        else:
            print(f"❌ Failed to fetch holonic scores: {result.get('error')}")
            self.results["holonic_scores"] = result
    
    def print_summary(self):
        """Print diagnostic summary"""
        self.print_header("DIAGNOSTIC SUMMARY")
        
        print("Endpoint Status:")
        for endpoint, result in self.results.items():
            status = "✅" if result.get("success") else "❌"
            print(f"  {status} {endpoint}")
        
        print("\n🔍 Key Findings:\n")
        
        # Check transactions
        if "transactions" in self.results and self.results["transactions"].get("success"):
            tx_data = self.results["transactions"]["data"]
            if "transactions" in tx_data and tx_data["transactions"]:
                tx = tx_data["transactions"][0]
                if tx.get("operations", 0) == 0:
                    print("  ⚠️  ISSUE: Transaction 'operations' field is 0")
                    print("     → This causes 0.00 amounts in dashboard")
                    print("     → Check if real transaction data exists in database\n")
        
        # Check watersheds
        if "watersheds" in self.results and self.results["watersheds"].get("success"):
            ws_data = self.results["watersheds"]["data"]
            if "watersheds" in ws_data and ws_data["watersheds"]:
                ws = ws_data["watersheds"][0]
                if "area_sqkm" not in ws or ws.get("area_sqkm") == 0:
                    print("  ⚠️  ISSUE: Watershed 'area_sqkm' missing or zero")
                    print("     → This causes 0 km² display in dashboard")
                    print("     → Check bioregion manager calculations\n")
                
                if "name" not in ws or "Watershed #" in str(ws.get("name", "")):
                    print("  ⚠️  ISSUE: Watershed 'name' missing or generic")
                    print("     → This causes 'Watershed #' display")
                    print("     → Check feow_basins table has proper names\n")
        
        print("\n📋 Recommendations:\n")
        print("  1. Run backend API verification: python3 verify_deployment.py")
        print("  2. Check database has actual transaction data")
        print("  3. Verify feow_basins table has populated name and area_sqkm fields")
        print("  4. Check bioregion manager is calculating areas correctly")
        print("  5. Review data transformation in main_web.py dashboard route")


async def main():
    """Run diagnostic"""
    print("\n" + "="*80)
    print("  UBEC Dashboard Data Diagnostic Tool")
    print("  " + "-"*76)
    print("  Analyzing backend API data structure and dashboard expectations")
    print("="*80)
    
    async with DashboardDiagnostic() as diagnostic:
        await diagnostic.diagnose_network_status()
        await diagnostic.diagnose_recent_transactions()
        await diagnostic.diagnose_watersheds()
        await diagnostic.diagnose_ecoregions()
        await diagnostic.diagnose_holonic_scores()
        
        diagnostic.print_summary()
    
    print("\n" + "="*80)
    print("  Diagnostic complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
