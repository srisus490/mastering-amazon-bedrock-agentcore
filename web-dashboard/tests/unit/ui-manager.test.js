/**
 * Unit tests for UI Manager
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UIManager } from '../../js/ui-manager.js';
import { StateManager } from '../../js/state-manager.js';
import { APIClient } from '../../js/api-client.js';

describe('UIManager', () => {
    let uiManager;
    let stateManager;
    let apiClient;

    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div id="system-overview"></div>
            <div id="file-arrivals"></div>
            <div id="sla-metrics"></div>
            <div id="error-banner"></div>
            <div id="notifications"></div>
            <div id="last-refresh-time"></div>
            <select id="system-select"></select>
            <input type="date" id="start-date" />
            <input type="date" id="end-date" />
            <button id="clear-filters"></button>
            <button id="manual-refresh"></button>
            <div id="date-range-error"></div>
        `;

        stateManager = new StateManager();
        apiClient = new APIClient();
        uiManager = new UIManager(stateManager, apiClient);
    });

    describe('Constructor', () => {
        it('should initialize with stateManager and apiClient', () => {
            expect(uiManager.stateManager).toBe(stateManager);
            expect(uiManager.apiClient).toBe(apiClient);
        });

        it('should initialize pagination properties', () => {
            expect(uiManager.currentPage).toBe(1);
            expect(uiManager.pageSize).toBe(50);
        });
    });

    describe('renderSystemOverview', () => {
        it('should render system cards with all required fields', () => {
            const systems = [
                {
                    sourceSystemId: 'TEST001',
                    systemName: 'Test System',
                    status: 'healthy',
                    fileCount: 1234,
                    slaScore: 95.5,
                    hasViolations: false
                }
            ];

            uiManager.renderSystemOverview(systems);

            const container = document.getElementById('system-overview');
            expect(container.innerHTML).toContain('Test System');
            expect(container.innerHTML).toContain('1,234');
            expect(container.innerHTML).toContain('95.5');
            expect(container.innerHTML).toContain('healthy');
        });

        it('should show warning indicator for systems with violations', () => {
            const systems = [
                {
                    sourceSystemId: 'TEST001',
                    systemName: 'Test System',
                    status: 'warning',
                    fileCount: 100,
                    slaScore: 75,
                    hasViolations: true
                }
            ];

            uiManager.renderSystemOverview(systems);

            const container = document.getElementById('system-overview');
            expect(container.innerHTML).toContain('warning-indicator');
            expect(container.innerHTML).toContain('⚠️');
        });

        it('should show warning indicator for systems with SLA score < 80', () => {
            const systems = [
                {
                    sourceSystemId: 'TEST001',
                    systemName: 'Test System',
                    status: 'healthy',
                    fileCount: 100,
                    slaScore: 75,
                    hasViolations: false
                }
            ];

            uiManager.renderSystemOverview(systems);

            const container = document.getElementById('system-overview');
            expect(container.innerHTML).toContain('warning-indicator');
        });

        it('should display "No systems found" when systems array is empty', () => {
            uiManager.renderSystemOverview([]);

            const container = document.getElementById('system-overview');
            expect(container.innerHTML).toContain('No systems found');
        });
    });

    describe('renderFileArrivals', () => {
        it('should render file arrivals table with all required fields', () => {
            const arrivals = [
                {
                    fileName: 'test.csv',
                    arrivalTime: new Date('2024-01-15T10:30:00'),
                    status: 'processed',
                    fileSize: 1024000,
                    processingTime: 150
                }
            ];

            uiManager.renderFileArrivals(arrivals);

            const container = document.getElementById('file-arrivals');
            expect(container.innerHTML).toContain('test.csv');
            expect(container.innerHTML).toContain('processed');
            expect(container.innerHTML).toContain('150ms');
        });

        it('should render pagination when total count exceeds page size', () => {
            const arrivals = Array(10).fill({
                fileName: 'test.csv',
                arrivalTime: new Date(),
                status: 'processed',
                fileSize: 1024,
                processingTime: 100
            });

            uiManager.renderFileArrivals(arrivals, 100);

            const container = document.getElementById('file-arrivals');
            expect(container.innerHTML).toContain('pagination');
            expect(container.innerHTML).toContain('Showing');
        });

        it('should display "No file arrivals found" when arrivals array is empty', () => {
            uiManager.renderFileArrivals([]);

            const container = document.getElementById('file-arrivals');
            expect(container.innerHTML).toContain('No file arrivals found');
        });
    });

    describe('renderSLAMetrics', () => {
        it('should render SLA score with all required fields', () => {
            const scores = {
                score: 95.5,
                threshold: 80,
                isCompliant: true
            };

            uiManager.renderSLAMetrics(scores, []);

            const container = document.getElementById('sla-metrics');
            expect(container.innerHTML).toContain('95.5');
            expect(container.innerHTML).toContain('Threshold: 80');
            expect(container.innerHTML).toContain('Compliant');
        });

        it('should show warning indicator when SLA score < 80', () => {
            const scores = {
                score: 75,
                threshold: 80,
                isCompliant: false
            };

            uiManager.renderSLAMetrics(scores, []);

            const container = document.getElementById('sla-metrics');
            expect(container.innerHTML).toContain('warning-indicator');
            expect(container.innerHTML).toContain('⚠️');
        });

        it('should render violations with severity colors', () => {
            const violations = [
                {
                    severity: 'high',
                    violationType: 'Late Arrival',
                    timestamp: new Date('2024-01-15T10:30:00'),
                    description: 'File arrived 2 hours late',
                    resolved: false
                }
            ];

            uiManager.renderSLAMetrics({}, violations);

            const container = document.getElementById('sla-metrics');
            expect(container.innerHTML).toContain('high');
            expect(container.innerHTML).toContain('Late Arrival');
            expect(container.innerHTML).toContain('File arrived 2 hours late');
        });
    });

    describe('renderErrorMessage', () => {
        it('should render error message with guidance', () => {
            uiManager.renderErrorMessage('Network error occurred');

            const container = document.getElementById('error-banner');
            expect(container.innerHTML).toContain('Network error occurred');
            expect(container.innerHTML).toContain('error-message');
        });

        it('should provide actionable guidance for network errors', () => {
            uiManager.renderErrorMessage('Network fetch failed');

            const container = document.getElementById('error-banner');
            expect(container.innerHTML).toContain('http://localhost:8000');
        });
    });

    describe('Utility Methods', () => {
        describe('formatNumber', () => {
            it('should format numbers with thousand separators', () => {
                expect(uiManager.formatNumber(1000)).toBe('1,000');
                expect(uiManager.formatNumber(1234567)).toBe('1,234,567');
                expect(uiManager.formatNumber(100)).toBe('100');
            });

            it('should return "N/A" for null or undefined', () => {
                expect(uiManager.formatNumber(null)).toBe('N/A');
                expect(uiManager.formatNumber(undefined)).toBe('N/A');
            });
        });

        describe('formatDate', () => {
            it('should format dates to readable strings', () => {
                const date = new Date('2024-01-15T10:30:00');
                const formatted = uiManager.formatDate(date);
                expect(formatted).toContain('Jan');
                expect(formatted).toContain('15');
                expect(formatted).toContain('2024');
            });

            it('should return "N/A" for null or undefined', () => {
                expect(uiManager.formatDate(null)).toBe('N/A');
                expect(uiManager.formatDate(undefined)).toBe('N/A');
            });
        });

        describe('getSeverityColor', () => {
            it('should return correct colors for severity levels', () => {
                expect(uiManager.getSeverityColor('high')).toBe('#dc3545');
                expect(uiManager.getSeverityColor('medium')).toBe('#fd7e14');
                expect(uiManager.getSeverityColor('low')).toBe('#0dcaf0');
                expect(uiManager.getSeverityColor('healthy')).toBe('#198754');
            });

            it('should return default color for unknown severity', () => {
                expect(uiManager.getSeverityColor('unknown')).toBe('#6c757d');
            });
        });

        describe('formatFileSize', () => {
            it('should format file sizes correctly', () => {
                expect(uiManager.formatFileSize(0)).toBe('0 Bytes');
                expect(uiManager.formatFileSize(1024)).toBe('1 KB');
                expect(uiManager.formatFileSize(1048576)).toBe('1 MB');
                expect(uiManager.formatFileSize(1073741824)).toBe('1 GB');
            });

            it('should return "N/A" for null or undefined', () => {
                expect(uiManager.formatFileSize(null)).toBe('N/A');
                expect(uiManager.formatFileSize(undefined)).toBe('N/A');
            });
        });

        describe('escapeHtml', () => {
            it('should escape HTML special characters', () => {
                expect(uiManager.escapeHtml('<script>alert("xss")</script>'))
                    .toBe('&lt;script&gt;alert("xss")&lt;/script&gt;');
            });

            it('should return empty string for null or undefined', () => {
                expect(uiManager.escapeHtml(null)).toBe('');
                expect(uiManager.escapeHtml(undefined)).toBe('');
            });
        });
    });

    describe('clearFilters', () => {
        it('should reset all filter inputs', () => {
            const systemSelect = document.getElementById('system-select');
            const startDate = document.getElementById('start-date');
            const endDate = document.getElementById('end-date');

            systemSelect.value = 'TEST001';
            startDate.value = '2024-01-01';
            endDate.value = '2024-01-31';

            uiManager.clearFilters();

            expect(systemSelect.value).toBe('');
            expect(startDate.value).toBe('');
            expect(endDate.value).toBe('');
        });
    });
});
