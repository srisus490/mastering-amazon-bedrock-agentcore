/**
 * Message Formatter
 * Formats data and messages for display in chat
 * 
 * Requirements: 4.2, 4.3, 13.1, 13.2, 13.3, 13.4, 13.5
 */

export class MessageFormatter {
    constructor() {
        console.log('MessageFormatter created');
    }

    /**
     * Format data as HTML table
     * Requirements: 4.2, 13.1
     */
    formatTable(data) {
        if (!data || data.length === 0) {
            return '<p class="no-data">No data available</p>';
        }

        // Get column names from first row
        const columns = Object.keys(data[0]);

        let html = '<div class="chat-table-container"><table class="chat-table">';
        
        // Header
        html += '<thead><tr>';
        columns.forEach(col => {
            html += `<th>${this.formatColumnName(col)}</th>`;
        });
        html += '</tr></thead>';

        // Body
        html += '<tbody>';
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                html += `<td>${this.formatCellValue(col, value)}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';

        html += '</table></div>';

        return html;
    }

    /**
     * Format single metric with highlighting
     * Requirements: 4.3, 13.2
     */
    formatMetric(label, value, unit = '') {
        const formattedValue = this.formatNumber(value);
        return `
            <div class="chat-metric">
                <span class="chat-metric-label">${label}:</span>
                <span class="chat-metric-value">${formattedValue}${unit}</span>
            </div>
        `;
    }

    /**
     * Format list of items
     * Requirements: 13.1
     */
    formatList(items) {
        if (!items || items.length === 0) {
            return '<p class="no-data">No items</p>';
        }

        let html = '<ul class="chat-list">';
        items.forEach(item => {
            html += `<li>${item}</li>`;
        });
        html += '</ul>';

        return html;
    }

    /**
     * Format timestamp consistently
     * Requirements: 4.5, 13.3
     */
    formatTimestamp(date) {
        if (!date) return '';

        const d = date instanceof Date ? date : new Date(date);
        
        // Format as "HH:MM AM/PM"
        const hours = d.getHours();
        const minutes = d.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        const displayHours = hours % 12 || 12;
        const displayMinutes = minutes.toString().padStart(2, '0');

        return `${displayHours}:${displayMinutes} ${ampm}`;
    }

    /**
     * Format date consistently
     * Requirements: 13.3
     */
    formatDate(date) {
        if (!date) return '';

        const d = date instanceof Date ? date : new Date(date);
        
        // Format as "MMM DD, YYYY"
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return d.toLocaleDateString('en-US', options);
    }

    /**
     * Format datetime consistently
     * Requirements: 13.3
     */
    formatDateTime(date) {
        if (!date) return '';

        const d = date instanceof Date ? date : new Date(date);
        
        // Format as "MMM DD, YYYY HH:MM AM/PM"
        return `${this.formatDate(d)} ${this.formatTimestamp(d)}`;
    }

    /**
     * Format number with thousand separators
     * Requirements: 13.4
     */
    formatNumber(value) {
        if (value === null || value === undefined) return '-';
        
        const num = typeof value === 'number' ? value : parseFloat(value);
        
        if (isNaN(num)) return value;

        // Use toLocaleString for thousand separators
        return num.toLocaleString('en-US', {
            maximumFractionDigits: 2
        });
    }

    /**
     * Format percentage with precision
     * Requirements: 13.5
     */
    formatPercentage(value, precision = 1) {
        if (value === null || value === undefined) return '-';
        
        const num = typeof value === 'number' ? value : parseFloat(value);
        
        if (isNaN(num)) return value;

        return `${num.toFixed(precision)}%`;
    }

    /**
     * Format column name (convert snake_case to Title Case)
     * @private
     */
    formatColumnName(name) {
        return name
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Format cell value based on column type
     * @private
     */
    formatCellValue(columnName, value) {
        if (value === null || value === undefined) {
            return '-';
        }

        // Date columns
        if (columnName.includes('date') || columnName.includes('time')) {
            if (columnName.includes('time') || columnName.includes('timestamp')) {
                return this.formatDateTime(value);
            }
            return this.formatDate(value);
        }

        // Percentage columns
        if (columnName.includes('percent') || columnName.includes('score')) {
            return this.formatPercentage(value);
        }

        // Count/number columns
        if (columnName.includes('count') || columnName.includes('total') || 
            columnName.includes('avg') || columnName.includes('average')) {
            return this.formatNumber(value);
        }

        // Default: return as-is
        return value;
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === null || bytes === undefined) return '-';
        
        const num = typeof bytes === 'number' ? bytes : parseFloat(bytes);
        
        if (isNaN(num)) return bytes;

        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = num;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }

    /**
     * Format duration (seconds to human-readable)
     */
    formatDuration(seconds) {
        if (seconds === null || seconds === undefined) return '-';
        
        const num = typeof seconds === 'number' ? seconds : parseFloat(seconds);
        
        if (isNaN(num)) return seconds;

        if (num < 60) {
            return `${num.toFixed(0)}s`;
        } else if (num < 3600) {
            const minutes = Math.floor(num / 60);
            const secs = Math.floor(num % 60);
            return `${minutes}m ${secs}s`;
        } else {
            const hours = Math.floor(num / 3600);
            const minutes = Math.floor((num % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @private
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
