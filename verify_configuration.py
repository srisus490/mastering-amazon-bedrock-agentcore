"""Verify source systems configuration"""

import os
from pathlib import Path
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, SLADefinitionModel

def verify_configuration():
    """Verify that all configured systems are ready for monitoring"""
    
    print("Verifying Source Systems Configuration")
    print("=" * 70)
    
    init_db()
    
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).all()
        
        if not systems:
            print("❌ No systems configured!")
            print("   Run: python add_systems.py")
            return
        
        print(f"\nFound {len(systems)} configured systems\n")
        
        issues = []
        active_count = 0
        
        for sys in systems:
            # Load all attributes before expunging
            _ = (sys.id, sys.name, sys.directory_path, sys.is_active)
            session.expunge(sys)
            
            print(f"System: {sys.id}")
            print(f"  Name: {sys.name}")
            print(f"  Path: {sys.directory_path}")
            print(f"  Active: {'✅ Yes' if sys.is_active else '⚠️  No (disabled)'}")
            
            # Check if directory exists
            path = Path(sys.directory_path)
            if path.exists():
                print(f"  Directory: ✅ Exists")
                
                # Check if writable
                if os.access(sys.directory_path, os.W_OK):
                    print(f"  Permissions: ✅ Writable")
                else:
                    print(f"  Permissions: ⚠️  Not writable")
                    issues.append(f"{sys.id}: Directory not writable - {sys.directory_path}")
            else:
                print(f"  Directory: ❌ Does not exist")
                issues.append(f"{sys.id}: Directory does not exist - {sys.directory_path}")
            
            # Check SLA definition
            sla = session.query(SLADefinitionModel).filter_by(
                source_system_id=sys.id
            ).first()
            
            if sla:
                _ = (sla.expected_arrival_time, sla.expected_arrival_window_minutes, 
                     sla.minimum_files_per_day)
                session.expunge(sla)
                
                print(f"  SLA: ✅ Configured")
                print(f"    Expected: {sla.expected_arrival_time} ±{sla.expected_arrival_window_minutes}min")
                print(f"    Min files/day: {sla.minimum_files_per_day}")
            else:
                print(f"  SLA: ❌ Not configured")
                issues.append(f"{sys.id}: No SLA definition")
            
            if sys.is_active:
                active_count += 1
            
            print()
    
    # Summary
    print("=" * 70)
    print("\nSummary:")
    print(f"  Total systems: {len(systems)}")
    print(f"  Active systems: {active_count}")
    print(f"  Inactive systems: {len(systems) - active_count}")
    
    if issues:
        print(f"\n⚠️  Issues found ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRecommendations:")
        print("  1. Create missing directories:")
        for issue in issues:
            if "does not exist" in issue:
                path = issue.split(" - ")[1] if " - " in issue else ""
                if path:
                    if os.name == 'nt':  # Windows
                        print(f"     mkdir {path}")
                    else:  # Linux/Mac
                        print(f"     mkdir -p {path}")
        
        print("\n  2. Fix permissions for non-writable directories:")
        print("     python fix_permissions.py")
        print("     OR run as Administrator:")
        for issue in issues:
            if "not writable" in issue:
                path = issue.split(" - ")[1] if " - " in issue else ""
                if path and os.name == 'nt':
                    print(f'     icacls "{path}" /grant %USERNAME%:(OI)(CI)F /T')
        
        print("\n  3. See detailed guide:")
        print("     PERMISSIONS_GUIDE.md")
        
        print("\n  4. Re-run this script to verify")
        print("     python verify_configuration.py")
    else:
        print("\n✅ All systems configured correctly!")
        print("\nNext steps:")
        print("  1. Start monitoring: python start_monitoring.py")
        print("  2. Start API server: python run_api.py")
        print("  3. View API docs: http://localhost:8000/docs")
        print("  4. Test AI features: python test_ai.py")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    verify_configuration()
