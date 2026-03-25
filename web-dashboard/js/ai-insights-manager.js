/**
 * AI Insights Manager Module
 * Manages AI-powered insights display and interactions
 * 
 * Features:
 * - Smart insights with trends and anomalies
 * - 7-day forecast with Chart.js visualization
 * - Root cause analysis for SLA violations
 * - Loading states and error handling
 * - Graceful degradation when AI unavailable
 */

export class AIInsightsManager {
    constructor(apiClient, uiManager) {
        this.apiClient = apiClient;
        this.uiManager = uiManager;
        this.currentSystemId = null;
        this.currentDateRange = null;
        this.forecastChart = null;
        
        console.log('AIInsightsManager initialized');
    }

    /**
     * Load all three types of insights for a system
     * @param {string} systemId - Source system identifier
     * @param {string} startDate - Start date (YYYY-MM-DD)
     * @param {string} endDate - End date (YYYY-MM-DD)
     */
    async loadInsights(systemId, startDate, endDate) {
        this.currentSystemId = systemId;
        this.currentDateRange = { startDate, endDate };

        console.log(`Loading AI insights for ${systemId} (${startDate} to ${endDate})`);

        // Load all three insights in parallel
        await Promise.all([
            this.loadSmartInsights(systemId, startDate, endDate),
            this.loadForecast(systemId),
            this.loadRootCause(systemId, startDate, endDate)
        ]);
    }

    /**
     * Load and display smart insights
     * @param {string} systemId - Source system identifier
     * @param {string} startDate - Start date (YYYY-MM-DD) or null
     * @param {string} endDate - End date (YYYY-MM-DD) or null
     */
    async loadSmartInsights(systemId, startDate, endDate) {
        const container = document.getElementById('ai-insights-content');
        if (!container) {
            console.warn('AI insights container not found');
            return;
        }

        // Skip if dates are null - AI insights require date range
        if (!startDate || !endDate) {
            console.log('Skipping smart insights - no date range selected');
            container.innerHTML = `
                <div class="ai-info-message">
                    <p>📅 Please select a date range to view AI insights</p>
                </div>
            `;
            return;
        }

        try {
            this.showLoading('insights');
            
            console.log(`Loading smart insights for ${systemId} (${startDate} to ${endDate})`);
            const insights = await this.apiClient.getSmartInsights(systemId, startDate, endDate);
            console.log('Smart insights received:', insights);
            
            this.renderInsights(insights);
            this.hideLoading('insights');
            
        } catch (error) {
            console.error('Failed to load smart insights:', error);
            console.error('Error details:', error.message, error.stack);
            this.handleError(error, 'insights');
        }
    }

    /**
     * Load and display forecast
     * @param {string} systemId - Source system identifier
     */
    async loadForecast(systemId) {
        const container = document.getElementById('ai-forecast-content');
        if (!container) {
            console.warn('AI forecast container not found');
            return;
        }

        try {
            this.showLoading('forecast');
            
            console.log(`Loading forecast for ${systemId}`);
            const forecast = await this.apiClient.getForecast(systemId, 60);
            console.log('Forecast received:', forecast);
            
            this.renderForecast(forecast);
            this.hideLoading('forecast');
            
        } catch (error) {
            console.error('Failed to load forecast:', error);
            console.error('Error details:', error.message, error.stack);
            this.handleError(error, 'forecast');
        }
    }

    /**
     * Load and display root cause analysis
     * @param {string} systemId - Source system identifier
     * @param {string} startDate - Start date (YYYY-MM-DD) or null
     * @param {string} endDate - End date (YYYY-MM-DD) or null
     */
    async loadRootCause(systemId, startDate, endDate) {
        const container = document.getElementById('ai-root-cause-content');
        if (!container) {
            console.warn('AI root cause container not found');
            return;
        }

        // Skip if dates are null - root cause analysis requires date range
        if (!startDate || !endDate) {
            console.log('Skipping root cause analysis - no date range selected');
            container.innerHTML = `
                <div class="ai-info-message">
                    <p>📅 Please select a date range to view root cause analysis</p>
                </div>
            `;
            return;
        }

        try {
            this.showLoading('root-cause');
            
            console.log(`Loading root cause for ${systemId} (${startDate} to ${endDate})`);
            const rootCause = await this.apiClient.getRootCauseAnalysis(systemId, startDate, endDate);
            console.log('Root cause received:', rootCause);
            
            this.renderRootCause(rootCause);
            this.hideLoading('root-cause');
            
        } catch (error) {
            console.error('Failed to load root cause analysis:', error);
            console.error('Error details:', error.message, error.stack);
            this.handleError(error, 'root-cause');
        }
    }

    /**
     * Render smart insights in the UI
     * @param {Object} data - Insights data from API
     */
    renderInsights(data) {
        const container = document.getElementById('ai-insights-content');
        if (!container) {
            console.warn('AI insights container not found');
            return;
        }

        try {
            let html = `
                <div class="ai-insights-summary">
                    <p class="insights-text">${this.escapeHtml(data.insights || 'No insights available')}</p>
                    ${data.cached ? '<span class="cache-badge">Cached</span>' : ''}
                </div>
            `;

            // Render trends
            if (data.trends && data.trends.length > 0) {
                html += '<div class="insights-section"><h4>Trends</h4><ul class="insights-list">';
                data.trends.forEach(trend => {
                    const icon = this.getTrendIcon(trend.type || 'trend');
                    const description = trend.description || 'No description';
                    const confidence = trend.confidence || 'medium';
                    html += `<li class="trend-item trend-${confidence}">
                        ${icon} ${this.escapeHtml(description)}
                        <span class="confidence-badge">${confidence}</span>
                    </li>`;
                });
                html += '</ul></div>';
            }

            // Render anomalies
            if (data.anomalies && data.anomalies.length > 0) {
                html += '<div class="insights-section"><h4>Anomalies</h4><ul class="insights-list">';
                data.anomalies.forEach(anomaly => {
                    const icon = this.getAnomalyIcon(anomaly.severity || 'medium');
                    const description = anomaly.description || 'No description';
                    const severity = anomaly.severity || 'medium';
                    html += `<li class="anomaly-item severity-${severity}">
                        ${icon} ${this.escapeHtml(description)}
                    </li>`;
                });
                html += '</ul></div>';
            } else {
                html += '<div class="insights-section"><p class="no-anomalies">✓ No anomalies detected</p></div>';
            }

            // Render recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                html += '<div class="insights-section"><h4>Recommendations</h4><ol class="recommendations-list">';
                data.recommendations.forEach(rec => {
                    html += `<li>${this.escapeHtml(rec || 'No recommendation')}</li>`;
                });
                html += '</ol></div>';
            }

            container.innerHTML = html;
            console.log('Smart insights rendered successfully');
        } catch (error) {
            console.error('Error rendering insights:', error);
            container.innerHTML = `
                <div class="ai-error">
                    <div class="error-icon">⚠</div>
                    <p>Error displaying insights. Please try again.</p>
                </div>
            `;
        }
    }

    /**
     * Render forecast with Chart.js visualization
     * @param {Object} data - Forecast data from API
     */
    renderForecast(data) {
        const container = document.getElementById('ai-forecast-content');
        if (!container) return;

        // Render summary
        let html = `
            <div class="forecast-summary">
                <p>7-day forecast based on ${data.historical_period.days} days of historical data</p>
                ${data.cached ? '<span class="cache-badge">Cached</span>' : ''}
            </div>
        `;

        // Render patterns if available
        if (data.patterns_identified && data.patterns_identified.length > 0) {
            html += '<div class="forecast-patterns"><h4>Patterns Identified</h4><ul>';
            data.patterns_identified.forEach(pattern => {
                html += `<li>${this.escapeHtml(pattern)}</li>`;
            });
            html += '</ul></div>';
        }

        // Add chart canvas
        html += '<div class="forecast-chart-container"><canvas id="forecast-chart"></canvas></div>';

        // Render predictions table
        html += '<div class="forecast-table"><h4>Predictions</h4><table><thead><tr>';
        html += '<th>Date</th><th>Predicted Count</th><th>Confidence</th><th>Range</th>';
        html += '</tr></thead><tbody>';
        
        data.predictions.forEach(pred => {
            const confidenceClass = `confidence-${pred.confidence_level}`;
            html += `<tr>
                <td>${pred.date}</td>
                <td class="predicted-count">${pred.predicted_count}</td>
                <td><span class="confidence-badge ${confidenceClass}">${pred.confidence_level}</span></td>
                <td>${pred.confidence_range.min} - ${pred.confidence_range.max}</td>
            </tr>`;
        });
        
        html += '</tbody></table></div>';

        container.innerHTML = html;

        // Render chart
        this.renderForecastChart(data.predictions);
    }

    /**
     * Render forecast chart using Chart.js
     * @param {Array} predictions - Prediction data
     */
    renderForecastChart(predictions) {
        const canvas = document.getElementById('forecast-chart');
        if (!canvas) return;

        // Destroy existing chart if any
        if (this.forecastChart) {
            this.forecastChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        // Prepare data
        const labels = predictions.map(p => p.date);
        const counts = predictions.map(p => p.predicted_count);
        const mins = predictions.map(p => p.confidence_range.min);
        const maxs = predictions.map(p => p.confidence_range.max);

        this.forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Predicted Count',
                        data: counts,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Confidence Range (Min)',
                        data: mins,
                        borderColor: '#FFC107',
                        backgroundColor: 'transparent',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0
                    },
                    {
                        label: 'Confidence Range (Max)',
                        data: maxs,
                        borderColor: '#FFC107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: '-1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '7-Day File Arrival Forecast'
                    },
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'File Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    /**
     * Render root cause analysis
     * @param {Object} data - Root cause data from API
     */
    renderRootCause(data) {
        const container = document.getElementById('ai-root-cause-content');
        if (!container) return;

        let html = `
            <div class="root-cause-summary">
                <p><strong>${data.violations_analyzed}</strong> violations analyzed</p>
                ${data.cached ? '<span class="cache-badge">Cached</span>' : ''}
            </div>
        `;

        // If no violations, show healthy status
        if (data.violations_analyzed === 0) {
            html += `
                <div class="healthy-status">
                    <div class="status-icon">✓</div>
                    <h4>System Healthy</h4>
                    <p>No SLA violations detected in the selected period.</p>
                </div>
            `;
        } else {
            // Render root causes
            if (data.root_causes && data.root_causes.length > 0) {
                html += '<div class="root-cause-section"><h4>Root Causes</h4><ul class="root-cause-list">';
                data.root_causes.forEach(cause => {
                    html += `<li class="cause-item confidence-${cause.confidence}">
                        <div class="cause-title">${this.escapeHtml(cause.cause)}</div>
                        <div class="cause-description">${this.escapeHtml(cause.description)}</div>
                        <span class="confidence-badge">${cause.confidence}</span>
                    </li>`;
                });
                html += '</ul></div>';
            }

            // Render correlations
            if (data.correlations && data.correlations.length > 0) {
                html += '<div class="root-cause-section"><h4>Correlations</h4><ul class="correlation-list">';
                data.correlations.forEach(corr => {
                    html += `<li class="correlation-item strength-${corr.strength}">
                        ${this.escapeHtml(corr.pattern)}
                        <span class="strength-badge">${corr.strength}</span>
                    </li>`;
                });
                html += '</ul></div>';
            }
        }

        // Render remediation actions (always show)
        if (data.remediation_actions && data.remediation_actions.length > 0) {
            html += '<div class="root-cause-section"><h4>Remediation Actions</h4><ol class="remediation-list">';
            data.remediation_actions.forEach(action => {
                html += `<li>${this.escapeHtml(action)}</li>`;
            });
            html += '</ol></div>';
        }

        container.innerHTML = html;
    }

    /**
     * Show loading state for a specific insight type
     * @param {string} type - Insight type (insights, forecast, root-cause)
     */
    showLoading(type) {
        const container = document.getElementById(`ai-${type}-content`);
        if (container) {
            container.innerHTML = '<div class="ai-loading"><div class="spinner"></div><p>Generating AI insights...</p></div>';
        }
    }

    /**
     * Hide loading state for a specific insight type
     * @param {string} type - Insight type (insights, forecast, root-cause)
     */
    hideLoading(type) {
        // Loading is replaced by content, so nothing to do here
    }

    /**
     * Handle errors with user-friendly messages
     * @param {Error} error - Error object
     * @param {string} type - Insight type (insights, forecast, root-cause)
     */
    handleError(error, type) {
        const container = document.getElementById(`ai-${type}-content`);
        if (!container) return;

        let message = 'An error occurred generating insights. Please try again.';
        
        if (error.message.includes('503')) {
            message = 'AI service is temporarily unavailable. Showing cached data if available.';
        } else if (error.message.includes('429')) {
            message = 'Too many requests. Please try again in a moment.';
        } else if (error.message.includes('404')) {
            message = 'System not found. Please select a valid system.';
        } else if (error.message.includes('400')) {
            message = 'Invalid request. Please check your date range.';
        }

        container.innerHTML = `
            <div class="ai-error">
                <div class="error-icon">⚠</div>
                <p>${message}</p>
            </div>
        `;

        this.hideLoading(type);
    }

    /**
     * Get icon for trend type
     * @param {string} type - Trend type
     * @returns {string} Icon HTML
     */
    getTrendIcon(type) {
        const icons = {
            'increasing': '📈',
            'decreasing': '📉',
            'stable': '➡️',
            'trend': '📊'
        };
        return icons[type] || icons['trend'];
    }

    /**
     * Get icon for anomaly severity
     * @param {string} severity - Severity level
     * @returns {string} Icon HTML
     */
    getAnomalyIcon(severity) {
        const icons = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        };
        return icons[severity] || '⚠️';
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Clear all insights and show loading placeholders
     */
    clear() {
        ['insights', 'forecast', 'root-cause'].forEach(type => {
            const container = document.getElementById(`ai-${type}-content`);
            if (container) {
                container.innerHTML = '<div class="ai-loading"><div class="spinner"></div><p>Loading insights...</p></div>';
            }
        });

        // Destroy chart
        if (this.forecastChart) {
            this.forecastChart.destroy();
            this.forecastChart = null;
        }

        this.currentSystemId = null;
        this.currentDateRange = null;
    }
}
