/**
 * Date Presets Module
 * Handles quick date range selection
 */

export class DatePresetsManager {
    constructor(stateManager) {
        this.stateManager = stateManager;
        this.presetButtons = [];
        this.startDateInput = null;
        this.endDateInput = null;
        
        console.log('DatePresetsManager initialized');
    }

    /**
     * Initialize date presets
     */
    initialize() {
        // Get date inputs
        this.startDateInput = document.getElementById('start-date');
        this.endDateInput = document.getElementById('end-date');
        
        // Get all preset buttons
        this.presetButtons = document.querySelectorAll('.btn-preset');
        
        // Add click handlers
        this.presetButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const preset = e.target.getAttribute('data-preset');
                this.applyPreset(preset);
                this.setActiveButton(e.target);
            });
        });
        
        // Listen for manual date changes to clear active preset
        if (this.startDateInput) {
            this.startDateInput.addEventListener('change', () => this.clearActiveButtons());
        }
        if (this.endDateInput) {
            this.endDateInput.addEventListener('change', () => this.clearActiveButtons());
        }
        
        console.log('Date presets initialized');
    }

    /**
     * Apply a date preset
     */
    applyPreset(preset) {
        const today = new Date();
        let startDate, endDate;
        
        switch (preset) {
            case 'last-week':
                endDate = new Date(today);
                startDate = new Date(today);
                startDate.setDate(today.getDate() - 7);
                break;
                
            case 'last-2-weeks':
                endDate = new Date(today);
                startDate = new Date(today);
                startDate.setDate(today.getDate() - 14);
                break;
                
            case 'last-month':
                endDate = new Date(today);
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 1);
                break;
                
            case 'last-3-months':
                endDate = new Date(today);
                startDate = new Date(today);
                startDate.setMonth(today.getMonth() - 3);
                break;
                
            default:
                console.warn('Unknown preset:', preset);
                return;
        }
        
        // Format dates as YYYY-MM-DD for input fields
        const startStr = this.formatDate(startDate);
        const endStr = this.formatDate(endDate);
        
        // Update input fields
        if (this.startDateInput) {
            this.startDateInput.value = startStr;
        }
        if (this.endDateInput) {
            this.endDateInput.value = endStr;
        }
        
        // Update state manager
        this.stateManager.setDateRange(startDate, endDate);
        
        console.log(`Applied preset: ${preset} (${startStr} to ${endStr})`);
    }

    /**
     * Format date as YYYY-MM-DD
     */
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Set active button
     */
    setActiveButton(button) {
        // Remove active class from all buttons
        this.presetButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to clicked button
        button.classList.add('active');
    }

    /**
     * Clear all active buttons
     */
    clearActiveButtons() {
        this.presetButtons.forEach(btn => btn.classList.remove('active'));
    }

    /**
     * Get preset label
     */
    getPresetLabel(preset) {
        const labels = {
            'last-week': 'Last Week',
            'last-2-weeks': 'Last 2 Weeks',
            'last-month': 'Last Month',
            'last-3-months': 'Last 3 Months'
        };
        return labels[preset] || preset;
    }
}
