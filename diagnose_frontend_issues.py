#!/usr/bin/env python3
"""
Frontend Data Diagnostic Tool
==============================

Checks what data the backend is actually returning to identify
frontend display issues.

Usage:
    python3 diagnose_frontend_issues.py
"""

import asyncio
import json
from pathlib import Path
import sys

# Add app directory to path
sys.path.insert(0, '/srv/ubec-www/app')

from utils.backend_client import BackendAPIClient


async def diagnose():
    """Run comprehensive diagnostics."""
    print("=" * 70)
    print("UBEC Frontend Data Diagnostic")
    print("=" * 70)
    print()
    
    client = BackendAPIClient()
    
    try:
        # Test 1: Tokens data
        print("[1/4] Checking Tokens Data")
        print("-" * 70)
        tokens = await client.get_all_tokens()
        
        if not tokens:
            print("❌ ERROR: No tokens returned!")
        else:
            print(f"✓ Retrieved {len(tokens)} tokens\n")
            
            for i, token in enumerate(tokens, 1):
                print(f"Token {i}:")
                print(f"  Name: {token.get('name', 'MISSING')}")
                print(f"  Element: {token.get('element', 'MISSING')}")
                print(f"  Asset Code: {token.get('asset_code', 'MISSING')}")
                print(f"  Total Supply: {token.get('total_supply', 'MISSING'):,}")
                print(f"  Has Description: {'description' in token}")
                print(f"  Has Ubuntu Principle: {'ubuntu_principle' in token}")
                
                # Check for frontend template field
                if token.get('name') == 'MISSING' or not token.get('name'):
                    print(f"  ⚠️ WARNING: 'name' field missing or empty!")
                
                if token.get('total_supply', 0) == 0:
                    print(f"  ⚠️ WARNING: Total supply is 0!")
                
                print()
        
        # Test 2: Network Status
        print("\n[2/4] Checking Network Status")
        print("-" * 70)
        network = await client.get_network_status()
        
        print(f"Total Supply: {network.get('total_supply', 'MISSING'):,}")
        print(f"Total Holders: {network.get('total_holders', 'MISSING')}")
        print(f"Bioregion Count: {network.get('bioregion_count', 'MISSING')}")
        print(f"Health Score: {network.get('health_score', 'MISSING')}")
        
        if network.get('health_score', 0) == 0:
            print("⚠️ WARNING: Health score is 0 - may display as 'Unhealthy'")
        
        # Test 3: Holonic Scores
        print("\n[3/4] Checking Holonic Scores")
        print("-" * 70)
        holonic = await client.get_holonic_scores(limit=1)
        
        summary = holonic.get('summary', {})
        print(f"Average Score: {summary.get('average_score', 'MISSING')}")
        print(f"Has reciprocity_health: {'average_reciprocity' in summary}")
        print(f"Has mutualism_capacity: {'average_mutualism' in summary}")
        
        if summary.get('average_score', 0) == 0:
            print("⚠️ WARNING: All holonic metrics will show as 0%")
        
        # Test 4: Check for template data structure
        print("\n[4/4] Checking Data Structure for Templates")
        print("-" * 70)
        
        # Create sample template context
        template_context = {
            'tokens': tokens,
            'network_status': network,
            'holonic_summary': summary
        }
        
        print("Sample template context structure:")
        print(json.dumps({
            'tokens_count': len(tokens),
            'first_token_keys': list(tokens[0].keys()) if tokens else [],
            'network_keys': list(network.keys()),
            'holonic_summary_keys': list(summary.keys())
        }, indent=2))
        
        # Check for common template issues
        print("\n" + "=" * 70)
        print("FRONTEND TEMPLATE CHECKLIST")
        print("=" * 70)
        
        issues = []
        
        # Issue 1: Token names
        if tokens:
            if not tokens[0].get('name'):
                issues.append("❌ Token 'name' field is missing or empty")
            else:
                print("✓ Token 'name' field exists")
        
        # Issue 2: Zero supplies
        zero_supply_tokens = [t for t in tokens if t.get('total_supply', 0) == 0]
        if zero_supply_tokens:
            issues.append(f"⚠️ {len(zero_supply_tokens)} tokens have zero supply")
        else:
            print("✓ All tokens have non-zero supply")
        
        # Issue 3: Health score
        if network.get('health_score', 0) == 0:
            issues.append("⚠️ Health score is 0 (will show as 'Unhealthy')")
        else:
            print("✓ Network has non-zero health score")
        
        # Issue 4: Holonic metrics
        if summary.get('average_score', 0) == 0:
            issues.append("ℹ️ Holonic metrics are 0 (may be expected if no activity)")
        else:
            print("✓ Holonic metrics have non-zero values")
        
        if issues:
            print("\nISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
        
        print("\n" + "=" * 70)
        print("RECOMMENDED TEMPLATE FIXES")
        print("=" * 70)
        
        print("""
For token names showing "Unknown":
  
  BAD:  <h3>Unknown {{ token.element }}</h3>
  GOOD: <h3>{{ token.name }}</h3>

For zero supply tokens:
  Check backend database - tokens should have non-zero supply

For "Unhealthy" network status:
  Check frontend logic for health score calculation
  Current health_score: {health}
  
For 0% holonic metrics:
  This may be expected if there's no network activity yet
        """.format(health=network.get('health_score', 0)))
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(diagnose())
