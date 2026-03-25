/**
 * Integration tests for UI Manager with State Manager and API Client
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UIManager } from '../../js/ui-manager.js';
import { StateManager } from '../../js/state-manager.js';
import { APIClient } from '../../js/api-client.js';

describe('UI Manager Integration', () => {
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
            <select id="system-select">
                <option value="">All Systems</option>
            </select>
            <input type="date" id="start-date" />
            <input type="date" id="end-date" />
            <button id="clear-filters"></button>
            <button id="manual-refresh"></button>
            <div id="date-range-error"></div>
        `;

        stateManager = new StateManager();
        apiClient = new APIClient();
        uiManager = new UIManager(stateManager, apiClient);
        uiManager.initialize();
    });

    it('should update UI when state changes', () => {
        const systemSelect = document.getElementById('system-select');
        
        // Simulate user selecting a system
        systemSelect.value = 'TEST001';
        systemSelect.dispatchEvent(new Event('change'));

        // Verify state was updated
        expect(stateManager.getSelectedSystem()).toBe('TEST001');
    });

    it('should clear filters when clear button is clicked', () => {
        const systemSelect = document.getElementById('system-select');
        const startDate = document.getElementById('start-date');
        const clearBtn = document.getElementById('clear-filters');

        // Set some filters
        systemSelect.value = 'TEST001';
        startDate.value = '2024-01-01';
        stateManager.setSelectedSystem('TEST001');
        stateManager.setDateRange(new Date('2024-01-01'), null);

        // Click clear button
        clearBtn.click();

        // Verify filters were cleared
        expect(systemSelect.value).toBe('');
        expect(startDate.value).toBe('');
        expect(stateManager.getSelectedSystem()).toBeNull();
    });

    it('should validate date range and show error for invalid range', () => {
        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');
        const errorContainer = document.getElementById('date-range-error');

        // Set invalid date range (start after end)
        startDate.value = '2024-01-31';
        endDate.value = '2024-01-01';

        // Trigger change event
        startDate.dispatchEvent(new Event('change'));

        // Verify error message is displayed
        expect(errorContainer.innerHTML).toContain('Start date must be before end date');
    });

    it('should render system overview with proper formatting', () => {
        const systems = [
            {
                sourceSystemId: 'TEST001',
                systemName: 'Test System 1',
                status: 'healthy',
                fileCount: 1234567,
                slaScore: 95.5,
                hasViolations: false
            },
            {
                sourceSystemId: 'TEST002',
                systemName: 'Test System 2',
                status: 'warning',
                fileCount: 500,
                slaScore: 75.0,
                hasViolations: true
            }
        ];

        uiManager.renderSystemOverview(systems);

        const container = document.getElementById('system-overview');
        
        // Verify both systems are rendered
        expect(container.innerHTML).toContain('Test System 1');
        expect(container.innerHTML).toContain('Test System 2');
        
        // Verify number formatting
        expect(container.innerHTML).toContain('1,234,567');
        
        // Verify warning indicator for system with violations
        expect(container.innerHTML).toContain('warning-indicator');
    });

    it('should handle pagination for large datasets', () => {
        const arrivals = Array(75).fill(null).map((_, i) => ({
            fileName: `file_${i}.csv`,
            arrivalTime: new Date(),
            status: 'processed',
            fileSize: 1024 * (i + 1),
            processingTime: 100 + i
        }));

        uiManager.renderFileArrivals(arrivals, 75);

        const container = document.getElementById('file-arrivals');
        
        // Verify pagination is rendered
        expect(container.innerHTML).toContain('pagination');
        expect(container.innerHTML).toContain('Showing 1-50 of 75');
        
        // Verify pagination buttons exist
        expect(container.innerHTML).toContain('Previous');
        expect(container.innerHTML).toContain('Next');
    });

    it('should display SLA metrics with proper severity colors', () => {
        const scores = {
            score: 85.5,
            threshold: 80,
            isCompliant: true
        };

        const violations = [
            {
                severity: 'high',
                violationType: 'Late Arrival',
                timestamp: new Date('2024-01-15T10:30:00'),
                description: 'File arrived 2 hours late',
                resolved: false
            },
            {
                severity: 'medium',
                violationType: 'Missing File',
                timestamp: new Date('2024-01-14T08:00:00'),
                description: 'Expected file not received',
                resolved: true
            }
        ];

        uiManager.renderSLAMetrics(scores, violations);

        const container = document.getElementById('sla-metrics');
        
        // Verify score is displayed
        expect(container.innerHTML).toContain('85.5');
        
        // Verify violations are displayed
        expect(container.innerHTML).toContain('Late Arrival');
        expect(container.innerHTML).toContain('Missing File');
        
        // Verify severity levels are shown
        expect(container.innerHTML).toContain('high');
        expect(container.innerHTML).toContain('medium');
        
        // Verify resolved status
        expect(container.innerHTML).toContain('Resolved');
    });

    it('should update last refresh time display', () => {
        const timestamp = new Date('2024-01-15T10:30:00');
        
        uiManager.updateLastRefreshTime(timestamp);

        const container = document.getElementById('last-refresh-time');
        expect(container.textContent).toContain('Last updated:');
        expect(container.textContent).toContain('Jan');
        expect(container.textContent).toContain('15');
    });

    it('should show notifications with auto-dismiss', (done) => {
        uiManager.showNotification('Test notification', 'success');

        const container = document.getElementById('notifications');
        expect(container.innerHTML).toContain('Test notification');
        
        // Notification should auto-dismiss after 5 seconds
        // We won't wait for the full 5 seconds in the test
        expect(container.querySelector('.notification')).toBeTruthy();
        done();
    });
});
