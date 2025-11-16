#!/usr/bin/env python3
"""
Backend API Diagnostic Script
==============================

Tests what the backend is actually returning for tokens and holonic scores.

Usage:
    python3 backend_diagnostic.py
"""

import asyncio
import aiohttp
import json
from pprint import pprint

BACKEND_URL = "http://92.205.230.245:8000"

async def test_endpoints():
    """Test backend API endpoints and show actual responses."""
    
    print("=" * 70)
    print("UBEC Backend API Diagnostic")
    print("=" * 70)
    print(f"\nBackend URL: {BACKEND_URL}\n")
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("\n" + "=" * 70)
        print("TEST 1: Health Check")
        print("=" * 70)
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/health") as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response:")
                pprint(data)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: All tokens
        print("\n" + "=" * 70)
        print("TEST 2: Get All Tokens (/api/v1/tokens)")
        print("=" * 70)
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/tokens") as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, list):
                    print(f"Number of tokens: {len(data)}")
                    if data:
                        print(f"\nFirst token structure:")
                        pprint(data[0])
                        print(f"\nKeys in first token:")
                        print(list(data[0].keys()))
                else:
                    print(f"Response:")
                    pprint(data)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Network status
        print("\n" + "=" * 70)
        print("TEST 3: Network Status (/api/v1/network-status)")
        print("=" * 70)
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/network-status") as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response:")
                pprint(data)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Holonic scores
        print("\n" + "=" * 70)
        print("TEST 4: Holonic Scores (/api/v1/holonic-scores?limit=5)")
        print("=" * 70)
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/holonic-scores?limit=5") as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys in response: {list(data.keys())}")
                    if 'scores' in data:
                        scores = data['scores']
                        print(f"Number of scores: {len(scores)}")
                        if scores:
                            print(f"\nFirst score structure:")
                            pprint(scores[0])
                    else:
                        print(f"Full response:")
                        pprint(data)
                else:
                    print(f"Response:")
                    pprint(data)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Individual token
        print("\n" + "=" * 70)
        print("TEST 5: Individual Token (/api/v1/tokens/UBEC)")
        print("=" * 70)
        try:
            async with session.get(f"{BACKEND_URL}/api/v1/tokens/UBEC") as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response:")
                pprint(data)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Diagnostic Complete")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check if token keys match template expectations")
    print("  2. Check if holonic_scores keys match template expectations")
    print("  3. Verify data transformation in main_web.py")
    print("")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
