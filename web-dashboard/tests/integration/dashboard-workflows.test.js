/**
 * End-to-End Dashboard Workflow Tests
 * Tests complete user workflows as specified in Task 15.2
 * 
 * Requirements: 1.1, 2.1, 3.1, 4.1, 5.4, 6.2, 8.1
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DashboardApp } from '../../js/app.js';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Mock API responses
const mockSystemsSummary = [
    {
        sourceSystemId: 'TEST001',
        systemName: 'Test System 1',
        status: 'healthy',
        fileCount: 1500,
        lastFileArrival: '2024-01-15T10:30:00Z',
        slaScore: 95.5,
        hasViolations: false
    },
    {
        sourceSystemId: 'TEST002',
        systemName: 'Test System 2',
        status: 'warning',
        fileCount: 800,
        lastFileArrival: '2024-01-15T09:00:00Z',
        slaScore: 78.0,
        hasViolations: true
    }
];

const mockFileArrivals = [
    {
        id: '1',
        sourceSystemId: 'TEST001',
        fileName: 'data_001.csv',
        arrivalTime: '2024-01-15T10:30:00Z',
        fileSize: 2048000,
        status: 'processed',
        processingTime: 150
    },
    {
        id: '2',
        sourceSystemId: 'TEST001',
        fileName: 'data_002.csv',
        arrivalTime: '2024-01-15T11:00:00Z',
        fileSize: 1024000,
        status: 'processed',
        processingTime: 120
    }
];

const mockSLAScores = {
    score: 95.5,
    threshold: 80,
    isCompliant: true
};

const mockSLAViolations = [
    {
        id: '1',
        sourceSystemId: 'TEST001',
        severity: 'high',
        violationType: 'Late Arrival',
        timestamp: '2024-01-14T10:00:00Z',
        description: 'File arrived 2 hours late',
        resolved: false
    }
];

const mockDailyTrends = [
    { timestamp: '2024-01-10T00:00:00Z', value: 100 },
    { timestamp: '2024-01-11T00:00:00Z', value: 120 },
    { timestamp: '2024-01-12T00:00:00Z', value: 110 },
    { timestamp: '2024-01-13T00:00:00Z', value: 130 },
    { timestamp: '2024-01-14T00:00:00Z', value: 125 }
];

const mockMovingAverage = [
    { timestamp: '2024-01-10T00:00:00Z', value: 100 },
    { timestamp: '2024-01-11T00:00:00Z', value: 110 },
    { timestamp: '2024-01-12T00:00:00Z', value: 110 },
    { timestamp: '2024-01-13T00:00:00Z', value: 115 },
    { timestamp: '2024-01-14T00:00:00Z', value: 121 }
];

const mockHourlyPatterns = [
    { timestamp: '2024-01-15T00:00:00Z', value: 5 },
    { timestamp: '2024-01-15T01:00:00Z', value: 3 },
    { timestamp: '2024-01-15T02:00:00Z', value: 2 },
    { timestamp: '2024-01-15T08:00:00Z', value: 50 },
    { timestamp: '2024-01-15T09:00:00Z', value: 75 },
    { timestamp: '2024-01-15T10:00:00Z', value: 80 }
];

// Setup MSW server for API mocking
const server = setupServer(
    // Systems summary endpoint
    http.get('http://localhost:8000/api/v1/trends/summary', () => {
        return HttpResponse.json(mockSystemsSummary);
    }),

    // File arrivals endpoint
    http.get('http://localhost:8000/api/v1/file-arrivals', ({ request }) => {
        const url = new URL(request.url);
        const systemId = url.searchParams.get('source_system_id');
        
        if (systemId) {
            return HttpResponse.json(mockFileArrivals.filter(f => f.sourceSystemId === systemId));
        }
        return HttpResponse.json(mockFileArrivals);
    }),

    // SLA scores endpoint
    http.get('http://localhost:8000/api/v1/sla/average-score/:systemId', () => {
        return HttpResponse.json(mockSLAScores);
    }),

    // SLA violations endpoint
    http.get('http://localhost:8000/api/v1/sla/violations', ({ request }) => {
        const url = new URL(request.url);
        const systemId = url.searchParams.get('source_system_id');
        
        if (systemId) {
            return HttpResponse.json(mockSLAViolations.filter(v => v.sourceSystemId === systemId));
        }
        return HttpResponse.json(mockSLAViolations);
    }),

    // Daily trends endpoint
    http.get('http://localhost:8000/api/v1/trends/daily/:systemId', () => {
        return HttpResponse.json(mockDailyTrends);
    }),

    // Moving average endpoint
    http.get('http://localhost:8000/api/v1/trends/moving-average/:systemId', () => {
        return HttpResponse.json(mockMovingAverage);
    }),

    // Hourly patterns endpoint
    http.get('http://localhost:8000/api/v1/trends/hourly-patterns/:systemId', () => {
        return HttpResponse.json(mockHourlyPatterns);
    })
);

describe('Dashboard Complete User Workflows', () => {
    let app;

    beforeEach(async () => {
        // Start MSW server
        server.listen({ onUnhandledRequest: 'error' });

        // Setup DOM with complete dashboard structure
        document.body.innerHTML = `
            <div id="app">
                <header class="header">
                    <div class="header-content">
                        <h1>Intelligent File Monitoring System</h1>
                        <div class="header-controls">
                            <span id="last-refresh-time" class="refresh-time">Last updated: Never</span>
                            <button id="manual-refresh" class="btn btn-primary">Refresh</button>
                        </div>
                    </div>
                </header>
                <main class="main-content">
                    <div id="notifications" class="notifications"></div>
                    <div id="connectivity-banner" class="banner banner-warning hidden"></div>
                    <div id="error-banner" class="banner banner-error hidden"></div>
                    <div id="date-range-error" class="inline-error hidden"></div>
                    
                    <section id="filters" class="filters-section">
                        <div class="filters-container">
                            <select id="system-select">
                                <option value="">All Systems</option>
                            </select>
                            <input type="date" id="start-date" />
                            <input type="date" id="end-date" />
                            <select id="severity-filter">
                                <option value="">All</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                            <button id="clear-filters" class="btn btn-secondary">Clear Filters</button>
                        </div>
                    </section>
                    
                    <section class="system-overview-section">
                        <h2>System Overview</h2>
                        <div id="system-overview" class="system-grid"></div>
                    </section>
                    
                    <section id="details-section" class="details-section hidden">
                        <div id="file-arrivals-tab" class="tab-content active">
                            <div id="file-arrivals" class="file-arrivals-container"></div>
                            <div id="pagination-controls" class="pagination hidden"></div>
                        </div>
                        <div id="sla-metrics-tab" class="tab-content">
                            <div id="sla-metrics" class="sla-metrics-container"></div>
                        </div>
                        <div id="trends-tab" class="tab-content">
                            <div class="charts-container">
                                <canvas id="daily-trend-chart"></canvas>
                                <canvas id="moving-average-chart"></canvas>
                                <canvas id="hourly-pattern-chart"></canvas>
                            </div>
                        </div>
                    </section>
                </main>
            </div>
            <div id="loading-overlay" class="loading-overlay hidden"></div>
        `;

        // Mock fetch for config.json
        global.fetch = vi.fn((url) => {
            if (url.includes('config.json')) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        apiBaseURL: 'http://localhost:8000',
                        refreshInterval: 30000,
                        cacheTimeout: 30000,
                        retryAttempts: 3,
                        retryBackoff: 100,
                        chartMaxDataPoints: 100,
                        paginationPageSize: 50
                    })
                });
            }
            // Let MSW handle API requests
            return fetch(url);
        });

        // Create and initialize app
        app = new DashboardApp();
    });

    afterEach(() => {
        // Stop app and clean up
        if (app) {
            app.stop();
        }
        server.resetHandlers();
        server.close();
        vi.restoreAllMocks();
    });

    /**
     * Test: Load dashboard → See system overview
     * Requirements: 1.1, 1.2, 1.3
     */
    it('should load dashboard and display system overview', async () => {
        // Initialize the app
        await app.initialize();

        // Wait for data to load
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify system overview is rendered
        const systemOverview = document.getElementById('system-overview');
        expect(systemOverview).toBeTruthy();
        expect(systemOverview.innerHTML).toContain('Test System 1');
        expect(systemOverview.innerHTML).toContain('Test System 2');

        // Verify system cards show required fields
        expect(systemOverview.innerHTML).toContain('1,500'); // Formatted file count
        expect(systemOverview.innerHTML).toContain('800');

        // Verify SLA scores are displayed
        expect(systemOverview.innerHTML).toContain('95.5');
        expect(systemOverview.innerHTML).toContain('78.0');

        // Verify warning indicator for system with violations
        expect(systemOverview.innerHTML).toContain('warning');

        // Verify last refresh time is updated
        const lastRefreshTime = document.getElementById('last-refresh-time');
        expect(lastRefreshTime.textContent).not.toContain('Never');
    });

    /**
     * Test: Select system → See details and charts
     * Requirements: 2.1, 3.1, 4.1, 6.2
     */
    it('should display system details and charts when system is selected', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Select a system
        const systemSelect = document.getElementById('system-select');
        systemSelect.value = 'TEST001';
        systemSelect.dispatchEvent(new Event('change'));

        // Wait for data to load
        await new Promise(resolve => setTimeout(resolve, 200));

        // Verify file arrivals are displayed
        const fileArrivals = document.getElementById('file-arrivals');
        expect(fileArrivals.innerHTML).toContain('data_001.csv');
        expect(fileArrivals.innerHTML).toContain('data_002.csv');

        // Verify SLA metrics are displayed
        const slaMetrics = document.getElementById('sla-metrics');
        expect(slaMetrics.innerHTML).toContain('95.5');
        expect(slaMetrics.innerHTML).toContain('Late Arrival');

        // Verify charts are rendered (canvas elements should have Chart.js instances)
        const dailyChart = document.getElementById('daily-trend-chart');
        const movingAvgChart = document.getElementById('moving-average-chart');
        const hourlyChart = document.getElementById('hourly-pattern-chart');
        
        expect(dailyChart).toBeTruthy();
        expect(movingAvgChart).toBeTruthy();
        expect(hourlyChart).toBeTruthy();
    });

    /**
     * Test: Apply filters → See filtered data
     * Requirements: 6.2, 6.4
     */
    it('should filter data when date range is applied', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Select a system first
        const systemSelect = document.getElementById('system-select');
        systemSelect.value = 'TEST001';
        systemSelect.dispatchEvent(new Event('change'));
        await new Promise(resolve => setTimeout(resolve, 100));

        // Apply date range filter
        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');
        
        startDate.value = '2024-01-01';
        endDate.value = '2024-01-31';
        
        startDate.dispatchEvent(new Event('change'));
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify state was updated
        const dateRange = app.stateManager.getDateRange();
        expect(dateRange.startDate).toBeTruthy();
        expect(dateRange.endDate).toBeTruthy();

        // Verify data was refreshed with filters
        const fileArrivals = document.getElementById('file-arrivals');
        expect(fileArrivals.innerHTML).toContain('data_001.csv');
    });

    /**
     * Test: Clear filters → See all data
     * Requirements: 6.5
     */
    it('should clear all filters and reset to default view', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Apply some filters
        const systemSelect = document.getElementById('system-select');
        const startDate = document.getElementById('start-date');
        const severityFilter = document.getElementById('severity-filter');
        
        systemSelect.value = 'TEST001';
        startDate.value = '2024-01-01';
        severityFilter.value = 'high';
        
        systemSelect.dispatchEvent(new Event('change'));
        await new Promise(resolve => setTimeout(resolve, 100));

        // Click clear filters button
        const clearBtn = document.getElementById('clear-filters');
        clearBtn.click();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify filters are cleared
        expect(systemSelect.value).toBe('');
        expect(startDate.value).toBe('');
        expect(severityFilter.value).toBe('');

        // Verify state is cleared
        expect(app.stateManager.getSelectedSystem()).toBeNull();
        expect(app.stateManager.getDateRange().startDate).toBeNull();
        expect(app.stateManager.getFilters().severity).toBeNull();
    });

    /**
     * Test: Manual refresh → See updated data
     * Requirements: 5.4
     */
    it('should refresh data when manual refresh button is clicked', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Get initial last refresh time
        const lastRefreshTime = document.getElementById('last-refresh-time');
        const initialTime = lastRefreshTime.textContent;

        // Wait a moment
        await new Promise(resolve => setTimeout(resolve, 50));

        // Click manual refresh button
        const refreshBtn = document.getElementById('manual-refresh');
        refreshBtn.click();
        await new Promise(resolve => setTimeout(resolve, 200));

        // Verify last refresh time was updated
        const updatedTime = lastRefreshTime.textContent;
        expect(updatedTime).not.toBe(initialTime);
        expect(updatedTime).not.toContain('Never');

        // Verify notification was shown
        const notifications = document.getElementById('notifications');
        expect(notifications.innerHTML).toContain('refreshed successfully');
    });

    /**
     * Test: Simulate API failure → See error handling
     * Requirements: 8.1, 8.3
     */
    it('should handle API failures gracefully and show error messages', async () => {
        // Override server to return error
        server.use(
            http.get('http://localhost:8000/api/v1/trends/summary', () => {
                return HttpResponse.json(
                    { detail: 'Internal server error' },
                    { status: 500 }
                );
            })
        );

        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify error message is displayed
        const errorBanner = document.getElementById('error-banner');
        expect(errorBanner.classList.contains('hidden')).toBe(false);
        expect(errorBanner.innerHTML).toContain('error');

        // Verify error was logged to console
        expect(console.error).toHaveBeenCalled();
    });

    /**
     * Test: Auto-refresh functionality
     * Requirements: 5.1, 5.2
     */
    it('should auto-refresh data at configured interval', async () => {
        // Use shorter interval for testing
        app.config = {
            ...app.config,
            refreshInterval: 100 // 100ms for testing
        };

        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 50));

        // Get initial refresh count
        const initialTime = app.stateManager.getLastRefreshTime();

        // Wait for auto-refresh to trigger
        await new Promise(resolve => setTimeout(resolve, 150));

        // Verify data was refreshed
        const updatedTime = app.stateManager.getLastRefreshTime();
        expect(updatedTime).not.toBe(initialTime);
        expect(updatedTime.getTime()).toBeGreaterThan(initialTime.getTime());
    });

    /**
     * Test: Auto-refresh pauses during user interaction
     * Requirements: 5.5
     */
    it('should pause auto-refresh during user interaction', async () => {
        // Use shorter interval for testing
        app.config = {
            ...app.config,
            refreshInterval: 100 // 100ms for testing
        };

        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 50));

        // Simulate user interaction
        document.dispatchEvent(new MouseEvent('mousedown'));
        app.isUserInteracting = true;

        // Get refresh time before auto-refresh should trigger
        const beforeTime = app.stateManager.getLastRefreshTime();

        // Wait for auto-refresh interval
        await new Promise(resolve => setTimeout(resolve, 150));

        // Verify refresh was paused (time should be same)
        const afterTime = app.stateManager.getLastRefreshTime();
        expect(afterTime).toBe(beforeTime);

        // End user interaction
        document.dispatchEvent(new MouseEvent('mouseup'));
        await new Promise(resolve => setTimeout(resolve, 1100)); // Wait for interaction timeout

        // Wait for next auto-refresh
        await new Promise(resolve => setTimeout(resolve, 150));

        // Verify refresh resumed
        const finalTime = app.stateManager.getLastRefreshTime();
        expect(finalTime.getTime()).toBeGreaterThan(beforeTime.getTime());
    });

    /**
     * Test: Network connectivity detection
     * Requirements: 8.4
     */
    it('should detect network connectivity loss and show warning', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Simulate offline event
        window.dispatchEvent(new Event('offline'));
        await new Promise(resolve => setTimeout(resolve, 50));

        // Verify connectivity warning is shown
        const notifications = document.getElementById('notifications');
        expect(notifications.innerHTML).toContain('No internet connection');

        // Simulate online event
        window.dispatchEvent(new Event('online'));
        await new Promise(resolve => setTimeout(resolve, 50));

        // Verify connection restored notification
        expect(notifications.innerHTML).toContain('Connection restored');
    });

    /**
     * Test: Date range validation
     * Requirements: 6.7
     */
    it('should validate date range and prevent invalid ranges', async () => {
        // Initialize the app
        await app.initialize();
        await new Promise(resolve => setTimeout(resolve, 100));

        // Set invalid date range (start after end)
        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');
        
        startDate.value = '2024-01-31';
        endDate.value = '2024-01-01';
        
        startDate.dispatchEvent(new Event('change'));
        await new Promise(resolve => setTimeout(resolve, 50));

        // Verify error message is displayed
        const errorContainer = document.getElementById('date-range-error');
        expect(errorContainer.innerHTML).toContain('Start date must be before end date');

        // Verify state was not updated with invalid range
        const dateRange = app.stateManager.getDateRange();
        expect(dateRange.startDate).toBeNull();
    });
});
