#!/usr/bin/env python3
"""
Test Script for Bioregion API Client Integration

Tests the integration between the frontend BackendAPIClient and the backend
bioregion API endpoints to verify real data is being fetched correctly.

Attribution: This project uses the services of Claude and Anthropic PBC to 
inform our decisions and recommendations. This project was made possible with 
the assistance of Claude and Anthropic PBC.

Usage:
    python test_bioregion_client.py

Requirements:
    - Backend API server must be running on http://localhost:8000
    - backend_api.py must be in the same directory or PYTHONPATH
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import backend_api
sys.path.insert(0, str(Path(__file__).parent))

from backend_api import BackendAPIClient


async def test_bioregion_integration():
    """Test all bioregion client methods."""
    
    # Initialize client
    client = BackendAPIClient(
        base_url="http://localhost:8000",
        api_key=None  # No auth required for read-only
    )
    
    print("=" * 70)
    print("UBEC Bioregion API Client Integration Test")
    print("=" * 70)
    print()
    
    success = True
    
    try:
        # Test 1: Get bioregion count
        print("Test 1: get_bioregion_count()")
        print("-" * 70)
        try:
            count = await client.get_bioregion_count()
            print(f"✓ Bioregion count: {count}")
            if count == 0:
                print("  ⚠️  Warning: No bioregions found in database")
                print("  → Consider loading sample data (see integration guide)")
            print()
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
            print()
        
        # Test 2: Get all bioregions
        print("Test 2: get_bioregions()")
        print("-" * 70)
        try:
            bioregions_data = await client.get_bioregions()
            count = bioregions_data.get('count', 0)
            print(f"✓ Received {count} bioregions")
            
            summary = bioregions_data.get('summary', {})
            if summary:
                print(f"✓ Total members: {summary.get('total_members', 0)}")
                print(f"✓ Average size: {summary.get('average_size', 0):.1f}")
                print(f"✓ Average autonomy: {summary.get('average_autonomy', 0):.2f}")
                print(f"✓ Average integration: {summary.get('average_integration', 0):.2f}")
            
            bioregions = bioregions_data.get('bioregions', [])
            if bioregions:
                print(f"✓ First bioregion: {bioregions[0].get('name', 'Unknown')}")
            print()
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
            print()
        
        # Test 3: Get specific bioregion (if any exist)
        print("Test 3: get_bioregion(bioregion_id)")
        print("-" * 70)
        try:
            bioregions_data = await client.get_bioregions()
            bioregions = bioregions_data.get('bioregions', [])
            
            if bioregions:
                bioregion_id = bioregions[0]['id']
                bioregion = await client.get_bioregion(bioregion_id)
                print(f"✓ Successfully fetched bioregion ID: {bioregion_id}")
                print(f"✓ Name: {bioregion.get('name', 'Unknown')}")
                print(f"✓ Members: {bioregion.get('member_count', 0)}")
                print(f"✓ Autonomy score: {bioregion.get('autonomy_score', 0):.2f}")
                print(f"✓ Integration score: {bioregion.get('integration_score', 0):.2f}")
                print(f"✓ Health rating: {bioregion.get('health_rating', 'unknown')}")
            else:
                print("⚠️  No bioregions available to test individual fetch")
            print()
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
            print()
        
        # Test 4: Get network status with real bioregion count
        print("Test 4: get_network_status() - Enhanced with real count")
        print("-" * 70)
        try:
            status = await client.get_network_status()
            print(f"✓ Active participants: {status.get('active_participants', 0)}")
            print(f"✓ Bioregions count: {status.get('bioregions_count', 0)}")
            print(f"✓ Average Ubuntu score: {status.get('average_ubuntu_score', 0):.2f}")
            print(f"✓ Network health: {status.get('network_health', 'unknown')}")
            
            data_source = status.get('data_source', 'unknown')
            print(f"✓ Data source: {data_source}")
            
            if data_source == 'real':
                print()
                print("🎉 SUCCESS: Using REAL bioregion data from backend!")
            elif data_source == 'mock':
                print()
                print("⚠️  WARNING: Still using MOCK data")
                print("   → Check backend API connectivity")
                print("   → Verify bioregion_manager service is running")
                success = False
            else:
                print()
                print("⚠️  WARNING: Unknown data source")
                success = False
            print()
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
            print()
        
        # Final summary
        print("=" * 70)
        if success:
            print("✅ ALL TESTS PASSED - Integration working correctly!")
            print()
            print("Next steps:")
            print("  1. Update your dashboard to use these client methods")
            print("  2. Deploy to production")
            print("  3. Monitor using the health endpoints")
        else:
            print("❌ SOME TESTS FAILED - See errors above")
            print()
            print("Troubleshooting:")
            print("  1. Verify backend API server is running: http://localhost:8000/health")
            print("  2. Check if bioregion_manager service is initialized")
            print("  3. Verify database has bioregion data")
            print("  4. Review API logs for errors")
            print()
            print("See BIOREGION_DASHBOARD_INTEGRATION_COMPLETE.md for detailed help")
        print("=" * 70)
        
        return 0 if success else 1
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ FATAL ERROR: {e}")
        print("=" * 70)
        print()
        print("Troubleshooting:")
        print("  1. Is the backend API server running?")
        print("     → Start with: python main.py serve --host 0.0.0.0 --port 8000")
        print()
        print("  2. Can you reach the API?")
        print("     → Test with: curl http://localhost:8000/health")
        print()
        print("  3. Is backend_api.py in the correct location?")
        print("     → Should be in same directory as this test script")
        print()
        
        import traceback
        print("Full error traceback:")
        traceback.print_exc()
        
        return 1
    
    finally:
        await client.close()


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(test_bioregion_integration())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
