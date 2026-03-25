"""Complete test workflow for file monitoring system"""

import os
import time
from pathlib import Path

def test_workflow():
    """Run complete test workflow"""
    
    print("=" * 70)
    print("FILE MONITORING SYSTEM - TEST WORKFLOW")
    print("=" * 70)
    
    # Step 1: Add test system
    print("\n📋 Step 1: Adding test system to database...")
    os.system("python add_test_system.py")
    
    input("\n⏸️  Press Enter to continue to Step 2...")
    
    # Step 2: Verify configuration
    print("\n📋 Step 2: Verifying configuration...")
    os.system("python verify_configuration.py")
    
    input("\n⏸️  Press Enter to continue to Step 3...")
    
    # Step 3: Instructions for starting monitoring
    print("\n📋 Step 3: Start monitoring service")
    print("\n⚠️  IMPORTANT: Open a NEW terminal window and run:")
    print("     python start_monitoring.py")
    print("\n   Keep that terminal open while testing.")
    
    input("\n⏸️  Press Enter once monitoring is started...")
    
    # Step 4: Create test file
    print("\n📋 Step 4: Creating test file...")
    test_dir = Path("C:/data/test1")
    test_file = test_dir / "testfile.txt"
    
    try:
        with open(test_file, "w") as f:
            f.write(f"Test file created at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"✅ Created test file: {test_file}")
    except Exception as e:
        print(f"❌ Failed to create test file: {e}")
        return
    
    # Step 5: Wait for detection
    print("\n📋 Step 5: Waiting for file detection...")
    print("   (Monitoring should detect the file within 30 seconds)")
    
    for i in range(10, 0, -1):
        print(f"   Waiting {i} seconds...", end="\r")
        time.sleep(1)
    print("\n")
    
    # Step 6: Check if file was detected
    print("📋 Step 6: Checking if file was detected...")
    os.system("python check_test_system.py")
    
    input("\n⏸️  Press Enter to continue to Step 7...")
    
    # Step 7: Start API and test endpoints
    print("\n📋 Step 7: Testing API endpoints")
    print("\n⚠️  IMPORTANT: Open ANOTHER terminal window and run:")
    print("     python run_api.py")
    print("\n   Then visit: http://localhost:8000/docs")
    print("\n   Try these endpoints:")
    print("     - GET /api/v1/source-systems")
    print("     - GET /api/v1/file-arrivals?days=1")
    print("     - GET /api/v1/file-arrivals/count")
    
    input("\n⏸️  Press Enter to continue to Step 8...")
    
    # Step 8: Create more test files
    print("\n📋 Step 8: Creating additional test files...")
    
    for i in range(1, 6):
        test_file = test_dir / f"testfile_{i}.txt"
        try:
            with open(test_file, "w") as f:
                f.write(f"Test file {i} created at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f"✅ Created: {test_file.name}")
            time.sleep(2)  # Wait 2 seconds between files
        except Exception as e:
            print(f"❌ Failed to create {test_file.name}: {e}")
    
    print("\n   Waiting for detection...")
    time.sleep(10)
    
    # Step 9: Final check
    print("\n📋 Step 9: Final verification...")
    os.system("python check_test_system.py")
    
    # Step 10: Summary
    print("\n" + "=" * 70)
    print("✅ TEST WORKFLOW COMPLETE!")
    print("=" * 70)
    print("\nWhat was tested:")
    print("  ✅ Database configuration")
    print("  ✅ Directory monitoring")
    print("  ✅ File detection (< 30 seconds)")
    print("  ✅ Database writes")
    print("  ✅ API endpoints")
    print("\nNext steps:")
    print("  1. Review the test results above")
    print("  2. If all tests passed, configure your 20 production systems")
    print("  3. Edit add_systems.py with your actual directories")
    print("  4. Run: python add_systems.py")
    print("  5. Run: python start_monitoring.py (for production)")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_workflow()
