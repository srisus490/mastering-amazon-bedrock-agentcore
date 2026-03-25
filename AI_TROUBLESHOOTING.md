# AI Insights Troubleshooting Guide

## Issue: "An error occurred generating insights"

### Quick Diagnosis Steps

1. **Open Browser Console** (F12 → Console tab)
   - Look for error messages in red
   - Check for network errors
   - Look for JavaScript errors

2. **Check Network Tab** (F12 → Network tab)
   - Filter by "ai"
   - Look for failed requests (red)
   - Check response status codes

3. **Test API Directly**
   ```bash
   python test_frontend_api.py
   ```

### Common Issues and Solutions

#### Issue 1: CORS Errors
**Symptoms:** Console shows "CORS policy" error

**Solution:**
- API server already has CORS enabled
- Make sure you're accessing dashboard from `localhost:3000`
- Don't use `file://` protocol

#### Issue 2: API Server Not Running
**Symptoms:** "Failed to fetch" or "Network error"

**Solution:**
```bash
# Start API server
uvicorn src.api.app:create_app --factory --reload
```

#### Issue 3: JavaScript Module Errors
**Symptoms:** "Cannot find module" or "Unexpected token"

**Solution:**
- Clear browser cache (Ctrl+Shift+R)
- Check that all JS files exist:
  - `web-dashboard/js/api-client.js`
  - `web-dashboard/js/ai-insights-manager.js`
  - `web-dashboard/js/app.js`

#### Issue 4: Date Format Issues
**Symptoms:** "Invalid date range" or 400 error

**Solution:**
- Dates must be in YYYY-MM-DD format
- Start date must be before end date
- Check StateManager is providing correct format

#### Issue 5: System Not Found
**Symptoms:** 404 error

**Solution:**
- Verify system exists in database
- Check system ID spelling (case-sensitive)
- Run: `python test_frontend_api.py` with correct system ID

### Testing Tools

#### 1. Test API Directly
```bash
python test_frontend_api.py
```
This tests the backend API with the same parameters the frontend uses.

#### 2. Test JavaScript API Client
Open: `http://localhost:3000/test-ai.html`

This page tests the JavaScript API client in isolation:
- Click "Test Insights" button
- Click "Test Forecast" button
- Click "Test Root Cause" button
- Check results in the page and console

#### 3. Test Backend Service
```bash
python test_insights_service.py
```
This tests the Python service directly.

### Debugging Steps

#### Step 1: Verify Backend is Working
```bash
# Test backend
python test_insights_service.py

# Should show:
# ✓ Insights generated
# ✓ Forecast generated
# ✓ Root cause analysis generated
```

#### Step 2: Verify API Endpoints
```bash
# Test API
python test_frontend_api.py

# Should show:
# ✓ Success for all three endpoints
```

#### Step 3: Test JavaScript in Isolation
1. Open `http://localhost:3000/test-ai.html`
2. Open browser console (F12)
3. Click each test button
4. Check for errors in console

#### Step 4: Check Main Dashboard
1. Open `http://localhost:3000`
2. Open browser console (F12)
3. Select a system
4. Watch console for errors
5. Look for these log messages:
   - "Loading smart insights for..."
   - "Smart insights received:"
   - "Smart insights rendered successfully"

### Improved Error Logging

The frontend now has enhanced logging. In the browser console, you should see:

**Success case:**
```
Loading smart insights for PROD_ANALYTICS (2026-02-14 to 2026-02-19)
Smart insights received: {insights: "...", trends: [...], ...}
Smart insights rendered successfully
```

**Error case:**
```
Loading smart insights for PROD_ANALYTICS (2026-02-14 to 2026-02-19)
Failed to load smart insights: Error: HTTP 500: Internal Server Error
Error details: HTTP 500: Internal Server Error
  at _fetchWithRetry (api-client.js:45)
  ...
```

### Check These Files

If errors persist, verify these files are correct:

1. **web-dashboard/js/api-client.js**
   - Has `getSmartInsights()` method
   - Has `getForecast()` method
   - Has `getRootCauseAnalysis()` method

2. **web-dashboard/js/ai-insights-manager.js**
   - Exists and is valid JavaScript
   - Has all render methods

3. **web-dashboard/js/app.js**
   - Imports AIInsightsManager
   - Initializes aiInsightsManager
   - Calls loadAIInsights()

4. **web-dashboard/index.html**
   - Has AI insights section
   - Has correct element IDs:
     - `ai-insights-section`
     - `ai-insights-content`
     - `ai-forecast-content`
     - `ai-root-cause-content`

### Hard Refresh

After making changes, always do a hard refresh:
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

This clears the browser cache and loads fresh JavaScript files.

### Still Not Working?

1. **Check browser console** - Copy the exact error message
2. **Check network tab** - Look at the failed request details
3. **Test with curl:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ai/insights \
     -H "Content-Type: application/json" \
     -d '{"source_system_id":"PROD_ANALYTICS","start_date":"2026-02-14","end_date":"2026-02-19"}'
   ```

4. **Check API server logs** - Look at the terminal where uvicorn is running

### Expected Behavior

When working correctly:
1. Select a system from dropdown
2. AI Insights section appears
3. Three panels show loading spinners
4. After 1-10 seconds, insights appear
5. Cached responses load instantly (< 1s)

### Performance Notes

- **First load:** 5-15 seconds (calls Bedrock API)
- **Cached load:** < 1 second (from SQLite cache)
- **Cache TTL:** 
  - Insights: 1 hour
  - Forecast: 6 hours
  - Root Cause: 1 hour

### Contact Information

If issues persist:
1. Copy browser console errors
2. Copy network tab details
3. Run all test scripts and share output
4. Check API server logs for errors
