"""Fix directory permissions for file monitoring"""

import os
import sys
import subprocess
from pathlib import Path
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

def check_permissions(directory):
    """Check if directory is readable and writable"""
    path = Path(directory)
    
    if not path.exists():
        return {"exists": False, "readable": False, "writable": False}
    
    readable = os.access(directory, os.R_OK)
    writable = os.access(directory, os.W_OK)
    
    return {"exists": True, "readable": readable, "writable": writable}

def fix_windows_permissions(directory):
    """Fix permissions on Windows using icacls"""
    try:
        # Get current user
        username = os.environ.get('USERNAME', 'Everyone')
        
        # Grant full control to current user
        cmd = f'icacls "{directory}" /grant {username}:(OI)(CI)F /T'
        
        print(f"   Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Permissions fixed for {username}")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def fix_permissions():
    """Check and fix permissions for all configured directories"""
    
    print("Checking and Fixing Directory Permissions")
    print("=" * 70)
    
    if os.name != 'nt':
        print("\n⚠️  This script is designed for Windows.")
        print("   For Linux/Mac, use: chmod -R 755 /path/to/directory")
        return
    
    init_db()
    
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).all()
        
        if not systems:
            print("❌ No systems configured!")
            print("   Run: python add_systems.py")
            return
        
        print(f"\nFound {len(systems)} configured systems\n")
        
        issues = []
        fixed = []
        
        for sys in systems:
            # Load attributes
            _ = (sys.id, sys.name, sys.directory_path)
            session.expunge(sys)
            
            print(f"System: {sys.id}")
            print(f"  Path: {sys.directory_path}")
            
            perms = check_permissions(sys.directory_path)
            
            if not perms["exists"]:
                print(f"  Status: ❌ Directory does not exist")
                print(f"  Action: Create it first with: mkdir {sys.directory_path}")
                issues.append((sys.id, "does not exist"))
            elif not perms["readable"]:
                print(f"  Status: ❌ Not readable")
                print(f"  Action: Fixing permissions...")
                if fix_windows_permissions(sys.directory_path):
                    fixed.append(sys.id)
                else:
                    issues.append((sys.id, "cannot fix permissions"))
            elif not perms["writable"]:
                print(f"  Status: ⚠️  Not writable")
                print(f"  Action: Fixing permissions...")
                if fix_windows_permissions(sys.directory_path):
                    fixed.append(sys.id)
                else:
                    issues.append((sys.id, "cannot fix permissions"))
            else:
                print(f"  Status: ✅ Readable and writable")
            
            print()
    
    # Summary
    print("=" * 70)
    print("\nSummary:")
    print(f"  Total systems: {len(systems)}")
    print(f"  Fixed: {len(fixed)}")
    print(f"  Issues remaining: {len(issues)}")
    
    if fixed:
        print(f"\n✅ Fixed permissions for:")
        for sys_id in fixed:
            print(f"  - {sys_id}")
    
    if issues:
        print(f"\n⚠️  Issues remaining:")
        for sys_id, issue in issues:
            print(f"  - {sys_id}: {issue}")
        
        print("\n📋 Manual Steps Required:")
        print("\n1. For directories that don't exist:")
        print("   mkdir <directory_path>")
        
        print("\n2. If permission fixes failed, run as Administrator:")
        print("   - Right-click Command Prompt")
        print("   - Select 'Run as administrator'")
        print("   - Run: python fix_permissions.py")
        
        print("\n3. Or manually fix permissions:")
        print("   - Right-click directory → Properties")
        print("   - Security tab → Edit")
        print("   - Add your user with Full Control")
    else:
        print("\n✅ All directories have correct permissions!")
        print("\nNext steps:")
        print("  1. Verify: python verify_configuration.py")
        print("  2. Start monitoring: python start_monitoring.py")
    
    print("\n" + "=" * 70)

def show_manual_instructions():
    """Show manual instructions for fixing permissions"""
    
    print("\n" + "=" * 70)
    print("MANUAL PERMISSION FIX INSTRUCTIONS")
    print("=" * 70)
    
    print("\nMethod 1: Using File Explorer (GUI)")
    print("-" * 40)
    print("1. Right-click the directory")
    print("2. Select 'Properties'")
    print("3. Go to 'Security' tab")
    print("4. Click 'Edit' button")
    print("5. Click 'Add' to add your user")
    print("6. Enter your username and click 'Check Names'")
    print("7. Click 'OK'")
    print("8. Select your user and check 'Full Control'")
    print("9. Click 'Apply' and 'OK'")
    
    print("\nMethod 2: Using Command Prompt (as Administrator)")
    print("-" * 40)
    print("1. Open Command Prompt as Administrator")
    print("2. Run this command for each directory:")
    print("   icacls \"C:\\data\\your_directory\" /grant %USERNAME%:(OI)(CI)F /T")
    print("\nExample:")
    print("   icacls \"C:\\data\\test1\" /grant %USERNAME%:(OI)(CI)F /T")
    
    print("\nMethod 3: Using PowerShell (as Administrator)")
    print("-" * 40)
    print("1. Open PowerShell as Administrator")
    print("2. Run this command for each directory:")
    print("   $acl = Get-Acl \"C:\\data\\your_directory\"")
    print("   $permission = \"$env:USERNAME\",\"FullControl\",\"ContainerInherit,ObjectInherit\",\"None\",\"Allow\"")
    print("   $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission")
    print("   $acl.SetAccessRule($accessRule)")
    print("   Set-Acl \"C:\\data\\your_directory\" $acl")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_manual_instructions()
    else:
        fix_permissions()
        
        print("\n💡 Tip: For manual instructions, run:")
        print("   python fix_permissions.py --help")
