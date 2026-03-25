# Design Document: Web Dashboard for Intelligent File Monitoring System

## Overview

The web dashboard is a single-page application (SPA) that provides real-time monitoring and visualization of the Intelligent File Monitoring System. It will be built using vanilla JavaScript with modern ES6+ features, HTML5, and CSS3 to minimize dependencies and simplify deployment. The dashboard communicates with the existing FastAPI backend via REST API calls and uses Chart.js for data visualization.

The architecture follows a modular design with separate concerns for API communication, state management, UI rendering, and chart visualization. This approach ensures maintainability and allows for easy testing of individual components.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Dashboard Application (SPA)             │  │
│  │                                                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │   UI     │  │  State   │  │   Chart      │  │  │
│  │  │ Manager  │◄─┤ Manager  │  │  Renderer    │  │  │
│  │  └──────────┘  └──────────┘  └──────────────┘  │  │
│  │       ▲             ▲              ▲            │  │
│  │       │             │              │            │  │
│  │       └─────────────┴──────────────┘            │  │
│  │                     │                           │  │
│  │              ┌──────────────┐                   │  │
│  │              │ API Client   │                   │  │
│  │              └──────────────┘                   │  │
│  └──────────────────────┬───────────────────────────┘  │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP/REST
                          ▼
              ┌────────────────────────┐
              │   FastAPI Backend      │
              │   (localhost:8000)     │
              └────────────────────────┘
```

### Component Responsibilities

1. **API Client**: Handles all HTTP communication with the FastAPI backend, including error handling, retries, and response caching
2. **State Manager**: Maintains application state (selected system, filters, data cache) and notifies components of state changes
3. **UI Manager**: Renders HTML components, handles user interactions, and updates the DOM based on state changes
4. **Chart Renderer**: Creates and updates Chart.js visualizations for trend data

### Technology Stack

- **Frontend Framework**: Vanilla JavaScript (ES6+)
- **Charting Library**: Chart.js 4.x
- **CSS Framework**: Custom CSS with CSS Grid and Flexbox
- **Build Tool**: None (direct browser execution)
- **HTTP Client**: Fetch API with custom wrapper

## Components and Interfaces

### 1. API Client Module (`api-client.js`)

**Purpose**: Centralized API communication with error handling and caching

**Interface**:
```javascript
class APIClient {
  constructor(baseURL)
  
  // File arrival endpoints
  async getFileArrivals(filters)
  async getFileCount(filters)
  
  // SLA endpoints
  async getSLAScores(sourceSystemId)
  async getAverageSLAScore(sourceSystemId)
  async getSLAViolations(filters)
  async getSLAViolationsBySeverity(sourceSystemId, severity)
  
  // Trend endpoints
  async getDailyTrends(sourceSystemId, dateRange)
  async getMovingAverage(sourceSystemId, window)
  async getHourlyPatterns(sourceSystemId)
  async getSystemsSummary()
  
  // Utility methods
  clearCache()
  setRetryPolicy(maxRetries, backoffMs)
}
```

**Key Behaviors**:
- Implements exponential backoff retry logic (max 3 retries)
- Caches responses for 30 seconds to reduce API load
- Throws structured errors with context for UI handling
- Supports request cancellation for component unmounting

### 2. State Manager Module (`state-manager.js`)

**Purpose**: Centralized state management with observer pattern

**Interface**:
```javascript
class StateManager {
  constructor()
  
  // State getters
  getSelectedSystem()
  getDateRange()
  getFilters()
  getLastRefreshTime()
  
  // State setters
  setSelectedSystem(systemId)
  setDateRange(startDate, endDate)
  setFilters(filters)
  updateLastRefreshTime()
  
  // Observer pattern
  subscribe(eventType, callback)
  unsubscribe(eventType, callback)
  notify(eventType, data)
  
  // Data cache
  setCachedData(key, data, ttl)
  getCachedData(key)
  clearCache()
}
```

**State Structure**:
```javascript
{
  selectedSystem: string | null,
  dateRange: {
    startDate: Date | null,
    endDate: Date | null
  },
  filters: {
    severity: string | null,
    status: string | null
  },
  lastRefreshTime: Date,
  autoRefreshEnabled: boolean,
  cache: Map<string, CachedData>
}
```

### 3. UI Manager Module (`ui-manager.js`)

**Purpose**: DOM manipulation and user interaction handling

**Interface**:
```javascript
class UIManager {
  constructor(stateManager, apiClient)
  
  // Initialization
  initialize()
  setupEventListeners()
  
  // Rendering methods
  renderSystemOverview(systems)
  renderFileArrivals(arrivals)
  renderSLAMetrics(scores, violations)
  renderFilters()
  renderErrorMessage(error)
  renderLoadingState(component)
  
  // Update methods
  updateSystemCard(systemId, data)
  updateLastRefreshTime(timestamp)
  showNotification(message, type)
  
  // Utility methods
  formatNumber(num)
  formatDate(date)
  getSeverityColor(severity)
}
```

### 4. Chart Renderer Module (`chart-renderer.js`)

**Purpose**: Chart.js wrapper for creating and updating visualizations

**Interface**:
```javascript
class ChartRenderer {
  constructor()
  
  // Chart creation
  createDailyTrendChart(canvasId, data)
  createMovingAverageChart(canvasId, data)
  createHourlyPatternChart(canvasId, data)
  createSLAScoreChart(canvasId, data)
  
  // Chart updates
  updateChart(chartId, newData)
  destroyChart(chartId)
  
  // Configuration
  getDefaultChartOptions()
  getChartColors()
}
```

### 5. Main Application Module (`app.js`)

**Purpose**: Application orchestration and lifecycle management

**Interface**:
```javascript
class DashboardApp {
  constructor()
  
  // Lifecycle
  async initialize()
  start()
  stop()
  
  // Data refresh
  async refreshAllData()
  async refreshSystemOverview()
  async refreshSelectedSystemData()
  startAutoRefresh()
  stopAutoRefresh()
  
  // Event handlers
  handleSystemSelection(systemId)
  handleFilterChange(filters)
  handleManualRefresh()
  handleError(error)
}
```

## Data Models

### SystemSummary
```javascript
{
  sourceSystemId: string,
  systemName: string,
  status: "healthy" | "warning" | "critical",
  fileCount: number,
  lastFileArrival: Date | null,
  slaScore: number,
  hasViolations: boolean
}
```

### FileArrival
```javascript
{
  id: string,
  sourceSystemId: string,
  fileName: string,
  arrivalTime: Date,
  fileSize: number,
  status: "processed" | "pending" | "failed",
  processingTime: number | null
}
```

### SLAScore
```javascript
{
  sourceSystemId: string,
  score: number,
  timestamp: Date,
  threshold: number,
  isCompliant: boolean
}
```

### SLAViolation
```javascript
{
  id: string,
  sourceSystemId: string,
  severity: "high" | "medium" | "low",
  violationType: string,
  timestamp: Date,
  description: string,
  resolved: boolean
}
```

### TrendData
```javascript
{
  sourceSystemId: string,
  dataPoints: Array<{
    timestamp: Date,
    value: number
  }>,
  aggregationType: "daily" | "hourly" | "moving_average"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas where properties can be consolidated:

**API Endpoint Verification (1.4, 2.4, 3.2, 3.3, 3.5, 4.2, 4.3, 4.4)**: All these criteria test that correct API endpoints are called. These can be combined into a single comprehensive property that verifies the API client calls the correct endpoint for each operation type.

**Required Field Rendering (1.2, 2.2, 3.4)**: These all test that rendered components contain required fields. Can be combined into a property about complete data rendering.

**Error Handling (1.5, 8.1, 8.3, 8.4, 8.5, 8.6)**: Multiple properties about error handling can be consolidated into fewer comprehensive properties about error display and recovery.

**Loading States (4.7, 7.6)**: Both test loading indicators, can be combined.

**Filter Application (2.3, 6.4)**: Both test that filters are passed to API calls, can be combined.

After reflection, I'll focus on unique, high-value properties that provide distinct validation coverage.

### Correctness Properties

Property 1: System overview completeness
*For any* list of source systems returned from the API, the dashboard should render exactly one summary card per system with all required fields (system name, status, file count)
**Validates: Requirements 1.1, 1.2**

Property 2: Violation highlighting
*For any* source system with SLA violations, the rendered summary card should include warning indicators (CSS class or visual styling)
**Validates: Requirements 1.3**

Property 3: API endpoint correctness
*For any* dashboard operation (get summary, get file arrivals, get SLA scores, get trends), the API client should call the correct REST endpoint with appropriate parameters
**Validates: Requirements 1.4, 2.4, 3.2, 3.3, 3.5, 4.2, 4.3, 4.4**

Property 4: Error state preservation
*For any* API failure, the dashboard should display an error message and maintain the last successfully loaded data in the UI
**Validates: Requirements 1.5, 8.3**

Property 5: System selection filtering
*For any* selected source system, all displayed data (file arrivals, SLA scores, trends) should be filtered to show only that system's information
**Validates: Requirements 2.1, 3.1, 6.2**

Property 6: Complete data field rendering
*For any* data entity (file arrival, SLA violation, system summary), the rendered HTML should contain all required fields specified in the requirements
**Validates: Requirements 1.2, 2.2, 3.4**

Property 7: Filter parameter propagation
*For any* applied filter (date range, severity, status), all subsequent API requests should include those filter parameters in the query string
**Validates: Requirements 2.3, 6.4**

Property 8: Pagination for large datasets
*For any* file arrival list with more than 50 items, the dashboard should render pagination controls and display items in pages
**Validates: Requirements 2.5**

Property 9: Severity color mapping
*For any* SLA violation or system status, the dashboard should apply the correct color coding (green=healthy, yellow=warning, red=critical/high, orange=medium, blue=low)
**Validates: Requirements 3.6, 7.3**

Property 10: SLA score warning threshold
*For any* SLA score below 80, the dashboard should display a warning indicator alongside the score
**Validates: Requirements 3.7**

Property 11: Chart rendering on system selection
*For any* selected source system with trend data, the dashboard should render at least one chart visualization (daily, moving average, or hourly)
**Validates: Requirements 4.1**

Property 12: Chart tooltip interactivity
*For any* rendered chart, hovering over data points should display a tooltip containing the exact value and timestamp
**Validates: Requirements 4.6**

Property 13: Auto-refresh interval
*For any* 30-second time window with auto-refresh enabled, the dashboard should trigger exactly one data refresh operation
**Validates: Requirements 5.1**

Property 14: Refresh without page reload
*For any* data refresh operation (auto or manual), the dashboard should update displayed data without causing a full page reload (window.location should not change)
**Validates: Requirements 5.2**

Property 15: Manual refresh availability
*For any* dashboard state, a manual refresh button should be present and clicking it should trigger an immediate data refresh
**Validates: Requirements 5.4**

Property 16: Auto-refresh pause during interaction
*For any* user interaction with filters or controls, auto-refresh should be paused until the interaction completes
**Validates: Requirements 5.5**

Property 17: Refresh timestamp display
*For any* successful data refresh, the dashboard should update and display the timestamp of that refresh
**Validates: Requirements 5.6**

Property 18: Filter reset functionality
*For any* applied filters, clicking the "Clear Filters" button should reset all filters to their default values (no system selected, no date range, no severity filter)
**Validates: Requirements 6.5**

Property 19: URL state synchronization
*For any* filter change (system selection, date range, severity), the browser URL should be updated to include query parameters reflecting the current filter state
**Validates: Requirements 6.6**

Property 20: Date range validation
*For any* date range input where start date is after end date, the dashboard should display a validation error and prevent the filter from being applied
**Validates: Requirements 6.7**

Property 21: Number formatting with separators
*For any* displayed number greater than 999, the dashboard should format it with thousand separators (e.g., 1,000 not 1000)
**Validates: Requirements 7.5**

Property 22: Loading indicator display
*For any* asynchronous data fetch operation, the dashboard should display a loading indicator (spinner or skeleton) until the data is received or an error occurs
**Validates: Requirements 4.7, 7.6**

Property 23: Error message display
*For any* API request failure, the dashboard should display a user-friendly error message containing actionable guidance
**Validates: Requirements 8.1, 8.5**

Property 24: Retry with exponential backoff
*For any* API request timeout, the API client should retry the request up to 3 times with exponentially increasing delays between attempts
**Validates: Requirements 8.2**

Property 25: Network connectivity warning
*For any* detected loss of network connectivity, the dashboard should display a warning banner indicating offline status
**Validates: Requirements 8.4**

Property 26: Error logging
*For any* error that occurs (API failure, validation error, rendering error), the dashboard should log the error details to the browser console
**Validates: Requirements 8.6**

Property 27: System switch performance
*For any* source system selection change, the dashboard should complete the UI update within 500 milliseconds
**Validates: Requirements 9.2**

Property 28: Response caching
*For any* API endpoint, making the same request twice within 30 seconds should result in only one actual HTTP request (the second should use cached data)
**Validates: Requirements 9.3**

Property 29: Chart data point limiting
*For any* trend dataset with more than 100 data points, the rendered chart should display at most 100 points (using sampling or aggregation)
**Validates: Requirements 9.4**

Property 30: Configuration file usage
*For any* configured Backend API URL in the configuration file, the API client should use that URL for all requests
**Validates: Requirements 10.2**

Property 31: Default API URL fallback
*For any* dashboard initialization without a configured API URL, the API client should default to http://localhost:8000
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Network Errors**: Connection failures, timeouts, DNS resolution failures
2. **API Errors**: 4xx client errors, 5xx server errors, malformed responses
3. **Validation Errors**: Invalid user input, date range errors, missing required fields
4. **Rendering Errors**: Chart rendering failures, DOM manipulation errors

### Error Handling Strategy

**Network Errors**:
- Implement retry logic with exponential backoff (100ms, 200ms, 400ms)
- Display connectivity warning banner
- Maintain last known good state
- Log error details to console

**API Errors**:
- Parse error responses for specific error messages
- Display user-friendly error messages with context
- For 404 errors: "System not found"
- For 500 errors: "Server error, please try again"
- For timeout: "Request timed out, retrying..."

**Validation Errors**:
- Validate inputs before API calls
- Display inline validation messages near input fields
- Prevent form submission until validation passes
- Highlight invalid fields with red borders

**Rendering Errors**:
- Wrap rendering code in try-catch blocks
- Log rendering errors to console
- Display fallback UI for failed components
- Prevent entire dashboard from crashing due to single component failure

### Error Recovery

- **Automatic Recovery**: Retry failed requests, clear cache on persistent errors
- **Manual Recovery**: Provide "Retry" buttons in error messages
- **Graceful Degradation**: Show partial data if some API calls fail
- **State Preservation**: Maintain user selections and filters across errors

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Test specific error scenarios (404, 500, timeout)
- Test empty state rendering (no systems, no files, no violations)
- Test specific date range examples
- Test UI component integration
- Test Chart.js integration and configuration

**Property-Based Tests**: Verify universal properties across all inputs
- Generate random system data and verify rendering completeness
- Generate random filter combinations and verify API parameter correctness
- Generate random error scenarios and verify error handling
- Generate random datasets and verify caching behavior
- Each property test should run minimum 100 iterations

### Property-Based Testing Configuration

**Library**: fast-check (JavaScript property-based testing library)
**Configuration**:
- Minimum 100 iterations per property test
- Seed-based reproducibility for failed tests
- Shrinking enabled to find minimal failing examples

**Test Tagging**: Each property test must include a comment referencing the design property:
```javascript
// Feature: web-dashboard, Property 1: System overview completeness
test('renders complete system summary cards', async () => {
  await fc.assert(
    fc.asyncProperty(fc.array(systemGenerator()), async (systems) => {
      // Test implementation
    }),
    { numRuns: 100 }
  );
});
```

### Test Organization

```
tests/
├── unit/
│   ├── api-client.test.js
│   ├── state-manager.test.js
│   ├── ui-manager.test.js
│   ├── chart-renderer.test.js
│   └── app.test.js
├── property/
│   ├── rendering.property.test.js
│   ├── api-integration.property.test.js
│   ├── filtering.property.test.js
│   ├── error-handling.property.test.js
│   └── caching.property.test.js
├── integration/
│   └── dashboard.integration.test.js
└── helpers/
    ├── generators.js (fast-check generators)
    ├── mocks.js (API mocks)
    └── fixtures.js (test data)
```

### Testing Tools

- **Test Runner**: Jest or Vitest
- **Property Testing**: fast-check
- **DOM Testing**: @testing-library/dom
- **API Mocking**: MSW (Mock Service Worker)
- **Coverage**: Istanbul/nyc (target: 80% coverage)

### Key Testing Scenarios

1. **Happy Path**: All APIs return valid data, user interactions work smoothly
2. **Error Scenarios**: API failures, network errors, invalid data
3. **Edge Cases**: Empty datasets, very large datasets, boundary values
4. **Performance**: Response time validation, caching verification
5. **State Management**: Filter persistence, URL synchronization, cache invalidation
6. **Accessibility**: Keyboard navigation, screen reader compatibility (manual testing)

## Implementation Notes

### File Structure

```
web-dashboard/
├── index.html
├── css/
│   ├── main.css
│   ├── components.css
│   └── responsive.css
├── js/
│   ├── app.js
│   ├── api-client.js
│   ├── state-manager.js
│   ├── ui-manager.js
│   ├── chart-renderer.js
│   └── utils.js
├── config/
│   └── config.json
├── tests/
│   └── (as described in Testing Strategy)
├── package.json
└── README.md
```

### Configuration File Format

```json
{
  "apiBaseURL": "http://localhost:8000",
  "refreshInterval": 30000,
  "cacheTimeout": 30000,
  "retryAttempts": 3,
  "retryBackoff": 100,
  "chartMaxDataPoints": 100,
  "paginationPageSize": 50
}
```

### Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Performance Targets

- Initial load: < 2 seconds
- System switch: < 500ms
- Chart render: < 300ms
- API response cache hit: < 10ms

### Security Considerations

- No sensitive data stored in localStorage
- API calls use relative URLs to prevent CORS issues
- Input sanitization for all user inputs
- CSP headers recommended for production deployment
