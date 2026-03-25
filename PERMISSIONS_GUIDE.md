# Directory Permissions Guide

Guide to fixing directory permission issues on Windows.

## Quick Fix

```bash
# Run the automated fix script
python fix_permissions.py
```

If that doesn't work, run as Administrator:
1. Right-click Command Prompt
2. Select "Run as administrator"
3. Run: `python fix_permissions.py`

---

## Understanding the Issue

The file monitoring system needs to:
- **Read** directories to detect new files
- **Write** to directories to test access (optional)
- **List** directory contents

If permissions are incorrect, the monitoring service cannot detect files.

---

## Automated Fix

### Step 1: Run the Fix Script

```bash
python fix_permissions.py
```

This will:
1. Check all configured directories
2. Identify permission issues
3. Attempt to fix them automatically
4. Report results

### Step 2: Review Results

**If successful:**
```
✅ Fixed permissions for:
  - TEST001
  - PROD_SALES
```

**If issues remain:**
```
⚠️  Issues remaining:
  - PROD_INVENTORY: cannot fix permissions
```

Follow the manual steps below.

---

## Manual Fix Methods

### Method 1: File Explorer (Easiest)

1. **Navigate to the directory**
   - Open File Explorer
   - Go to `C:\data\test1` (or your directory)

2. **Open Properties**
   - Right-click the directory
   - Select "Properties"

3. **Edit Security Settings**
   - Click "Security" tab
   - Click "Edit" button

4. **Add Your User**
   - Click "Add"
   - Type your username
   - Click "Check Names"
   - Click "OK"

5. **Grant Full Control**
   - Select your username
   - Check "Full Control"
   - Click "Apply"
   - Click "OK"

### Method 2: Command Prompt (Fast)

**Run as Administrator:**

```cmd
# For a single directory
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T

# For multiple directories
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T
icacls "C:\data\sales" /grant %USERNAME%:(OI)(CI)F /T
icacls "C:\data\inventory" /grant %USERNAME%:(OI)(CI)F /T
```

**Explanation:**
- `icacls` - Windows permission tool
- `/grant` - Grant permissions
- `%USERNAME%` - Your current user
- `(OI)(CI)` - Object Inherit, Container Inherit
- `F` - Full Control
- `/T` - Apply to all subdirectories

### Method 3: PowerShell (Advanced)

**Run as Administrator:**

```powershell
# Single directory
$path = "C:\data\test1"
$acl = Get-Acl $path
$permission = "$env:USERNAME","FullControl","ContainerInherit,ObjectInherit","None","Allow"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($accessRule)
Set-Acl $path $acl

# Multiple directories
$directories = @("C:\data\test1", "C:\data\sales", "C:\data\inventory")
foreach ($dir in $directories) {
    $acl = Get-Acl $dir
    $permission = "$env:USERNAME","FullControl","ContainerInherit,ObjectInherit","None","Allow"
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
    $acl.SetAccessRule($accessRule)
    Set-Acl $dir $acl
    Write-Host "Fixed: $dir"
}
```

---

## Common Issues

### Issue 1: "Access Denied"

**Cause:** You don't have permission to change permissions.

**Solution:** Run Command Prompt as Administrator
1. Search for "cmd" in Start Menu
2. Right-click "Command Prompt"
3. Select "Run as administrator"
4. Run the fix command

### Issue 2: "Directory does not exist"

**Cause:** Directory hasn't been created yet.

**Solution:** Create the directory first
```cmd
mkdir C:\data\test1
```

Then fix permissions:
```cmd
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T
```

### Issue 3: "Network drive permissions"

**Cause:** Directory is on a network drive with different permissions.

**Solution:** 
1. Contact your network administrator
2. Or map the network drive with proper credentials
3. Or use a local directory instead

### Issue 4: "OneDrive/Dropbox folder"

**Cause:** Cloud sync folders have special permissions.

**Solution:**
1. Use a local folder instead (recommended)
2. Or ensure cloud sync service has proper permissions
3. Or disable cloud sync for monitoring folders

---

## Verification

After fixing permissions, verify:

### Step 1: Run Verification Script

```bash
python verify_configuration.py
```

Look for:
```
Directory: ✅ Exists
Permissions: ✅ Writable
```

### Step 2: Test File Creation

```cmd
# Try creating a test file
echo test > C:\data\test1\permission_test.txt

# Check if it was created
dir C:\data\test1\permission_test.txt
```

If successful, permissions are correct!

### Step 3: Test Monitoring

```bash
# Start monitoring
python start_monitoring.py

# In another terminal, create a file
echo test > C:\data\test1\testfile.txt

# Check if detected
python check_test_system.py
```

---

## Best Practices

### 1. Use Local Directories

✅ **Good:**
```
C:\data\test1
C:\monitoring\sales
D:\file_drops\inventory
```

❌ **Avoid:**
```
\\network\share\data
C:\Users\YourName\OneDrive\data
```

### 2. Create Dedicated Monitoring Folder

```cmd
# Create a dedicated folder for all monitoring
mkdir C:\monitoring

# Create subfolders for each system
mkdir C:\monitoring\sales
mkdir C:\monitoring\inventory
mkdir C:\monitoring\customer
```

### 3. Set Permissions Once

After creating all directories, fix permissions for the parent:

```cmd
icacls "C:\monitoring" /grant %USERNAME%:(OI)(CI)F /T
```

This applies to all subdirectories automatically.

### 4. Document Your Setup

Keep a list of:
- Directory paths
- Permission settings
- Any special requirements

---

## Troubleshooting Commands

### Check Current Permissions

```cmd
# View permissions for a directory
icacls "C:\data\test1"
```

### Check Who Owns Directory

```cmd
# View ownership
dir /Q C:\data\test1
```

### Take Ownership (if needed)

```cmd
# Take ownership (as Administrator)
takeown /F "C:\data\test1" /R /D Y
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T
```

### Reset Permissions to Default

```cmd
# Reset to default Windows permissions
icacls "C:\data\test1" /reset /T
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Fix permissions | `python fix_permissions.py` |
| Manual fix | `icacls "C:\path" /grant %USERNAME%:(OI)(CI)F /T` |
| Check permissions | `icacls "C:\path"` |
| Create directory | `mkdir C:\path` |
| Test write access | `echo test > C:\path\test.txt` |
| Verify setup | `python verify_configuration.py` |

---

## Getting Help

If you're still having permission issues:

1. **Check Windows Event Viewer**
   - Look for access denied errors
   - Check Security logs

2. **Verify User Account**
   - Ensure you're logged in as the correct user
   - Check if account has admin rights

3. **Contact IT Support**
   - If on corporate network
   - If using managed devices

4. **Use Alternative Location**
   - Try a different drive (D:, E:)
   - Use a folder in your user directory

---

## Summary

**Quick Fix:**
```bash
python fix_permissions.py
```

**Manual Fix:**
```cmd
icacls "C:\data\test1" /grant %USERNAME%:(OI)(CI)F /T
```

**Verify:**
```bash
python verify_configuration.py
```

Your directories should now have correct permissions! ✅
