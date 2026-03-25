/**
 * Unit tests for DashboardApp
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { DashboardApp } from '../../js/app.js';

describe('DashboardApp', () => {
    let app;

    beforeEach(() => {
        // Mock DOM elements
        document.body.innerHTML = `
            <div id="system-overview"></div>
            <div id="file-arrivals"></div>
            <div id="sla-metrics"></div>
            <div id="error-banner"></div>
            <div id="notifications"></div>
            <div id="last-refresh-time"></div>
            <select id="system-select"></select>
            <input id="start-date" type="date" />
            <input id="end-date" type="date" />
            <button id="clear-filters"></button>
            <button id="manual-refresh"></button>
            <canvas id="daily-trend-chart"></canvas>
            <canvas id="moving-average-chart"></canvas>
            <canvas id="hourly-pattern-chart"></canvas>
        `;

        // Mock fetch for config loading
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
            return Promise.reject(new Error('Not found'));
        });

        app = new DashboardApp();
    });

    afterEach(() => {
        if (app) {
            app.stop();
        }
        vi.restoreAllMocks();
    });

    describe('Constructor', () => {
        it('should create a DashboardApp instance', () => {
            expect(app).toBeDefined();
            expect(app.config).toBeNull();
            expect(app.apiClient).toBeNull();
            expect(app.stateManager).toBeNull();
            expect(app.uiManager).toBeNull();
            expect(app.chartRenderer).toBeNull();
        });
    });

    describe('loadConfig', () => {
        it('should load configuration from config.json', async () => {
            await app.loadConfig();
            
            expect(app.config).toBeDefined();
            expect(app.config.apiBaseURL).toBe('http://localhost:8000');
            expect(app.config.refreshInterval).toBe(30000);
        });

        it('should use default config if loading fails', async () => {
            global.fetch = vi.fn(() => Promise.reject(new Error('Failed to load')));
            
            await app.loadConfig();
            
            expect(app.config).toBeDefined();
            expect(app.config.apiBaseURL).toBe('http://localhost:8000');
            expect(app.config.refreshInterval).toBe(30000);
        });
    });

    describe('initialize', () => {
        it('should initialize all components', async () => {
            // Mock API calls
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
                if (url.includes('/api/v1/trends/summary')) {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve([])
                    });
                }
                return Promise.reject(new Error('Not found'));
            });

            await app.initialize();

            expect(app.config).toBeDefined();
            expect(app.apiClient).toBeDefined();
            expect(app.stateManager).toBeDefined();
            expect(app.uiManager).toBeDefined();
            expect(app.chartRenderer).toBeDefined();
        });
    });

    describe('Auto-refresh', () => {
        it('should start auto-refresh', async () => {
            await app.loadConfig();
            app.stateManager = { setAutoRefreshEnabled: vi.fn() };
            
            app.startAutoRefresh();
            
            expect(app.autoRefreshInterval).toBeDefined();
            expect(app.stateManager.setAutoRefreshEnabled).toHaveBeenCalledWith(true);
        });

        it('should stop auto-refresh', async () => {
            await app.loadConfig();
            app.stateManager = { setAutoRefreshEnabled: vi.fn() };
            
            app.startAutoRefresh();
            app.stopAutoRefresh();
            
            expect(app.autoRefreshInterval).toBeNull();
            expect(app.stateManager.setAutoRefreshEnabled).toHaveBeenCalledWith(false);
        });
    });

    describe('Error handling', () => {
        it('should handle errors with logging', () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
            const error = new Error('Test error');
            
            app.uiManager = {
                renderErrorMessage: vi.fn(),
                showNotification: vi.fn()
            };
            
            app.handleError(error);
            
            expect(consoleSpy).toHaveBeenCalledWith('Dashboard error:', error);
            expect(app.uiManager.renderErrorMessage).toHaveBeenCalledWith(error);
            expect(app.uiManager.showNotification).toHaveBeenCalledWith('Test error', 'error');
            
            consoleSpy.mockRestore();
        });

        it('should log stack trace if available', () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
            const error = new Error('Test error');
            error.stack = 'Stack trace here';
            
            app.uiManager = {
                renderErrorMessage: vi.fn(),
                showNotification: vi.fn()
            };
            
            app.handleError(error);
            
            expect(consoleSpy).toHaveBeenCalledWith('Stack trace:', 'Stack trace here');
            
            consoleSpy.mockRestore();
        });
    });

    describe('Event handlers', () => {
        it('should handle system selection', async () => {
            app.chartRenderer = { destroyAllCharts: vi.fn() };
            app.refreshSelectedSystemData = vi.fn().mockResolvedValue(undefined);
            
            await app.handleSystemSelection('TEST001');
            
            expect(app.chartRenderer.destroyAllCharts).toHaveBeenCalled();
            expect(app.refreshSelectedSystemData).toHaveBeenCalled();
        });

        it('should handle filter change', async () => {
            app.refreshSelectedSystemData = vi.fn().mockResolvedValue(undefined);
            
            await app.handleFilterChange();
            
            expect(app.refreshSelectedSystemData).toHaveBeenCalled();
        });

        it('should handle manual refresh', async () => {
            app.refreshAllData = vi.fn().mockResolvedValue(undefined);
            app.uiManager = { showNotification: vi.fn() };
            
            await app.handleManualRefresh();
            
            expect(app.refreshAllData).toHaveBeenCalled();
            expect(app.uiManager.showNotification).toHaveBeenCalledWith('Data refreshed successfully', 'success');
        });
    });

    describe('Lifecycle', () => {
        it('should stop the application and clean up resources', async () => {
            await app.loadConfig();
            app.apiClient = { clearCache: vi.fn() };
            app.stateManager = { clearCache: vi.fn(), setAutoRefreshEnabled: vi.fn() };
            app.chartRenderer = { destroyAllCharts: vi.fn() };
            app.startAutoRefresh();
            
            app.stop();
            
            expect(app.autoRefreshInterval).toBeNull();
            expect(app.chartRenderer.destroyAllCharts).toHaveBeenCalled();
            expect(app.apiClient.clearCache).toHaveBeenCalled();
            expect(app.stateManager.clearCache).toHaveBeenCalled();
        });
    });
});
