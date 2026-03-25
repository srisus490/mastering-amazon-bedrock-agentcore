/**
 * Main Application Module
 * Orchestrates the dashboard application lifecycle
 * 
 * Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 6.2, 8.6
 */

import { APIClient } from './api-client.js?v=8';
import { StateManager } from './state-manager.js?v=2';
import { UIManager } from './ui-manager.js?v=12';
import { ChartRenderer } from './chart-renderer.js?v=2';
import { AIInsightsManager } from './ai-insights-manager.js?v=4';
import { ThemeManager } from './theme-manager.js?v=1';
import { DatePresetsManager } from './date-presets.js?v=1';
import { ChatWidget } from './chat-widget.js?v=6';
import { ChatManager } from './chat-manager.js?v=4';
import { MessageFormatter } from './message-formatter.js?v=1';

export class DashboardApp {
    constructor() {
        this.config = null;
        this.apiClient = null;
        this.stateManager = null;
        this.uiManager = null;
        this.chartRenderer = null;
        this.aiInsightsManager = null;
        this.themeManager = null;
        this.datePresetsManager = null;
        this.chatWidget = null;
        this.chatManager = null;
        this.messageFormatter = null;
        this.autoRefreshInterval = null;
        this.isUserInteracting = false;
        console.log('DashboardApp created');
    }

    /**
     * Initialize the application
     * Requirements: 5.1, 5.2, 6.2
     */
    async initialize() {
        try {
            console.log('Initializing Dashboard Application...');

            // Load configuration
            await this.loadConfig();

            // Create component instances
            this.apiClient = new APIClient(this.config.apiBaseURL);
            this.stateManager = new StateManager();
            this.uiManager = new UIManager(this.stateManager, this.apiClient);
            this.chartRenderer = new ChartRenderer();
            this.aiInsightsManager = new AIInsightsManager(this.apiClient, this.uiManager);
            this.themeManager = new ThemeManager();
            this.datePresetsManager = new DatePresetsManager(this.stateManager);
            
            // Create chat components
            this.chatManager = new ChatManager(this.apiClient);
            this.messageFormatter = new MessageFormatter();
            this.chatWidget = new ChatWidget(this.chatManager, this.messageFormatter);

            // Configure API client with retry policy from config
            this.apiClient.setRetryPolicy(
                this.config.retryAttempts,
                this.config.retryBackoff
            );

            // Initialize theme manager first (for visual consistency)
            this.themeManager.initialize();

            // Setup event listeners
            this.setupEventListeners();

            // Initialize UI
            this.uiManager.initialize();
            
            // Initialize date presets
            this.datePresetsManager.initialize();
            
            // Initialize chat widget
            this.chatWidget.initialize();
            this.chatWidget.setStateManager(this.stateManager);

            // Load state from URL (for bookmarked views)
            this.stateManager.loadStateFromURL();

            // Load initial data
            await this.refreshAllData();

            // Start auto-refresh
            this.startAutoRefresh();

            console.log('Dashboard Application initialized successfully');
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    /**
     * Load configuration from config.json
     * Requirements: 10.2, 10.5
     */
    async loadConfig() {
        try {
            const response = await fetch('./config/config.json');
            if (!response.ok) {
                throw new Error('Failed to load configuration');
            }
            this.config = await response.json();
            console.log('Configuration loaded:', this.config);
        } catch (error) {
            console.warn('Failed to load config.json, using defaults:', error);
            // Fallback to default configuration (Requirement 10.5)
            this.config = {
                apiBaseURL: 'http://localhost:8000',
                refreshInterval: 30000,
                cacheTimeout: 30000,
                retryAttempts: 3,
                retryBackoff: 100,
                chartMaxDataPoints: 100,
                paginationPageSize: 50
            };
        }
    }

    /**
     * Setup event listeners for state changes and user interactions
     * Requirements: 5.5, 6.2
     */
    setupEventListeners() {
        // System selection change
        this.stateManager.subscribe('systemChanged', (data) => {
            this.handleSystemSelection(data.systemId);
            // Update chat examples based on selected system
            if (this.chatWidget) {
                this.chatWidget.updateExamples(data.systemId);
            }
        });

        // Filter changes
        this.stateManager.subscribe('filtersChanged', () => {
            this.handleFilterChange();
        });

        this.stateManager.subscribe('dateRangeChanged', () => {
            this.handleDateRangeChange();
        });

        // Filters cleared — single reload instead of three
        this.stateManager.subscribe('filtersReset', () => {
            this.refreshAllData();
        });

        // Manual refresh
        this.stateManager.subscribe('manualRefresh', () => {
            this.handleManualRefresh();
        });

        // Page change (pagination)
        this.stateManager.subscribe('pageChange', async (data) => {
            await this.refreshSelectedSystemData();
        });

        // AI panel toggle functionality
        document.addEventListener('click', (e) => {
            const panelHeader = e.target.closest('.ai-panel-header');
            if (panelHeader) {
                const panel = panelHeader.closest('.ai-panel');
                if (panel) {
                    panel.classList.toggle('collapsed');
                }
            }
        });

        // Track user interaction to pause auto-refresh (Requirement 5.5)
        document.addEventListener('mousedown', () => {
            this.isUserInteracting = true;
        });

        document.addEventListener('mouseup', () => {
            setTimeout(() => {
                this.isUserInteracting = false;
            }, 1000); // Resume auto-refresh 1 second after interaction ends
        });

        document.addEventListener('keydown', () => {
            this.isUserInteracting = true;
        });

        document.addEventListener('keyup', () => {
            setTimeout(() => {
                this.isUserInteracting = false;
            }, 1000);
        });

        // Network connectivity monitoring (Requirement 8.4)
        window.addEventListener('online', () => {
            console.log('Network connection restored');
            this.uiManager.showNotification('Connection restored', 'success');
            this.refreshAllData();
        });

        window.addEventListener('offline', () => {
            console.log('Network connection lost');
            this.uiManager.showNotification('No internet connection', 'error');
        });
    }

    /**
     * Refresh all dashboard data
     */
    async refreshAllData() {
        try {
            this.uiManager.renderLoadingState('system-overview');

            // Run overview and selected-system data in parallel when possible
            const selectedSystem = this.stateManager.getSelectedSystem();
            if (selectedSystem) {
                await Promise.all([
                    this.refreshSystemOverview(),
                    this.refreshSelectedSystemData()
                ]);
            } else {
                await this.refreshSystemOverview();
            }

            this.stateManager.updateLastRefreshTime();
            this.uiManager.updateLastRefreshTime(this.stateManager.getLastRefreshTime());
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Refresh system overview data
     */
    async refreshSystemOverview() {
        try {
            // Get date range from state
            const dateRange = this.stateManager.getDateRange();
            const dateRangeParams = {};
            if (dateRange.startDate && dateRange.endDate) {
                dateRangeParams.start_date = dateRange.startDate.toISOString().split('T')[0];
                dateRangeParams.end_date = dateRange.endDate.toISOString().split('T')[0];
            }

            // Fetch today's summary and bulk SLA data in parallel (2 requests instead of N×2+1)
            const [todaySummary, slaSummary] = await Promise.all([
                this.apiClient.getSystemsSummary({}),
                this.apiClient.getAllSystemsSLASummary(30)
            ]);

            // If date range active, fetch range summary too (still just 1 extra request)
            let rangeSummary = null;
            if (dateRangeParams.start_date) {
                rangeSummary = await this.apiClient.getSystemsSummary(dateRangeParams);
            }

            // Merge summaries with bulk SLA data — no per-system loops
            const mergedSummary = todaySummary.map(todaySystem => {
                const systemId = todaySystem.source_system_id;
                const rangeSystem = rangeSummary ? rangeSummary.find(s => s.source_system_id === systemId) : null;
                const slaData = slaSummary[systemId] || {};

                return {
                    ...todaySystem,
                    file_count_today: todaySystem.file_count,
                    file_count_range: rangeSystem ? rangeSystem.file_count : null,
                    sla_score: slaData.sla_score ?? null,
                    worst_severity: slaData.worst_severity ?? null,
                };
            });

            const filters = this.stateManager.getFilters();
            this.uiManager.renderSystemOverview(mergedSummary, filters.severity || null);
        } catch (error) {
            console.error('Failed to refresh system overview:', error);
            this.handleError(error);
        }
    }

    /**
     * Refresh data for the selected system
     */
    async refreshSelectedSystemData() {
        const selectedSystem = this.stateManager.getSelectedSystem();
        if (!selectedSystem) return;

        try {
            const dateRange = this.stateManager.getDateRange();
            const filters = this.stateManager.getFilters();

            const apiFilters = {
                source_system_id: selectedSystem,
                start_date: dateRange.startDate ? dateRange.startDate.toISOString().split('T')[0] : null,
                end_date: dateRange.endDate ? dateRange.endDate.toISOString().split('T')[0] : null,
                ...filters
            };

            this.uiManager.renderLoadingState('file-arrivals');
            this.uiManager.renderLoadingState('sla-metrics');

            // Fetch file arrivals, SLA score, and violations in parallel
            const [fileArrivals, slaScores, slaViolations] = await Promise.all([
                this.apiClient.getFileArrivals(apiFilters),
                this.apiClient.getAverageSLAScore(selectedSystem),
                this.apiClient.getSLAViolations(apiFilters)
            ]);

            this.uiManager.renderFileArrivals(fileArrivals);
            this.uiManager.renderSLAMetrics(slaScores, slaViolations);

            // Charts are independent — fetch in parallel too
            await this.renderCharts(selectedSystem);
        } catch (error) {
            console.error('Failed to refresh selected system data:', error);
            this.handleError(error);
        }
    }

    /**
     * Render charts for the selected system
     */
    async renderCharts(systemId) {
        try {
            const dateRange = this.stateManager.getDateRange();
            let days = 30;
            if (dateRange.startDate && dateRange.endDate) {
                days = Math.max(7, Math.ceil((dateRange.endDate - dateRange.startDate) / (1000 * 60 * 60 * 24)));
            }

            const [dailyTrends, movingAverage, hourlyPatterns] = await Promise.all([
                this.apiClient.getDailyTrends(systemId, days).catch(() => []),
                this.apiClient.getMovingAverage(systemId, days).catch(() => []),
                this.apiClient.getHourlyPatterns(systemId, Math.max(days, 7)).catch(() => [])
            ]);

            if (dailyTrends.length > 0) {
                this.chartRenderer.createDailyTrendChart('daily-trend-chart', {
                    sourceSystemId: systemId,
                    dataPoints: dailyTrends.map(p => ({ timestamp: p.arrival_date || p.date, value: p.file_count || 0 })),
                    aggregationType: 'daily'
                });
            }

            if (movingAverage.length > 0) {
                this.chartRenderer.createMovingAverageChart('moving-average-chart', {
                    sourceSystemId: systemId,
                    dataPoints: movingAverage.map(p => ({ timestamp: p.date || p.arrival_date, value: p.moving_avg_7day || 0 })),
                    aggregationType: 'moving_average'
                });
            }

            if (hourlyPatterns.length > 0) {
                this.chartRenderer.createHourlyPatternChart('hourly-pattern-chart', {
                    sourceSystemId: systemId,
                    dataPoints: hourlyPatterns.map(p => {
                        const d = new Date();
                        d.setHours(p.hour_of_day || 0, 0, 0, 0);
                        return { timestamp: d.toISOString(), value: p.file_count || 0 };
                    }),
                    aggregationType: 'hourly'
                });
            }
        } catch (error) {
            console.error('Failed to render charts:', error);
        }
    }

    /**
     * Start auto-refresh with 30-second interval
     * Requirements: 5.1, 5.5
     */
    startAutoRefresh() {
        // Clear any existing interval
        this.stopAutoRefresh();

        console.log(`Starting auto-refresh with ${this.config.refreshInterval}ms interval`);

        this.autoRefreshInterval = setInterval(() => {
            // Pause auto-refresh during user interaction (Requirement 5.5)
            if (this.isUserInteracting) {
                console.log('Auto-refresh paused due to user interaction');
                return;
            }

            console.log('Auto-refresh triggered');
            this.refreshAllData();
        }, this.config.refreshInterval);

        this.stateManager.setAutoRefreshEnabled(true);
    }

    /**
     * Stop auto-refresh
     * Requirements: 5.1
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            this.stateManager.setAutoRefreshEnabled(false);
            console.log('Auto-refresh stopped');
        }
    }

    /**
     * Handle system selection event
     */
    async handleSystemSelection(systemId) {
        try {
            const detailsSection = document.getElementById('details-section');
            const aiInsightsSection = document.getElementById('ai-insights-section');

            if (systemId) {
                detailsSection?.classList.remove('hidden');
                aiInsightsSection?.classList.remove('hidden');
            } else {
                detailsSection?.classList.add('hidden');
                aiInsightsSection?.classList.add('hidden');
                this.aiInsightsManager.clear();
            }

            this.chartRenderer.destroyAllCharts();

            // Re-render cards (uses cached data — no new API call needed)
            await this.refreshSystemOverview();

            if (systemId) {
                // Fetch detail data and kick off AI insights in parallel
                await this.refreshSelectedSystemData();
                this.loadAIInsights(systemId); // non-blocking
            }
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Handle filter change event
     * Requirements: 6.2, 6.4
     */
    async handleFilterChange() {
        console.log('Filters changed');

        try {
            // Refresh system overview so severity filter affects the cards grid
            await this.refreshSystemOverview();
            // Refresh selected system data with new filters
            await this.refreshSelectedSystemData();
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Handle date range change event
     * Refreshes both system data and AI insights
     */
    async handleDateRangeChange() {
        console.log('Date range changed');

        try {
            const selectedSystem = this.stateManager.getSelectedSystem();
            
            // Refresh system overview with new date range
            await this.refreshSystemOverview();
            
            // Refresh selected system data if any
            if (selectedSystem) {
                await this.refreshSelectedSystemData();
                
                // Reload AI insights with new date range
                this.loadAIInsights(selectedSystem);
            }
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * Load AI insights for the selected system
     * Non-blocking operation that runs in the background
     * @param {string} systemId - Source system identifier
     */
    async loadAIInsights(systemId) {
        try {
            // Immediately clear stale content from the previous system
            this.aiInsightsManager.clear();

            const dateRange = this.stateManager.getDateRange();
            
            // If no date range is set, use last 7 days as default
            let startDate, endDate;
            
            if (dateRange.startDate && dateRange.endDate) {
                // Convert Date objects to YYYY-MM-DD strings
                startDate = dateRange.startDate.toISOString().split('T')[0];
                endDate = dateRange.endDate.toISOString().split('T')[0];
            } else {
                // Default to last 7 days
                const today = new Date();
                const sevenDaysAgo = new Date(today);
                sevenDaysAgo.setDate(today.getDate() - 7);
                
                startDate = sevenDaysAgo.toISOString().split('T')[0];
                endDate = today.toISOString().split('T')[0];
                
                console.log(`No date range selected, using default: ${startDate} to ${endDate}`);
            }
            
            // Load AI insights asynchronously without blocking the UI
            await this.aiInsightsManager.loadInsights(
                systemId,
                startDate,
                endDate
            );
            
            console.log('AI insights loaded successfully');
        } catch (error) {
            console.error('Failed to load AI insights:', error);
            // Don't throw - AI insights are supplementary and shouldn't break the app
        }
    }

    /**
     * Handle manual refresh button click
     * Requirements: 5.4
     */
    async handleManualRefresh() {
        console.log('Manual refresh triggered');

        try {
            // Disable refresh button temporarily
            const refreshBtn = document.getElementById('manual-refresh');
            if (refreshBtn) {
                refreshBtn.disabled = true;
            }

            // Refresh all data
            await this.refreshAllData();

            // Show success notification
            this.uiManager.showNotification('Data refreshed successfully', 'success');

            // Re-enable refresh button
            if (refreshBtn) {
                refreshBtn.disabled = false;
            }
        } catch (error) {
            this.handleError(error);

            // Re-enable refresh button on error
            const refreshBtn = document.getElementById('manual-refresh');
            if (refreshBtn) {
                refreshBtn.disabled = false;
            }
        }
    }

    /**
     * Handle errors with logging and user feedback
     * Requirements: 8.1, 8.6
     */
    handleError(error) {
        // Log error to console (Requirement 8.6)
        console.error('Dashboard error:', error);

        // Log stack trace if available
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }

        // Display user-friendly error message (Requirement 8.1)
        this.uiManager.renderErrorMessage(error);

        // Show notification
        const errorMessage = error instanceof Error ? error.message : String(error);
        this.uiManager.showNotification(errorMessage, 'error');
    }

    /**
     * Start the application
     */
    start() {
        console.log('Starting Dashboard Application...');
        this.initialize().catch(error => {
            console.error('Failed to start application:', error);
        });
    }

    /**
     * Stop the application and clean up resources
     */
    stop() {
        console.log('Stopping Dashboard Application...');
        this.stopAutoRefresh();
        this.chartRenderer.destroyAllCharts();
        this.apiClient.clearCache();
        this.stateManager.clearCache();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM ready - Initializing Dashboard Application');
    
    const app = new DashboardApp();
    app.start();

    // Make app globally accessible for debugging
    window.dashboardApp = app;
});
