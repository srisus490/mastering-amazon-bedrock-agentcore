# Dashboard Testing Guide

This guide provides instructions for manually testing the complete user workflows of the File Monitoring Dashboard.

## Prerequisites

1. Ensure the backend API is running at `http://localhost:8000`
2. Start a local web server in the `web-dashboard` directory:
   ```bash
   npx serve .
   # or
   python -m http.server 8080
   ```
3. Open the dashboard in a web browser (e.g., `http://localhost:3000` or `http://localhost:8080`)

## Test Workflows

### Test 1: Load Dashboard → See System Overview
**Requirements: 1.1, 1.2, 1.3**

**Steps:**
1. Open the dashboard in your browser
2. Wait for the page to load

**Expected Results:**
- ✓ System overview section displays cards for all monitored source systems
- ✓ Each system card shows:
  - System name
  - Current status (healthy/warning/critical)
  - File count (formatted with commas, e.g., "1,500")
  - SLA score
- ✓ Systems with SLA violations show warning indicators
- ✓ Last refresh timestamp is displayed in the header (not "Never")
- ✓ No error messages are shown

---

### Test 2: Select System → See Details and Charts
**Requirements: 2.1, 3.1, 4.1, 6.2**

**Steps:**
1. From the system overview, click on a system card OR use the dropdown filter
2. Select a specific source system (e.g., "TEST001")
3. Wait for data to load

**Expected Results:**
- ✓ File Arrivals tab shows:
  - List of file arrivals for the selected system
  - File names, arrival times, status, file sizes
  - Pagination controls if more than 50 files
- ✓ SLA Metrics tab shows:
  - Current SLA score
  - Average SLA score
  - List of SLA violations with severity levels (high/medium/low)
  - Color-coded severity indicators
- ✓ Trends tab shows:
  - Daily file counts chart
  - Moving average chart
  - Hourly patterns chart
- ✓ Charts display tooltips when hovering over data points
- ✓ Loading indicators appear briefly during data fetch

---

### Test 3: Apply Filters → See Filtered Data
**Requirements: 6.2, 6.4**

**Steps:**
1. Select a source system from the dropdown
2. Set a start date (e.g., "2024-01-01")
3. Set an end date (e.g., "2024-01-31")
4. Optionally select a severity filter (e.g., "High")
5. Wait for data to refresh

**Expected Results:**
- ✓ File arrivals are filtered to the selected date range
- ✓ SLA violations are filtered by severity (if selected)
- ✓ Charts update to show data for the selected date range
- ✓ URL updates to include filter parameters (for bookmarking)
- ✓ Data refreshes automatically with new filters applied

---

### Test 4: Clear Filters → See All Data
**Requirements: 6.5**

**Steps:**
1. Apply some filters (system, date range, severity)
2. Click the "Clear Filters" button
3. Wait for data to refresh

**Expected Results:**
- ✓ System dropdown resets to "All Systems"
- ✓ Date inputs are cleared
- ✓ Severity filter resets to "All"
- ✓ System overview shows all systems again
- ✓ Details section is hidden (no system selected)
- ✓ URL parameters are cleared

---

### Test 5: Manual Refresh → See Updated Data
**Requirements: 5.4**

**Steps:**
1. Note the current "Last updated" timestamp in the header
2. Wait a few seconds
3. Click the "Refresh" button in the header
4. Wait for refresh to complete

**Expected Results:**
- ✓ Refresh button is temporarily disabled during refresh
- ✓ Loading indicators appear briefly
- ✓ "Last updated" timestamp updates to current time
- ✓ Success notification appears: "Data refreshed successfully"
- ✓ All visible data is refreshed (system overview, details, charts)
- ✓ Refresh button is re-enabled after completion

---

### Test 6: Simulate API Failure → See Error Handling
**Requirements: 8.1, 8.3**

**Steps:**
1. Stop the backend API server
2. Click the "Refresh" button OR wait for auto-refresh
3. Observe error handling

**Expected Results:**
- ✓ Error banner appears at the top of the page
- ✓ Error message is user-friendly and actionable (e.g., "Failed to fetch data. Check if API is running at http://localhost:8000")
- ✓ Error notification appears
- ✓ Last successfully loaded data remains visible (not cleared)
- ✓ Error is logged to browser console (check DevTools)
- ✓ Dashboard remains functional (can still interact with UI)

**Recovery Test:**
1. Restart the backend API server
2. Click the "Refresh" button
3. Verify data loads successfully and error banner disappears

---

### Test 7: Auto-Refresh Functionality
**Requirements: 5.1, 5.2**

**Steps:**
1. Load the dashboard
2. Note the "Last updated" timestamp
3. Wait 30 seconds without interacting
4. Observe the timestamp

**Expected Results:**
- ✓ After 30 seconds, data automatically refreshes
- ✓ "Last updated" timestamp updates
- ✓ Page does NOT reload (no flicker, URL doesn't change)
- ✓ Charts and data update smoothly
- ✓ Auto-refresh continues every 30 seconds

---

### Test 8: Auto-Refresh Pauses During Interaction
**Requirements: 5.5**

**Steps:**
1. Load the dashboard
2. Start interacting with filters or controls (e.g., hover over dropdown, type in date field)
3. Keep interacting for more than 30 seconds
4. Observe that auto-refresh doesn't interrupt your interaction
5. Stop interacting and wait

**Expected Results:**
- ✓ Auto-refresh does NOT trigger while actively interacting
- ✓ No jarring updates or data changes during interaction
- ✓ Auto-refresh resumes ~1 second after interaction ends
- ✓ Console logs show "Auto-refresh paused due to user interaction" (check DevTools)

---

### Test 9: Date Range Validation
**Requirements: 6.7**

**Steps:**
1. Select a source system
2. Set start date to "2024-01-31"
3. Set end date to "2024-01-01" (before start date)
4. Observe validation

**Expected Results:**
- ✓ Inline error message appears: "Start date must be before end date"
- ✓ Data is NOT refreshed with invalid date range
- ✓ Previous data remains visible
- ✓ Error message disappears when valid dates are entered

---

### Test 10: Network Connectivity Detection
**Requirements: 8.4**

**Steps:**
1. Load the dashboard with working internet
2. Open browser DevTools → Network tab
3. Set network to "Offline" mode
4. Observe the dashboard

**Expected Results:**
- ✓ Connectivity warning banner appears: "Network connectivity lost. Displaying cached data."
- ✓ Error notification appears: "No internet connection"
- ✓ Last loaded data remains visible

**Recovery Test:**
1. Set network back to "Online"
2. Observe the dashboard

**Expected Results:**
- ✓ Success notification appears: "Connection restored"
- ✓ Data automatically refreshes
- ✓ Connectivity warning banner disappears

---

### Test 11: Number Formatting
**Requirements: 7.5**

**Steps:**
1. Load the dashboard
2. Observe file counts in system cards
3. Select a system with large file counts

**Expected Results:**
- ✓ Numbers > 999 are formatted with thousand separators
- ✓ Examples: "1,500" not "1500", "1,234,567" not "1234567"
- ✓ Formatting applies to:
  - File counts in system cards
  - File sizes in file arrivals
  - Any other large numbers

---

### Test 12: SLA Score Warning Threshold
**Requirements: 3.7**

**Steps:**
1. Load the dashboard
2. Find a system with SLA score < 80
3. Observe the system card and SLA metrics

**Expected Results:**
- ✓ System card shows warning indicator
- ✓ SLA score is highlighted or color-coded (yellow/red)
- ✓ Warning icon or badge appears next to score
- ✓ System status shows "warning" or "critical"

---

### Test 13: Chart Interactivity
**Requirements: 4.6**

**Steps:**
1. Select a source system
2. Navigate to the Trends tab
3. Hover over data points on each chart

**Expected Results:**
- ✓ Tooltip appears when hovering over data points
- ✓ Tooltip shows exact value and timestamp
- ✓ Tooltip follows mouse cursor
- ✓ Tooltip disappears when mouse leaves chart area
- ✓ All three charts (daily, moving average, hourly) have working tooltips

---

### Test 14: Pagination
**Requirements: 2.5**

**Steps:**
1. Select a system with > 50 file arrivals
2. Observe the file arrivals list

**Expected Results:**
- ✓ Only 50 files are displayed per page
- ✓ Pagination controls appear at bottom
- ✓ Shows "Showing 1-50 of X" (where X is total count)
- ✓ "Next" button is enabled
- ✓ "Previous" button is disabled on first page
- ✓ Clicking "Next" loads next 50 files
- ✓ Clicking "Previous" goes back to previous page

---

### Test 15: Responsive Layout
**Requirements: 7.1**

**Steps:**
1. Load the dashboard on desktop
2. Resize browser window to tablet size (~768px)
3. Resize to mobile size (~375px)

**Expected Results:**
- ✓ Layout adapts to different screen sizes
- ✓ System cards stack vertically on smaller screens
- ✓ Filters remain accessible and usable
- ✓ Charts resize appropriately
- ✓ No horizontal scrolling required
- ✓ All controls remain clickable and usable

---

## Automated Testing

To run the automated test suite:

```bash
# Install dependencies (if not already installed)
npm install

# Run all tests
npm test

# Run only integration tests
npm test tests/integration

# Run specific workflow tests
npm test tests/integration/dashboard-workflows.test.js

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run coverage
```

## Troubleshooting

### Dashboard doesn't load
- Check that backend API is running at `http://localhost:8000`
- Check browser console for errors (F12 → Console tab)
- Verify `config/config.json` has correct API URL

### No data appears
- Verify backend API has data (visit `http://localhost:8000/api/v1/trends/summary` in browser)
- Check Network tab in DevTools for failed requests
- Look for error messages in dashboard

### Charts don't render
- Verify Chart.js is loaded (check Network tab for CDN request)
- Check browser console for Chart.js errors
- Ensure canvas elements exist in DOM

### Auto-refresh not working
- Check console for "Auto-refresh triggered" messages
- Verify `refreshInterval` in config.json is set correctly
- Ensure no JavaScript errors are blocking execution

### Tests fail
- Ensure all dependencies are installed: `npm install`
- Check that test environment has jsdom and MSW installed
- Verify Node.js version is 18+ (for MSW compatibility)

## Browser Console Commands

For debugging, you can access the dashboard app instance in the browser console:

```javascript
// Access the app instance
window.dashboardApp

// Get current state
window.dashboardApp.stateManager.getState()

// Manually trigger refresh
window.dashboardApp.refreshAllData()

// Stop auto-refresh
window.dashboardApp.stopAutoRefresh()

// Start auto-refresh
window.dashboardApp.startAutoRefresh()

// Clear cache
window.dashboardApp.apiClient.clearCache()
```

## Success Criteria

All tests should pass with:
- ✓ No console errors (except expected errors during error handling tests)
- ✓ Smooth user experience with no jarring transitions
- ✓ Data loads within 2 seconds on initial load
- ✓ System switches complete within 500ms
- ✓ All interactive elements respond to user input
- ✓ Error messages are clear and actionable
- ✓ Dashboard remains functional even when API is unavailable
