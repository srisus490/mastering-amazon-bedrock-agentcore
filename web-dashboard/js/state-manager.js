/**
 * State Manager Module
 * Centralized state management with observer pattern
 */

export class StateManager {
    constructor() {
        // Initialize state object
        this.state = {
            selectedSystem: null,
            dateRange: {
                startDate: null,
                endDate: null
            },
            filters: {
                severity: null,
                status: null
            },
            lastRefreshTime: null,
            autoRefreshEnabled: true
        };

        // Initialize cache with Map for efficient lookups
        this.cache = new Map();

        // Initialize observers map for event subscriptions
        this.observers = new Map();

        console.log('StateManager initialized');
    }

    // ==================== Getter Methods ====================

    /**
     * Get the currently selected source system ID
     * @returns {string|null} The selected system ID or null
     */
    getSelectedSystem() {
        return this.state.selectedSystem;
    }

    /**
     * Get the current date range filter
     * @returns {Object} Object with startDate and endDate properties
     */
    getDateRange() {
        return { ...this.state.dateRange };
    }

    /**
     * Get the current filters
     * @returns {Object} Object with severity and status properties
     */
    getFilters() {
        return { ...this.state.filters };
    }

    /**
     * Get the last refresh timestamp
     * @returns {Date|null} The last refresh time or null
     */
    getLastRefreshTime() {
        return this.state.lastRefreshTime;
    }

    /**
     * Get the auto-refresh enabled state
     * @returns {boolean} True if auto-refresh is enabled
     */
    getAutoRefreshEnabled() {
        return this.state.autoRefreshEnabled;
    }

    /**
     * Get the entire state object (for debugging)
     * @returns {Object} A copy of the current state
     */
    getState() {
        return {
            ...this.state,
            dateRange: { ...this.state.dateRange },
            filters: { ...this.state.filters }
        };
    }

    // ==================== Setter Methods with Validation ====================

    /**
     * Set the selected source system
     * @param {string|null} systemId - The system ID to select
     */
    setSelectedSystem(systemId) {
        if (systemId !== null && typeof systemId !== 'string') {
            throw new Error('System ID must be a string or null');
        }

        this.state.selectedSystem = systemId;
        this.notify('systemChanged', { systemId });
        this.syncStateToURL();
    }

    /**
     * Set the date range filter with validation
     * @param {Date|string|null} startDate - The start date
     * @param {Date|string|null} endDate - The end date
     * @throws {Error} If start date is after end date
     */
    setDateRange(startDate, endDate) {
        // Convert strings to Date objects if needed
        const start = startDate ? (startDate instanceof Date ? startDate : new Date(startDate)) : null;
        const end = endDate ? (endDate instanceof Date ? endDate : new Date(endDate)) : null;

        // Validate date range
        if (start && end && start > end) {
            throw new Error('Start date must be before or equal to end date');
        }

        // Validate that dates are valid
        if (start && isNaN(start.getTime())) {
            throw new Error('Invalid start date');
        }
        if (end && isNaN(end.getTime())) {
            throw new Error('Invalid end date');
        }

        this.state.dateRange.startDate = start;
        this.state.dateRange.endDate = end;
        this.notify('dateRangeChanged', { startDate: start, endDate: end });
        this.syncStateToURL();
    }

    /**
     * Set filters (severity, status, etc.)
     * @param {Object} filters - Object containing filter properties
     */
    setFilters(filters) {
        if (typeof filters !== 'object' || filters === null) {
            throw new Error('Filters must be an object');
        }

        // Update only provided filter properties
        if (filters.hasOwnProperty('severity')) {
            this.state.filters.severity = filters.severity;
        }
        if (filters.hasOwnProperty('status')) {
            this.state.filters.status = filters.status;
        }

        this.notify('filtersChanged', { ...this.state.filters });
        this.syncStateToURL();
    }

    /**
     * Update the last refresh timestamp to current time
     */
    updateLastRefreshTime() {
        this.state.lastRefreshTime = new Date();
        this.notify('refreshTimeUpdated', { timestamp: this.state.lastRefreshTime });
    }

    /**
     * Set the auto-refresh enabled state
     * @param {boolean} enabled - Whether auto-refresh should be enabled
     */
    setAutoRefreshEnabled(enabled) {
        if (typeof enabled !== 'boolean') {
            throw new Error('Auto-refresh enabled must be a boolean');
        }

        this.state.autoRefreshEnabled = enabled;
        this.notify('autoRefreshChanged', { enabled });
    }

    /**
     * Reset all filters to default values
     */
    resetFilters() {
        this.state.selectedSystem = null;
        this.state.dateRange.startDate = null;
        this.state.dateRange.endDate = null;
        this.state.filters.severity = null;
        this.state.filters.status = null;

        this.notify('filtersReset', {});
        this.syncStateToURL();
    }

    // ==================== Observer Pattern ====================

    /**
     * Subscribe to state change events
     * @param {string} eventType - The event type to subscribe to
     * @param {Function} callback - The callback function to invoke
     */
    subscribe(eventType, callback) {
        if (typeof callback !== 'function') {
            throw new Error('Callback must be a function');
        }

        if (!this.observers.has(eventType)) {
            this.observers.set(eventType, []);
        }

        this.observers.get(eventType).push(callback);
    }

    /**
     * Unsubscribe from state change events
     * @param {string} eventType - The event type to unsubscribe from
     * @param {Function} callback - The callback function to remove
     */
    unsubscribe(eventType, callback) {
        if (!this.observers.has(eventType)) {
            return;
        }

        const callbacks = this.observers.get(eventType);
        const index = callbacks.indexOf(callback);

        if (index > -1) {
            callbacks.splice(index, 1);
        }

        // Clean up empty observer arrays
        if (callbacks.length === 0) {
            this.observers.delete(eventType);
        }
    }

    /**
     * Notify all subscribers of a state change event
     * @param {string} eventType - The event type that occurred
     * @param {*} data - The data to pass to subscribers
     */
    notify(eventType, data) {
        if (!this.observers.has(eventType)) {
            return;
        }

        const callbacks = this.observers.get(eventType);
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in observer callback for ${eventType}:`, error);
            }
        });
    }

    // ==================== Cache Management ====================

    /**
     * Set cached data with optional TTL (time-to-live)
     * @param {string} key - The cache key
     * @param {*} data - The data to cache
     * @param {number} ttl - Time-to-live in milliseconds (default: 30000)
     */
    setCachedData(key, data, ttl = 30000) {
        const expiresAt = Date.now() + ttl;
        this.cache.set(key, {
            data,
            expiresAt
        });
    }

    /**
     * Get cached data if it exists and hasn't expired
     * @param {string} key - The cache key
     * @returns {*} The cached data or null if not found or expired
     */
    getCachedData(key) {
        if (!this.cache.has(key)) {
            return null;
        }

        const cached = this.cache.get(key);

        // Check if cache has expired
        if (Date.now() > cached.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Clear all cached data
     */
    clearCache() {
        this.cache.clear();
        this.notify('cacheCleared', {});
    }

    /**
     * Clear expired cache entries
     */
    clearExpiredCache() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now > value.expiresAt) {
                this.cache.delete(key);
            }
        }
    }

    // ==================== URL State Synchronization ====================

    /**
     * Synchronize current state to URL query parameters
     * Allows bookmarking and sharing of filtered views
     */
    syncStateToURL() {
        const params = new URLSearchParams();

        // Add selected system to URL
        if (this.state.selectedSystem) {
            params.set('system', this.state.selectedSystem);
        }

        // Add date range to URL
        if (this.state.dateRange.startDate) {
            params.set('startDate', this.state.dateRange.startDate.toISOString().split('T')[0]);
        }
        if (this.state.dateRange.endDate) {
            params.set('endDate', this.state.dateRange.endDate.toISOString().split('T')[0]);
        }

        // Add filters to URL
        if (this.state.filters.severity) {
            params.set('severity', this.state.filters.severity);
        }
        if (this.state.filters.status) {
            params.set('status', this.state.filters.status);
        }

        // Update URL without reloading the page
        const newURL = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
        window.history.replaceState({}, '', newURL);
    }

    /**
     * Load state from URL query parameters
     * Called on page load to restore bookmarked state
     */
    loadStateFromURL() {
        const params = new URLSearchParams(window.location.search);

        // Load selected system
        const system = params.get('system');
        if (system) {
            this.state.selectedSystem = system;
            // Trigger system changed event so UI updates
            this.notify('systemChanged', { systemId: system });
        }

        // Load date range
        const startDate = params.get('startDate');
        const endDate = params.get('endDate');
        let datesLoaded = false;
        
        if (startDate) {
            try {
                this.state.dateRange.startDate = new Date(startDate);
                datesLoaded = true;
            } catch (error) {
                console.error('Invalid start date in URL:', error);
            }
        }
        if (endDate) {
            try {
                this.state.dateRange.endDate = new Date(endDate);
                datesLoaded = true;
            } catch (error) {
                console.error('Invalid end date in URL:', error);
            }
        }

        // Update date inputs in UI if dates were loaded
        if (startDate || endDate) {
            const startInput = document.getElementById('start-date');
            const endInput = document.getElementById('end-date');
            if (startInput && startDate) {
                startInput.value = startDate;
            }
            if (endInput && endDate) {
                endInput.value = endDate;
            }
        }

        // Trigger dateRangeChanged event if dates were loaded
        if (datesLoaded) {
            this.notify('dateRangeChanged', { 
                startDate: this.state.dateRange.startDate, 
                endDate: this.state.dateRange.endDate 
            });
        }

        // Load filters
        const severity = params.get('severity');
        const status = params.get('status');
        if (severity) {
            this.state.filters.severity = severity;
        }
        if (status) {
            this.state.filters.status = status;
        }

        // Notify subscribers that state was loaded from URL
        this.notify('stateLoadedFromURL', this.getState());
    }
}
