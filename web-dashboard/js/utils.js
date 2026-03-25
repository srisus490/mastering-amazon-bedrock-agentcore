/**
 * Utility Functions
 * Common helper functions used across the application
 */

/**
 * Format a number with thousand separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
export function formatNumber(num) {
    return num.toLocaleString();
}

/**
 * Format a date to a readable string
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 */
export function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleString();
}

/**
 * Get color for severity level
 * @param {string} severity - Severity level (high, medium, low)
 * @returns {string} CSS color value
 */
export function getSeverityColor(severity) {
    const colors = {
        high: '#ef4444',
        medium: '#f97316',
        low: '#3b82f6'
    };
    return colors[severity] || '#6b7280';
}

/**
 * Get color for system status
 * @param {string} status - Status (healthy, warning, critical)
 * @returns {string} CSS color value
 */
export function getStatusColor(status) {
    const colors = {
        healthy: '#10b981',
        warning: '#f59e0b',
        critical: '#ef4444'
    };
    return colors[status] || '#6b7280';
}
