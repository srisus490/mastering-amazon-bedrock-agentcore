/**
 * UI Manager Module
 * Handles DOM manipulation and user interaction
 */

export class UIManager {
    constructor(stateManager, apiClient) {
        this.stateManager = stateManager;
        this.apiClient = apiClient;
        this.currentPage = 1;
        this.pageSize = 30;
        console.log('UIManager initialized');
    }

    /**
     * Initialize UI and setup event listeners
     */
    initialize() {
        this.setupEventListeners();
    }

    /**
     * Setup event listeners for user interactions
     */
    setupEventListeners() {
        // System selection dropdown
        const systemSelect = document.getElementById('system-select');
        if (systemSelect) {
            systemSelect.addEventListener('change', (e) => {
                this.stateManager.setSelectedSystem(e.target.value || null);
            });
        }

        // Date range filters
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        if (startDateInput && endDateInput) {
            // Set today as the max for both inputs — no future dates allowed
            const todayStr = new Date().toISOString().split('T')[0];
            startDateInput.max = todayStr;
            endDateInput.max = todayStr;

            const onDateChange = () => this.handleDateRangeChange();
            startDateInput.addEventListener('change', onDateChange);
            startDateInput.addEventListener('input', onDateChange);
            endDateInput.addEventListener('change', onDateChange);
            endDateInput.addEventListener('input', onDateChange);
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }

        // Manual refresh button
        const refreshBtn = document.getElementById('manual-refresh');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.stateManager.notify('manualRefresh');
            });
        }

        // Severity filter
        const severitySelect = document.getElementById('severity-filter');
        if (severitySelect) {
            severitySelect.addEventListener('change', (e) => {
                this.stateManager.setFilters({ severity: e.target.value || null });
            });
        }

        // Tab buttons
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabId = e.target.dataset.tab;
                this.switchTab(tabId);
            });
        });
    }

    /**
     * Switch between tabs in the details section
     * @param {string} tabId - The tab to switch to
     */
    switchTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            }
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            if (content.id === tabId) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    }

    /**
     * Handle date range changes with validation
     */
    handleDateRangeChange() {
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        
        if (!startDateInput || !endDateInput) return;

        const todayStr = new Date().toISOString().split('T')[0];

        // Cross-constrain: start can't be after end, end can't be after today or before start
        if (startDateInput.value) {
            endDateInput.min = startDateInput.value;
        } else {
            endDateInput.removeAttribute('min');
        }
        if (endDateInput.value) {
            startDateInput.max = endDateInput.value;
        } else {
            startDateInput.max = todayStr;
        }
        // End date can never exceed today
        endDateInput.max = todayStr;

        const startDate = startDateInput.value ? new Date(startDateInput.value) : null;
        const endDate = endDateInput.value ? new Date(endDateInput.value) : null;

        // Clear any previous error
        const errorContainer = document.getElementById('date-range-error');
        if (errorContainer) errorContainer.innerHTML = '';

        // Only fire when both are set or both are cleared
        const bothSet = startDate && endDate;
        const bothCleared = !startDate && !endDate;
        if (bothSet || bothCleared) {
            this.stateManager.setDateRange(startDate, endDate);
        }
    }
    /**
     * Clear all filters
     */
    clearFilters() {
        const todayStr = new Date().toISOString().split('T')[0];

        const systemSelect = document.getElementById('system-select');
        if (systemSelect) systemSelect.value = '';

        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        if (startDateInput) { startDateInput.value = ''; startDateInput.max = todayStr; startDateInput.removeAttribute('min'); }
        if (endDateInput)   { endDateInput.value = '';   endDateInput.max = todayStr;   endDateInput.removeAttribute('min'); }

        const severitySelect = document.getElementById('severity-filter');
        if (severitySelect) severitySelect.value = '';

        const errorContainer = document.getElementById('date-range-error');
        if (errorContainer) errorContainer.innerHTML = '';

        this.stateManager.resetFilters();
    }

    /**
     * Render system overview cards
     * @param {Array} systems - Array of system summary objects
     * @param {string|null} severityFilter - Optional severity to filter cards by
     */
    renderSystemOverview(systems, severityFilter = null) {
        const container = document.getElementById('system-overview');
        if (!container) return;

        if (!systems || systems.length === 0) {
            container.innerHTML = '<p class="no-data">No systems found</p>';
            return;
        }

        // Filter systems if a specific system is selected
        const selectedSystem = this.stateManager.getSelectedSystem();
        let displaySystems = systems;
        if (selectedSystem) {
            displaySystems = systems.filter(s => 
                (s.source_system_id || s.sourceSystemId) === selectedSystem
            );
        }

        // Apply severity filter — show ONLY systems whose worst_severity exactly matches
        // the selected level. "Medium" = medium only, "High" = high only, "Critical" = critical only.
        if (severityFilter) {
            const sf = severityFilter.toLowerCase();
            displaySystems = displaySystems.filter(s => {
                const ws = (s.worst_severity || '').toLowerCase();
                return ws === sf;
            });
        }

        // When a date range is active, filter out systems with no files in that range
        const hasDateRange = systems.some(s => s.file_count_range !== null && s.file_count_range !== undefined);
        if (hasDateRange && !selectedSystem) {
            displaySystems = displaySystems.filter(s =>
                s.file_count_range !== null && s.file_count_range !== undefined && s.file_count_range > 0
            );
        }

        container.innerHTML = displaySystems.map(system => {
            return this._buildSystemCardHTML(system, hasDateRange);
        }).join('');

        // Add click handlers to system cards
        container.querySelectorAll('.system-card').forEach(card => {
            card.addEventListener('click', () => {
                const systemId = card.dataset.systemId;
                this.stateManager.setSelectedSystem(systemId);
                
                // Update the dropdown to reflect the selection
                const systemSelect = document.getElementById('system-select');
                if (systemSelect) {
                    systemSelect.value = systemId;
                }
            });
        });

        // Populate the system dropdown
        this.populateSystemDropdown(systems);

        // Build / refresh the alphabet sidebar
        this.buildAlphaSidebar(systems);

        // Update severity dropdown — disable options that don't exist in current system set
        this._updateSeverityDropdown(systems, severityFilter);
    }

    /**
     * Update severity dropdown options based on what severities exist in the current system set.
     * Disables options that have no matching systems, and reflects backward sync:
     * if a specific system is selected, only its severity (and above) are enabled.
     */
    _updateSeverityDropdown(systems, currentSeverityFilter) {
        const sel = document.getElementById('severity-filter');
        if (!sel) return;

        const SEV_ORDER = ['critical', 'high', 'medium', 'low'];

        // Collect all worst_severity values present in the full system list
        const presentSeverities = new Set(
            systems
                .map(s => (s.worst_severity || '').toLowerCase())
                .filter(s => SEV_ORDER.includes(s))
        );

        // If a single system is selected, only enable that system's exact severity
        const selectedSystem = this.stateManager.getSelectedSystem();
        let allowedSeverities = null;
        if (selectedSystem) {
            const sys = systems.find(s => (s.source_system_id || s.sourceSystemId) === selectedSystem);
            if (sys && sys.worst_severity) {
                // Only the exact severity of this system is valid to filter by
                allowedSeverities = new Set([sys.worst_severity.toLowerCase()]);
            } else {
                allowedSeverities = new Set(); // no violations — no severity applies
            }
        }

        Array.from(sel.options).forEach(opt => {
            if (!opt.value) return; // "All" always enabled
            const sev = opt.value.toLowerCase();
            const existsInData = presentSeverities.has(sev);
            const allowedBySelection = allowedSeverities === null || allowedSeverities.has(sev);
            const enabled = existsInData && allowedBySelection;
            opt.disabled = !enabled;
            opt.style.color = enabled ? '' : '#666';
            opt.title = enabled ? '' : 'Not applicable for current selection';
        });

        // If current selection is now disabled, reset to All
        const currentOpt = sel.options[sel.selectedIndex];
        if (currentOpt && currentOpt.value && currentOpt.disabled) {
            sel.value = '';
            this.stateManager.setFilters({ severity: null });
        }
    }

    /**
     * Build HTML for a single system card.
     * Priority is derived from worst_severity (actual violations), not SLA score.
     */
    _buildSystemCardHTML(system, hasDateRange) {
        const systemId = system.source_system_id || system.sourceSystemId;
        const fileCountToday = system.file_count_today !== undefined ? system.file_count_today : system.file_count;
        const fileCountRange = system.file_count_range;
        const lastArrival = system.last_arrival || system.lastFileArrival;
        const slaScore = system.sla_score !== undefined ? system.sla_score : system.slaScore;
        const status = system.status || 'healthy';
        const statusClass = this.getStatusClass(status);

        // Derive priority badge from actual worst violation severity
        const ws = (system.worst_severity || '').toLowerCase();
        let priority = null, priorityClass = '';
        if (ws === 'critical')  { priority = 'CRITICAL'; priorityClass = 'priority-critical'; }
        else if (ws === 'high') { priority = 'HIGH';     priorityClass = 'priority-high'; }
        else if (ws === 'medium'){ priority = 'MEDIUM';  priorityClass = 'priority-medium'; }
        else if (ws === 'low')  { priority = 'LOW';      priorityClass = 'priority-low'; }

        const hasViolations = !!ws;
        const warningClass = hasViolations ? 'has-warning' : '';

        // When a date range is active, show range count as the primary metric
        const rangeActive = hasDateRange && fileCountRange !== null && fileCountRange !== undefined;
        const primaryLabel = rangeActive ? 'File Count (Range):' : 'File Count (Today):';
        const primaryCount = rangeActive ? fileCountRange : fileCountToday;

        return `
            <div class="system-card ${statusClass} ${warningClass}" data-system-id="${systemId}">
                <div class="system-header">
                    <h3 class="system-name">${this.escapeHtml(systemId)}</h3>
                    ${priority ? `<span class="priority-badge ${priorityClass}">${priority}</span>` : ''}
                </div>
                <div class="system-status">
                    <span class="status-badge ${statusClass}">${status}</span>
                </div>
                <div class="system-stats">
                    <div class="stat">
                        <span class="stat-label">${primaryLabel}</span>
                        <span class="stat-value">${this.formatNumber(primaryCount || 0)}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">SLA Score:</span>
                        <span class="stat-value">${slaScore !== undefined && slaScore !== null ? slaScore.toFixed(1) : 'N/A'}</span>
                    </div>
                    ${lastArrival ? `
                        <div class="stat">
                            <span class="stat-label">Last Arrival:</span>
                            <span class="stat-value">${this.formatDate(lastArrival)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Build the A–Z alphabet sidebar.
     * Letters that have at least one matching system are active; others are dimmed.
     * Clicking a letter filters the system grid to show only matching systems.
     * For PROD_* systems the letter is derived from the suffix (e.g. PROD_CUSTOMER → C).
     */
    buildAlphaSidebar(systems) {
        const list = document.getElementById('alpha-list');
        if (!list) return;

        // Map each system to its "sort letter"
        const getSystemLetter = (id) => {
            const upper = (id || '').toUpperCase();
            // Strip common prefixes so PROD_SALES → S, TEST001 → T, SYS001 → S
            const stripped = upper.replace(/^(PROD_|TEST_|SYS_|DEV_|UAT_)/, '');
            return stripped.charAt(0) || '#';
        };

        // Build a set of active letters
        const activeLetters = new Set(
            systems.map(s => getSystemLetter(s.source_system_id || s.sourceSystemId))
        );

        const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

        list.innerHTML = alphabet.map(letter => {
            const isActive = activeLetters.has(letter);
            return `<li>
                <button
                    class="${isActive ? '' : 'disabled'}"
                    data-letter="${letter}"
                    title="${isActive ? 'Show ' + letter + ' systems' : 'No systems'}"
                    ${isActive ? '' : 'disabled'}
                >${letter}</button>
            </li>`;
        }).join('');

        // Add ALL button at the bottom
        const allLi = document.createElement('li');
        allLi.style.marginTop = '6px';
        allLi.innerHTML = `<button class="alpha-all-btn active" data-letter="ALL" title="Show all systems">ALL</button>`;
        list.appendChild(allLi);

        // Store all systems for filtering
        this._allSystems = systems;
        this._activeAlphaLetter = null;

        // Click handler
        list.querySelectorAll('button:not([disabled])').forEach(btn => {
            btn.addEventListener('click', () => {
                const letter = btn.dataset.letter;

                if (letter === 'ALL') {
                    this._activeAlphaLetter = null;
                    list.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    this._renderFilteredSystems(this._allSystems);
                    this._syncDropdownToFiltered(this._allSystems, null);
                    return;
                }

                if (this._activeAlphaLetter === letter) {
                    // Second click → show all, clear selection
                    this._activeAlphaLetter = null;
                    list.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    list.querySelector('.alpha-all-btn').classList.add('active');
                    this._renderFilteredSystems(this._allSystems);
                    this._syncDropdownToFiltered(this._allSystems, null);
                } else {
                    this._activeAlphaLetter = letter;
                    list.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    const filtered = systems.filter(s => {
                        const id = s.source_system_id || s.sourceSystemId;
                        return getSystemLetter(id) === letter;
                    });
                    this._renderFilteredSystems(filtered);

                    // Auto-select the best-ranked system in this letter group
                    const best = this._rankSystems(filtered)[0];
                    if (best) {
                        const bestId = best.source_system_id || best.sourceSystemId;
                        this.stateManager.setSelectedSystem(bestId);
                        this._syncDropdownToFiltered(filtered, bestId);
                    }
                }
            });
        });
    }

    /**
     * Re-render only the system cards grid (without rebuilding sidebar/dropdown).
     */
    _renderFilteredSystems(systems) {
        const container = document.getElementById('system-overview');
        if (!container) return;

        if (!systems || systems.length === 0) {
            container.innerHTML = '<p class="no-data">No systems for this letter</p>';
            return;
        }

        const hasDateRange = systems.some(s => s.file_count_range !== null && s.file_count_range !== undefined);

        container.innerHTML = systems.map(system => this._buildSystemCardHTML(system, hasDateRange)).join('');

        // Re-attach click handlers
        container.querySelectorAll('.system-card').forEach(card => {
            card.addEventListener('click', () => {
                const systemId = card.dataset.systemId;
                this.stateManager.setSelectedSystem(systemId);
                const systemSelect = document.getElementById('system-select');
                if (systemSelect) systemSelect.value = systemId;
            });
        });
    }

    /**
     * Rank systems within a letter group.
     * Priority: highest SLA score first, then alphabetical by ID as tiebreaker.
     * Systems with critical/high violations are ranked lower.
     */
    _rankSystems(systems) {
        const SEV_PENALTY = { critical: -30, high: -15, medium: -5, low: 0 };
        return [...systems].sort((a, b) => {
            const scoreA = (a.sla_score ?? 50) + (SEV_PENALTY[(a.worst_severity || '').toLowerCase()] ?? 0);
            const scoreB = (b.sla_score ?? 50) + (SEV_PENALTY[(b.worst_severity || '').toLowerCase()] ?? 0);
            if (scoreB !== scoreA) return scoreB - scoreA; // higher score first
            // Alphabetical tiebreaker
            const idA = (a.source_system_id || a.sourceSystemId || '');
            const idB = (b.source_system_id || b.sourceSystemId || '');
            return idA.localeCompare(idB);
        });
    }

    /**
     * Update the source system dropdown to show only the filtered set,
     * and set its value to the given selectedId (or empty for "All").
     */
    _syncDropdownToFiltered(systems, selectedId) {
        const dropdown = document.getElementById('system-select');
        if (!dropdown) return;

        dropdown.innerHTML = '<option value="">All Systems</option>';
        systems.forEach(s => {
            const id = s.source_system_id || s.sourceSystemId;
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = id;
            dropdown.appendChild(opt);
        });
        dropdown.value = selectedId || '';
    }

    /**
     * Populate system dropdown with available systems
     * @param {Array} systems - Array of system objects
     */
    populateSystemDropdown(systems) {
        const dropdown = document.getElementById('system-select');
        if (!dropdown) return;

        const selectedSystem = this.stateManager.getSelectedSystem();

        // If an alpha letter is active, narrow the dropdown to only that letter's systems
        let displaySystems = systems;
        if (this._activeAlphaLetter) {
            const getSystemLetter = (id) => {
                const upper = (id || '').toUpperCase();
                return upper.replace(/^(PROD_|TEST_|SYS_|DEV_|UAT_)/, '').charAt(0) || '#';
            };
            displaySystems = systems.filter(s => {
                const id = s.source_system_id || s.sourceSystemId;
                return getSystemLetter(id) === this._activeAlphaLetter;
            });
        }

        dropdown.innerHTML = '<option value="">All Systems</option>';
        displaySystems.forEach(system => {
            const systemId = system.source_system_id || system.sourceSystemId;
            const option = document.createElement('option');
            option.value = systemId;
            option.textContent = systemId;
            dropdown.appendChild(option);
        });

        dropdown.value = selectedSystem || '';
    }

    /**
     * Render file arrivals with pagination
     * @param {Array} arrivals - Array of file arrival objects
     * @param {number} totalCount - Total number of arrivals
     */
    renderFileArrivals(arrivals, totalCount = null) {
        const container = document.getElementById('file-arrivals');
        if (!container) return;

        if (!arrivals || arrivals.length === 0) {
            container.innerHTML = '<p class="no-data">No file arrivals found</p>';
            return;
        }

        const total = totalCount || arrivals.length;
        const totalPages = Math.ceil(total / this.pageSize);

        let html = `
            <div class="file-arrivals-table">
                <table>
                    <thead>
                        <tr>
                            <th>File Name</th>
                            <th>Arrival Time</th>
                            <th>Source System</th>
                            <th>File Size</th>
                            <th>Checksum</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        arrivals.forEach(arrival => {
            // Handle both camelCase and snake_case field names
            const fileName = arrival.filename || arrival.fileName || 'Unknown';
            const arrivalTime = arrival.arrival_timestamp || arrival.arrivalTime;
            const sourceSystem = arrival.source_system_id || arrival.sourceSystemId || 'Unknown';
            const fileSize = arrival.file_size_bytes !== undefined ? arrival.file_size_bytes : arrival.fileSize;
            const checksum = arrival.checksum || 'N/A';
            
            html += `
                <tr>
                    <td class="file-name" title="${this.escapeHtml(fileName)}">${this.escapeHtml(fileName)}</td>
                    <td>${this.formatDate(arrivalTime)}</td>
                    <td>${this.escapeHtml(sourceSystem)}</td>
                    <td>${this.formatFileSize(fileSize)}</td>
                    <td class="checksum" title="${this.escapeHtml(checksum)}">${checksum ? checksum.substring(0, 8) + '...' : 'N/A'}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Add pagination if needed
        if (total > this.pageSize) {
            html += this.renderPagination(this.currentPage, totalPages, total);
        }

        container.innerHTML = html;

        // Setup pagination event listeners
        this.setupPaginationListeners();
    }

    /**
     * Render pagination controls
     * @param {number} currentPage - Current page number
     * @param {number} totalPages - Total number of pages
     * @param {number} totalItems - Total number of items
     * @returns {string} HTML string for pagination
     */
    renderPagination(currentPage, totalPages, totalItems) {
        const startItem = (currentPage - 1) * this.pageSize + 1;
        const endItem = Math.min(currentPage * this.pageSize, totalItems);

        let html = `
            <div class="pagination">
                <div class="pagination-info">
                    Showing ${startItem}-${endItem} of ${this.formatNumber(totalItems)}
                </div>
                <div class="pagination-controls">
        `;

        // Previous button
        html += `
            <button class="pagination-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
                Previous
            </button>
        `;

        // Page numbers (show max 5 pages)
        const maxPages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
        let endPage = Math.min(totalPages, startPage + maxPages - 1);
        
        if (endPage - startPage < maxPages - 1) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        if (startPage > 1) {
            html += `<button class="pagination-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">
                    ${i}
                </button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
            html += `<button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>`;
        }

        // Next button
        html += `
            <button class="pagination-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
                Next
            </button>
        `;

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Setup pagination event listeners
     */
    setupPaginationListeners() {
        const paginationBtns = document.querySelectorAll('.pagination-btn');
        paginationBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.target.dataset.page);
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    this.stateManager.notify('pageChange', { page });
                }
            });
        });
    }

    /**
     * Render SLA metrics
     * @param {Object} scores - SLA scores object
     * @param {Array} violations - Array of SLA violations
     */
    renderSLAMetrics(scores, violations) {
        const container = document.getElementById('sla-metrics');
        if (!container) return;

        // Derive priority from score
        let priority = 'HEALTHY', priorityClass = 'priority-healthy';
        const score = scores && scores.average_score !== undefined ? scores.average_score : null;
        if (score !== null) {
            if (score < 50)      { priority = 'HIGH PRIORITY';   priorityClass = 'priority-high'; }
            else if (score < 80) { priority = 'MEDIUM PRIORITY'; priorityClass = 'priority-medium'; }
            else if (score < 95) { priority = 'LOW PRIORITY';    priorityClass = 'priority-low'; }
        }

        // Count violations by severity
        const sevCounts = { critical: 0, high: 0, medium: 0, low: 0 };
        if (violations) violations.forEach(v => { if (sevCounts[v.severity] !== undefined) sevCounts[v.severity]++; });

        let html = '<div class="sla-metrics-container">';

        // Priority banner
        if (score !== null) {
            html += `
                <div class="priority-banner ${priorityClass}">
                    <span class="priority-icon">${priority === 'HEALTHY' ? '✅' : priority.startsWith('HIGH') ? '🔴' : priority.startsWith('MEDIUM') ? '🟠' : '🟡'}</span>
                    <span class="priority-label">${priority}</span>
                    <span class="priority-score">SLA Score: ${score.toFixed(1)}</span>
                </div>
            `;
        }

        // Severity breakdown pills
        if (violations && violations.length > 0) {
            html += `
                <div class="severity-breakdown">
                    ${sevCounts.critical > 0 ? `<span class="sev-pill sev-critical">🔴 Critical: ${sevCounts.critical}</span>` : ''}
                    ${sevCounts.high > 0     ? `<span class="sev-pill sev-high">🟠 High: ${sevCounts.high}</span>` : ''}
                    ${sevCounts.medium > 0   ? `<span class="sev-pill sev-medium">🟡 Medium: ${sevCounts.medium}</span>` : ''}
                    ${sevCounts.low > 0      ? `<span class="sev-pill sev-low">🔵 Low: ${sevCounts.low}</span>` : ''}
                </div>
            `;
        }

        // SLA score card
        if (score !== null) {
            const scoreClass = score < 80 ? 'warning' : score >= 95 ? 'healthy' : 'normal';
            html += `
                <div class="sla-score-card ${scoreClass}">
                    <h3>SLA Score</h3>
                    <div class="score-display">
                        <span class="score-value">${score.toFixed(1)}</span>
                        ${score < 80 ? '<span class="warning-indicator">⚠️</span>' : ''}
                    </div>
                    <div class="score-threshold">Warning Threshold: 80</div>
                    <div class="score-status">${score >= 80 ? '✓ Compliant' : '✗ Non-Compliant'}</div>
                    <div class="score-period">Period: ${scores.start_date || 'N/A'} to ${scores.end_date || 'N/A'}</div>
                </div>
            `;
        } else {
            html += `
                <div class="sla-score-card">
                    <h3>SLA Score</h3>
                    <div class="score-display"><span class="score-value">N/A</span></div>
                    <p class="no-data">No SLA data available for this system</p>
                </div>
            `;
        }

        // Violations list
        if (violations && violations.length > 0) {
            html += `
                <div class="sla-violations">
                    <h3>SLA Violations (${violations.length})</h3>
                    <div class="violations-list">
            `;
            violations.forEach(violation => {
                const sev = violation.severity || 'low';
                const sevLabel = sev.charAt(0).toUpperCase() + sev.slice(1);
                const sevIcon = sev === 'critical' ? '🔴' : sev === 'high' ? '🟠' : sev === 'medium' ? '🟡' : '🔵';
                html += `
                    <div class="violation-item severity-${sev}">
                        <div class="violation-header">
                            <span class="violation-severity ${sev}">${sevIcon} ${sevLabel}</span>
                            <span class="violation-time">${this.formatDate(violation.violation_date)}</span>
                        </div>
                        <div class="violation-type">${this.escapeHtml(violation.violation_type || 'Unknown')}</div>
                        <div class="violation-details">
                            <div>Expected: ${this.escapeHtml(violation.expected_value || 'N/A')}</div>
                            <div>Actual: ${this.escapeHtml(violation.actual_value || 'N/A')}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div></div>';
        } else if (score !== null) {
            html += '<div class="no-violations"><p>✅ No SLA violations in selected period</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Render filter controls
     */
    renderFilters() {
        const container = document.getElementById('filters');
        if (!container) return;

        // This method can be used to dynamically populate filter options
        // For now, filters are defined in HTML, but this can be extended
        console.log('Filters rendered');
    }

    /**
     * Render error message
     * @param {string|Error} error - Error message or Error object
     * @param {string} containerId - Optional container ID for the error
     */
    renderErrorMessage(error, containerId = 'error-banner') {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Error container not found:', containerId);
            return;
        }

        const errorMessage = error instanceof Error ? error.message : error;
        const errorDetails = error instanceof Error && error.stack ? error.stack : '';

        container.innerHTML = `
            <div class="error-message">
                <span class="error-icon">⚠️</span>
                <div class="error-content">
                    <div class="error-title">Error</div>
                    <div class="error-text">${this.escapeHtml(errorMessage)}</div>
                    ${this.getErrorGuidance(errorMessage)}
                </div>
                <button class="error-close" onclick="this.parentElement.remove()">×</button>
            </div>
        `;

        container.style.display = 'block';

        // Log to console for debugging
        console.error('Error:', errorMessage, errorDetails);
    }

    /**
     * Get actionable guidance for common errors
     * @param {string} errorMessage - Error message
     * @returns {string} HTML string with guidance
     */
    getErrorGuidance(errorMessage) {
        const lowerMessage = errorMessage.toLowerCase();
        
        if (lowerMessage.includes('network') || lowerMessage.includes('fetch')) {
            return '<div class="error-guidance">Check if the API is running at http://localhost:8000</div>';
        }
        
        if (lowerMessage.includes('timeout')) {
            return '<div class="error-guidance">The request timed out. Please try again.</div>';
        }
        
        if (lowerMessage.includes('404') || lowerMessage.includes('not found')) {
            return '<div class="error-guidance">The requested resource was not found.</div>';
        }
        
        if (lowerMessage.includes('500') || lowerMessage.includes('server error')) {
            return '<div class="error-guidance">Server error occurred. Please try again later.</div>';
        }
        
        return '<div class="error-guidance">Please try refreshing the page or contact support if the issue persists.</div>';
    }

    /**
     * Render loading state
     * @param {string} component - Component name to show loading state for
     */
    renderLoadingState(component) {
        const container = document.getElementById(component);
        if (!container) return;

        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `;
    }

    /**
     * Update last refresh timestamp display
     * @param {Date} timestamp - Timestamp of last refresh
     */
    updateLastRefreshTime(timestamp) {
        const container = document.getElementById('last-refresh-time');
        if (!container) return;

        container.textContent = `Last updated: ${this.formatDate(timestamp)}`;
    }

    /**
     * Show notification message
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, info, warning, error)
     */
    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `<span class="notification-message">${this.escapeHtml(message)}</span>`;
        container.appendChild(notification);

        // Auto-dismiss: fade out after 2.5s, remove after animation
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => notification.remove(), 400);
        }, 2500);
    }

    /**
     * Format number with thousand separators
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber(num) {
        if (num === null || num === undefined) return 'N/A';
        return num.toLocaleString('en-US');
    }

    /**
     * Format date to readable string
     * @param {Date|string} date - Date to format
     * @returns {string} Formatted date string
     */
    formatDate(date) {
        if (!date) return 'N/A';
        
        const d = date instanceof Date ? date : new Date(date);
        
        if (isNaN(d.getTime())) return 'Invalid Date';
        
        return d.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Format file size to human-readable string
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize(bytes) {
        if (bytes === null || bytes === undefined) return 'N/A';
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Get color for severity level
     * @param {string} severity - Severity level (high, medium, low)
     * @returns {string} Color code
     */
    getSeverityColor(severity) {
        const colors = {
            high: '#dc3545',      // red
            critical: '#dc3545',  // red
            medium: '#fd7e14',    // orange
            warning: '#ffc107',   // yellow
            low: '#0dcaf0',       // blue
            healthy: '#198754',   // green
            normal: '#6c757d'     // gray
        };

        return colors[severity?.toLowerCase()] || colors.normal;
    }

    /**
     * Get CSS class for status
     * @param {string} status - Status string
     * @returns {string} CSS class name
     */
    getStatusClass(status) {
        const statusMap = {
            healthy: 'status-healthy',
            warning: 'status-warning',
            critical: 'status-critical',
            processed: 'status-healthy',
            pending: 'status-warning',
            failed: 'status-critical',
            unknown: 'status-unknown'
        };

        return statusMap[status?.toLowerCase()] || 'status-unknown';
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Update a specific system card
     * @param {string} systemId - System ID
     * @param {Object} data - Updated system data
     */
    updateSystemCard(systemId, data) {
        const card = document.querySelector(`.system-card[data-system-id="${systemId}"]`);
        if (!card) return;

        // Update file count
        const fileCountEl = card.querySelector('.stat-value');
        if (fileCountEl && data.fileCount !== undefined) {
            fileCountEl.textContent = this.formatNumber(data.fileCount);
        }

        // Update SLA score
        const slaScoreEl = card.querySelectorAll('.stat-value')[1];
        if (slaScoreEl && data.slaScore !== undefined) {
            slaScoreEl.textContent = data.slaScore.toFixed(1);
        }

        // Update status
        const statusBadge = card.querySelector('.status-badge');
        if (statusBadge && data.status) {
            statusBadge.textContent = data.status;
            statusBadge.className = `status-badge ${this.getStatusClass(data.status)}`;
        }

        // Update warning indicator
        const hasViolations = data.hasViolations || data.slaScore < 80;
        if (hasViolations && !card.querySelector('.warning-indicator')) {
            const header = card.querySelector('.system-header');
            header.innerHTML += '<span class="warning-indicator">⚠️</span>';
            card.classList.add('has-warning');
        } else if (!hasViolations) {
            const warningIndicator = card.querySelector('.warning-indicator');
            if (warningIndicator) warningIndicator.remove();
            card.classList.remove('has-warning');
        }
    }
}
