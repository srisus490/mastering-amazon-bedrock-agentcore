/**
 * API Client Module
 * Handles all HTTP communication with the FastAPI backend
 * 
 * Features:
 * - Configurable base URL
 * - Error handling with structured errors
 * - Retry logic with exponential backoff (max 3 retries)
 * - Response caching with 30-second TTL
 * - All backend API endpoints
 */

export class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.cache = new Map();
        this.retryPolicy = {
            maxRetries: 3,
            initialBackoff: 100 // milliseconds
        };
        console.log(`APIClient initialized with baseURL: ${this.baseURL}`);
    }

    /**
     * Fetch wrapper with error handling and retry logic
     * @private
     */
    async _fetchWithRetry(url, options = {}, retryCount = 0) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            // Retry logic with exponential backoff
            if (retryCount < this.retryPolicy.maxRetries) {
                const backoffTime = this.retryPolicy.initialBackoff * Math.pow(2, retryCount);
                console.warn(`Request failed, retrying in ${backoffTime}ms (attempt ${retryCount + 1}/${this.retryPolicy.maxRetries})`, error);
                
                await new Promise(resolve => setTimeout(resolve, backoffTime));
                return this._fetchWithRetry(url, options, retryCount + 1);
            }

            // Max retries exceeded
            console.error('API request failed after max retries:', error);
            throw error;
        }
    }

    /**
     * Get data with caching support
     * @private
     */
    async _getCached(endpoint, params = {}) {
        // Build cache key from endpoint and params
        const cacheKey = endpoint + JSON.stringify(params);
        
        // Check cache
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < 60000) { // 60-second TTL
            console.log(`Cache hit for ${endpoint}`);
            return cached.data;
        }

        // Build URL with query parameters
        const url = new URL(`${this.baseURL}${endpoint}`);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        // Fetch data
        const data = await this._fetchWithRetry(url.toString());

        // Cache the response
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });

        return data;
    }

    /**
     * File Arrival Endpoints
     */

    /**
     * Get file arrivals with optional filters
     * @param {Object} filters - Filter options (source_system_id, start_date, end_date, status)
     * @returns {Promise<Array>} List of file arrivals
     */
    async getFileArrivals(filters = {}) {
        return this._getCached('/api/v1/file-arrivals', filters);
    }

    /**
     * Get file count with optional filters
     * @param {Object} filters - Filter options (source_system_id, start_date, end_date)
     * @returns {Promise<Object>} File count data
     */
    async getFileCount(filters = {}) {
        return this._getCached('/api/v1/file-arrivals/count', filters);
    }

    /**
     * SLA Endpoints
     */

    /**
     * Get bulk SLA summary (score + worst severity) for ALL systems in one call.
     * @param {number} days - Lookback window (default 30)
     * @returns {Promise<Object>} Map of systemId -> { sla_score, worst_severity }
     */
    async getAllSystemsSLASummary(days = 30) {
        return this._getCached('/api/v1/sla/all-systems-summary', { days });
    }

    /**
     * Get SLA scores for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to retrieve (default: 7)
     * @returns {Promise<Array>} List of SLA scores
     */
    async getSLAScores(sourceSystemId, days = 7) {
        return this._getCached(`/api/v1/sla/scores/${encodeURIComponent(sourceSystemId)}`, { days });
    }

    /**
     * Get average SLA score for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to average (default: 7)
     * @param {Object} dateRange - Optional date range {start_date, end_date}
     * @returns {Promise<Object>} Average SLA score data
     */
    async getAverageSLAScore(sourceSystemId, days = 7, dateRange = {}) {
        const params = { days, ...dateRange };
        return this._getCached(`/api/v1/sla/average-score/${encodeURIComponent(sourceSystemId)}`, params);
    }

    /**
     * Get SLA violations with optional filters
     * @param {Object} filters - Filter options (source_system_id, start_date, end_date, severity)
     * @returns {Promise<Array>} List of SLA violations
     */
    async getSLAViolations(filters = {}) {
        return this._getCached('/api/v1/sla/violations', filters);
    }

    /**
     * Get SLA violations by severity for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to retrieve (default: 7)
     * @returns {Promise<Object>} Violations grouped by severity
     */
    async getSLAViolationsBySeverity(sourceSystemId, days = 7) {
        return this._getCached(`/api/v1/sla/violations/by-severity/${encodeURIComponent(sourceSystemId)}`, { days });
    }

    /**
     * Trend Endpoints
     */

    /**
     * Get daily trend data for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to retrieve (default: 30)
     * @returns {Promise<Array>} Daily trend data points
     */
    async getDailyTrends(sourceSystemId, days = 30) {
        return this._getCached(`/api/v1/trends/daily/${encodeURIComponent(sourceSystemId)}`, { days });
    }

    /**
     * Get moving average data for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to retrieve (default: 30)
     * @returns {Promise<Array>} Moving average data points
     */
    async getMovingAverage(sourceSystemId, days = 30) {
        return this._getCached(`/api/v1/trends/moving-average/${encodeURIComponent(sourceSystemId)}`, { days });
    }

    /**
     * Get hourly pattern data for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} days - Number of days to analyze (default: 7)
     * @returns {Promise<Array>} Hourly pattern data
     */
    async getHourlyPatterns(sourceSystemId, days = 7) {
        return this._getCached(`/api/v1/trends/hourly-patterns/${encodeURIComponent(sourceSystemId)}`, { days });
    }

    /**
     * Get summary of all monitored systems
     * @param {Object} filters - Optional filters (start_date, end_date)
     * @returns {Promise<Array>} List of system summaries
     */
    async getSystemsSummary(filters = {}) {
        return this._getCached('/api/v1/trends/summary', filters);
    }

    /**
     * AI Insights Endpoints
     */

    /**
     * Get AI-powered smart insights for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {string} startDate - Start date (YYYY-MM-DD)
     * @param {string} endDate - End date (YYYY-MM-DD)
     * @returns {Promise<Object>} Smart insights with trends, anomalies, and recommendations
     */
    async getSmartInsights(sourceSystemId, startDate, endDate) {
        const url = `${this.baseURL}/api/v1/ai/insights`;
        console.log('API Request - Smart Insights:', {
            url,
            sourceSystemId,
            startDate,
            endDate,
            startDateType: typeof startDate,
            endDateType: typeof endDate
        });
        
        try {
            const result = await this._fetchWithRetry(url, {
                method: 'POST',
                body: JSON.stringify({
                    source_system_id: sourceSystemId,
                    start_date: startDate,
                    end_date: endDate
                })
            });
            console.log('API Response - Smart Insights:', result);
            return result;
        } catch (error) {
            console.error('API Error - Smart Insights:', error);
            throw error;
        }
    }

    /**
     * Get AI-powered 7-day forecast for a source system
     * @param {string} sourceSystemId - Source system identifier
     * @param {number} historicalDays - Number of historical days to analyze (30-90, default: 60)
     * @returns {Promise<Object>} 7-day forecast with predictions and confidence levels
     */
    async getForecast(sourceSystemId, historicalDays = 60) {
        const url = `${this.baseURL}/api/v1/ai/forecast`;
        console.log('API Request - Forecast:', {
            url,
            sourceSystemId,
            historicalDays
        });
        
        try {
            const result = await this._fetchWithRetry(url, {
                method: 'POST',
                body: JSON.stringify({
                    source_system_id: sourceSystemId,
                    historical_days: historicalDays
                })
            });
            console.log('API Response - Forecast:', result);
            return result;
        } catch (error) {
            console.error('API Error - Forecast:', error);
            throw error;
        }
    }

    /**
     * Get AI-powered root cause analysis for SLA violations
     * @param {string} sourceSystemId - Source system identifier
     * @param {string} startDate - Start date (YYYY-MM-DD)
     * @param {string} endDate - End date (YYYY-MM-DD)
     * @returns {Promise<Object>} Root cause analysis with causes, correlations, and remediation actions
     */
    async getRootCauseAnalysis(sourceSystemId, startDate, endDate) {
        const url = `${this.baseURL}/api/v1/ai/root-cause`;
        console.log('API Request - Root Cause:', {
            url,
            sourceSystemId,
            startDate,
            endDate,
            startDateType: typeof startDate,
            endDateType: typeof endDate
        });
        
        try {
            const result = await this._fetchWithRetry(url, {
                method: 'POST',
                body: JSON.stringify({
                    source_system_id: sourceSystemId,
                    start_date: startDate,
                    end_date: endDate
                })
            });
            console.log('API Response - Root Cause:', result);
            return result;
        } catch (error) {
            console.error('API Error - Root Cause:', error);
            throw error;
        }
    }

    /**
     * Utility Methods
     */

    /**
     * Clear all cached responses
     */
    clearCache() {
        this.cache.clear();
        console.log('API cache cleared');
    }

    /**
     * Update retry policy configuration
     * @param {number} maxRetries - Maximum number of retry attempts
     * @param {number} initialBackoff - Initial backoff time in milliseconds
     */
    setRetryPolicy(maxRetries, initialBackoff) {
        this.retryPolicy = {
            maxRetries,
            initialBackoff
        };
        console.log(`Retry policy updated: maxRetries=${maxRetries}, initialBackoff=${initialBackoff}ms`);
    }

    /**
     * Chat Endpoints
     */

    /**
     * Send a chat query
     * @param {Object} request - Chat request (query, context, session_id, include_system_context)
     * @returns {Promise<Object>} Chat response
     */
    async sendChatQuery(request) {
        const url = `${this.baseURL}/api/v1/chat/agent`;
        return this._fetchWithRetry(url, {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    /**
     * Get example questions
     * @param {string} systemId - Optional system ID for context-aware examples
     * @returns {Promise<Object>} Examples response
     */
    async getChatExamples(systemId = null) {
        // Always fetch fresh — examples must reflect the currently selected system
        let endpoint = '/api/v1/chat/examples';
        if (systemId) {
            endpoint += `?system_id=${encodeURIComponent(systemId)}`;
        }
        const url = new URL(`${this.baseURL}${endpoint}`);
        return this._fetchWithRetry(url.toString());
    }

    /**
     * Clear chat cache
     * @param {string} sessionId - Session ID to clear
     * @returns {Promise<Object>} Clear response
     */
    async clearChatCache(sessionId) {
        const url = `${this.baseURL}/api/v1/chat/clear`;
        return this._fetchWithRetry(url, {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
    }

    /**
     * Check chat service health
     * @returns {Promise<Object>} Health status
     */
    async getChatHealth() {
        return this._getCached('/api/v1/chat/health');
    }
}
